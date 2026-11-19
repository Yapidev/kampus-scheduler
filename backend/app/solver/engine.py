from collections import defaultdict
from dataclasses import dataclass
import math
import os
import time
from typing import Any

from ortools.sat.python import cp_model

from app.schemas import OptimizationWeights
from app.solver.domain import (
    PRESET_WEIGHTS,
    SessionTask,
    build_session_tasks,
    build_valid_placements,
    get_lecturer_preferred_set,
)
from app.time_utils import (
    compute_time_slots,
    get_blocked_set,
    get_continuous_blocks,
    get_effective_days,
    is_slot_within_campus_hours,
)


@dataclass
class PlacementResult:
    offering_id: int
    session_index: int
    room_id: int
    day: str
    start_slot: int
    duration_slots: int
    is_locked: bool


@dataclass
class SolveOutput:
    status: str  # OPTIMAL, FEASIBLE, INFEASIBLE
    solve_time_ms: int
    weights_used: dict[str, int]
    placements: list[PlacementResult]
    errors: list[str]
    objective_value: float | None = None


def resolve_weights(preset: str, custom: OptimizationWeights | None) -> dict[str, int]:
    if preset == "custom" and custom is not None:
        return custom.model_dump()
    return dict(PRESET_WEIGHTS.get(preset, PRESET_WEIGHTS["balanced"]))


def solve_schedule(
    period: Any,
    rooms: list[Any],
    classes: list[Any],
    lecturers: list[Any],
    courses: list[Any],
    offerings: list[Any],
    locked_entries: list[Any] | None = None,
    preset: str = "balanced",
    custom_weights: OptimizationWeights | None = None,
    time_limit_seconds: float = 15.0,
) -> SolveOutput:
    t_start = time.monotonic()
    weights = resolve_weights(preset, custom_weights)

    slot_metas = compute_time_slots(period)
    slot_meta_by_idx = {s.index: s for s in slot_metas}
    blocks = get_continuous_blocks(slot_metas)
    blocked_set = get_blocked_set(period)

    active_rooms = [r for r in rooms if r.is_active]
    rooms_by_id = {r.id: r for r in rooms}
    classes_by_id = {c.id: c for c in classes}
    lecturers_by_id = {l.id: l for l in lecturers}
    courses_by_id = {c.id: c for c in courses}

    locked_map = {
        (e.offering_id, e.session_index): (e.day, e.start_slot, e.room_id)
        for e in (locked_entries or [])
        if e.is_locked
    }

    tasks = build_session_tasks(
        period=period,
        offerings=offerings,
        classes_by_id=classes_by_id,
        courses_by_id=courses_by_id,
        locked_by_key=locked_map,
    )

    if not tasks:
        return SolveOutput(
            status="INFEASIBLE",
            solve_time_ms=int((time.monotonic() - t_start) * 1000),
            weights_used=weights,
            placements=[],
            errors=["Tidak ada penawaran mata kuliah yang perlu dijadwalkan."],
        )

    domains: list[list[tuple[str, int, int]]] = []
    empty_errors: list[str] = []
    for task in tasks:
        dom = build_valid_placements(
            task=task,
            period=period,
            slot_metas=slot_metas,
            slot_meta_by_idx=slot_meta_by_idx,
            blocked_set=blocked_set,
            rooms=active_rooms,
            courses_by_id=courses_by_id,
            classes_by_id=classes_by_id,
            lecturers_by_id=lecturers_by_id,
        )
        if not dom:
            empty_errors.append(
                f"Mata kuliah {task.course_code} ({', '.join(task.class_codes)}) "
                f"tidak memiliki kombinasi waktu & ruangan yang valid."
            )
        domains.append(dom)

    if empty_errors:
        return SolveOutput(
            status="INFEASIBLE",
            solve_time_ms=int((time.monotonic() - t_start) * 1000),
            weights_used=weights,
            placements=[],
            errors=empty_errors,
        )

    model = cp_model.CpModel()

    # Decision variables & occupancy buckets
    x_vars: dict[tuple[int, str, int, int], cp_model.IntVar] = {}
    task_vars: list[list[tuple[cp_model.IntVar, str, int, int]]] = [[] for _ in tasks]

    room_occ: dict[tuple[int, str, int], list[cp_model.IntVar]] = defaultdict(list)
    lec_occ: dict[tuple[int, str, int], list[cp_model.IntVar]] = defaultdict(list)
    cls_occ: dict[tuple[int, str, int], list[cp_model.IntVar]] = defaultdict(list)

    lec_day_terms: dict[tuple[int, str], list[tuple[cp_model.IntVar, int]]] = defaultdict(list)
    off_day_vars: dict[tuple[int, str], list[cp_model.IntVar]] = defaultdict(list)
    off_valid_days: dict[int, set[str]] = defaultdict(set)

    cls_day_bld_vars: dict[tuple[int, str, int], list[cp_model.IntVar]] = defaultdict(list)
    lec_day_bld_vars: dict[tuple[int, str, int], list[cp_model.IntVar]] = defaultdict(list)

    pref_sets = {lid: get_lecturer_preferred_set(lec) for lid, lec in lecturers_by_id.items()}

    objective_terms: list[Any] = []
    w_seat = weights["w_seat"]
    w_gap = weights["w_gap"]
    w_pack = weights["w_pack"]
    w_bld = weights["w_building"]
    w_pref = weights["w_pref"]

    for task, dom in zip(tasks, domains):
        t_idx = task.task_idx
        for d, t0, rid in dom:
            var = model.NewBoolVar(f"x_{t_idx}_{d}_{t0}_{rid}")
            x_vars[(t_idx, d, t0, rid)] = var
            task_vars[t_idx].append((var, d, t0, rid))

            off_day_vars[(task.offering_id, d)].append(var)
            off_valid_days[task.offering_id].add(d)

            room = rooms_by_id[rid]
            bld_id = room.building_id

            for offset in range(task.duration_slots):
                tau = t0 + offset
                room_occ[(rid, d, tau)].append(var)
                for lid in task.lecturer_ids:
                    lec_occ[(lid, d, tau)].append(var)
                for cid in task.class_ids:
                    cls_occ[(cid, d, tau)].append(var)

            for lid in task.lecturer_ids:
                lec_day_terms[(lid, d)].append((var, task.duration_slots))
                lec_day_bld_vars[(lid, d, bld_id)].append(var)
            for cid in task.class_ids:
                cls_day_bld_vars[(cid, d, bld_id)].append(var)

            # Objective 1: Best-Fit Seat Waste
            seat_waste = max(0, int(room.capacity) - task.student_count) * task.duration_slots
            if w_seat > 0 and seat_waste > 0:
                objective_terms.append(w_seat * seat_waste * var)

            # Objective 5: Lecturer preferred slots bonus
            if w_pref > 0:
                pref_hits = 0
                for lid in task.lecturer_ids:
                    pset = pref_sets.get(lid, set())
                    pref_hits += sum(
                        1 for off in range(task.duration_slots) if (d, t0 + off) in pset
                    )
                if pref_hits > 0:
                    objective_terms.append(-w_pref * pref_hits * var)

    # Hard Constraint 1: Exactly one placement per session
    for t_idx, vlist in enumerate(task_vars):
        model.AddExactlyOne([item[0] for item in vlist])

    # Hard Constraint 2: Room no-overlap
    for _key, vlist in room_occ.items():
        if len(vlist) > 1:
            model.AddAtMostOne(vlist)

    # Hard Constraint 3: Lecturer no-overlap
    for _key, vlist in lec_occ.items():
        if len(vlist) > 1:
            model.AddAtMostOne(vlist)

    # Hard Constraint 4: Class no-overlap
    for _key, vlist in cls_occ.items():
        if len(vlist) > 1:
            model.AddAtMostOne(vlist)

    # Hard Constraint 5: Lecturer max SKS per day & max days per week
    days_by_lec: dict[int, list[cp_model.IntVar]] = defaultdict(list)
    for (lid, d), terms in lec_day_terms.items():
        lec = lecturers_by_id[lid]
        day_load = sum(var * dur for var, dur in terms)
        model.Add(day_load <= int(lec.max_sks_per_day))

        day_active = model.NewBoolVar(f"lec_day_{lid}_{d}")
        model.Add(day_load >= 1).OnlyEnforceIf(day_active)
        model.Add(day_load == 0).OnlyEnforceIf(day_active.Not())
        days_by_lec[lid].append(day_active)

    for lid, active_days in days_by_lec.items():
        max_days = int(lecturers_by_id[lid].max_days_per_week)
        if len(active_days) > max_days:
            model.Add(sum(active_days) <= max_days)

    # Hard Constraint 6: Multi-session offerings spread across distinct days
    tasks_by_off: dict[int, list[SessionTask]] = defaultdict(list)
    for task in tasks:
        tasks_by_off[task.offering_id].append(task)

    for off_id, group in tasks_by_off.items():
        if len(group) <= 1:
            continue
        valid_days = off_valid_days[off_id]
        max_per_day = max(1, math.ceil(len(group) / max(1, len(valid_days))))
        for d in valid_days:
            dvars = off_day_vars.get((off_id, d), [])
            if len(dvars) > max_per_day:
                if max_per_day == 1:
                    model.AddAtMostOne(dvars)
                else:
                    model.Add(sum(dvars) <= max_per_day)

    # Objective 2 & 3: Room Gap Penalty & Room Block Consolidation
    if w_gap > 0 or w_pack > 0:
        days = get_effective_days(period)
        valid_slot_set = {s.index for s in slot_metas if is_slot_within_campus_hours(s)}
        for r in active_rooms:
            rid = r.id
            for d in days:
                for b_idx, block_slots in enumerate(blocks):
                    open_slots = [
                        s for s in block_slots if s in valid_slot_set and (d, s) not in blocked_set
                    ]
                    if not open_slots:
                        continue
                    slot_bools: dict[int, cp_model.IntVar] = {}
                    for tau in open_slots:
                        vlist = room_occ.get((rid, d, tau))
                        if vlist:
                            b_var = model.NewBoolVar(f"rb_{rid}_{d}_{tau}")
                            model.Add(b_var == sum(vlist))
                            slot_bools[tau] = b_var
                    if not slot_bools:
                        continue

                    used_sum = sum(slot_bools.values())
                    block_active = model.NewBoolVar(f"rba_{rid}_{d}_{b_idx}")
                    model.Add(used_sum >= 1).OnlyEnforceIf(block_active)
                    model.Add(used_sum == 0).OnlyEnforceIf(block_active.Not())

                    if w_pack > 0:
                        objective_terms.append(w_pack * block_active)

                    if w_gap > 0 and len(slot_bools) >= 2 and len(open_slots) >= 3:
                        min_s = min(open_slots)
                        max_s = max(open_slots)
                        max_span = max_s - min_s + 1
                        first_s = model.NewIntVar(min_s, max_s, f"fs_{rid}_{d}_{b_idx}")
                        last_s = model.NewIntVar(min_s, max_s, f"ls_{rid}_{d}_{b_idx}")
                        gap = model.NewIntVar(0, max_span, f"gap_{rid}_{d}_{b_idx}")

                        for tau, b_var in slot_bools.items():
                            model.Add(first_s <= tau).OnlyEnforceIf(b_var)
                            model.Add(last_s >= tau).OnlyEnforceIf(b_var)

                        model.Add(gap >= last_s - first_s + 1 - used_sum).OnlyEnforceIf(block_active)
                        objective_terms.append(w_gap * gap)

    # Objective 4: Minimize Building Hops per day for Classes and Lecturers
    if w_bld > 0:
        for (cid, d, bld_id), vlist in cls_day_bld_vars.items():
            if not vlist:
                continue
            used = model.NewBoolVar(f"cb_{cid}_{d}_{bld_id}")
            for v in vlist:
                model.AddImplication(v, used)
            objective_terms.append(w_bld * used)

        for (lid, d, bld_id), vlist in lec_day_bld_vars.items():
            if not vlist:
                continue
            used = model.NewBoolVar(f"lb_{lid}_{d}_{bld_id}")
            for v in vlist:
                model.AddImplication(v, used)
            objective_terms.append(w_bld * used)

    if objective_terms:
        model.Minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = min(8, os.cpu_count() or 4)

    status_code = solver.Solve(model)
    elapsed_ms = int((time.monotonic() - t_start) * 1000)

    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        status_label = "INFEASIBLE"
        return SolveOutput(
            status=status_label,
            solve_time_ms=elapsed_ms,
            weights_used=weights,
            placements=[],
            errors=[
                "Solver tidak menemukan jadwal yang memenuhi seluruh batasan keras. "
                "Periksa laporan Pre-flight Audit atau longgarkan ketersediaan dosen / kapasitas ruangan."
            ],
        )

    placements: list[PlacementResult] = []
    for t_idx, vlist in enumerate(task_vars):
        task = tasks[t_idx]
        for var, d, t0, rid in vlist:
            if solver.Value(var) == 1:
                placements.append(
                    PlacementResult(
                        offering_id=task.offering_id,
                        session_index=task.session_index,
                        room_id=rid,
                        day=d,
                        start_slot=t0,
                        duration_slots=task.duration_slots,
                        is_locked=task.locked_assignment is not None,
                    )
                )
                break

    status_label = "OPTIMAL" if status_code == cp_model.OPTIMAL else "FEASIBLE"
    return SolveOutput(
        status=status_label,
        solve_time_ms=elapsed_ms,
        weights_used=weights,
        placements=placements,
        errors=[],
        objective_value=float(solver.ObjectiveValue()) if objective_terms else 0.0,
    )
