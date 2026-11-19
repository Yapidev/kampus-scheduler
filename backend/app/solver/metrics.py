from collections import defaultdict
from typing import Any

from app.schemas import EfficiencySummary, RoomEfficiencyMetric
from app.time_utils import (
    compute_time_slots,
    get_blocked_set,
    get_continuous_blocks,
    get_effective_days,
    is_slot_within_campus_hours,
)


def _classify_room(
    used_slots: int,
    util_pct: float,
    avg_fill_pct: float,
) -> str:
    if used_slots == 0:
        return "Idle"
    if util_pct > 90.0:
        return "High Load"
    if avg_fill_pct < 60.0:
        return "Oversized Match"
    if util_pct < 35.0:
        return "Underutilized"
    return "Optimal"


def compute_efficiency_metrics(
    period: Any,
    rooms: list[Any],
    buildings_by_id: dict[int, Any],
    entries: list[Any],
    offerings_by_id: dict[int, Any],
    classes_by_id: dict[int, Any],
    run: Any | None = None,
) -> EfficiencySummary:
    slot_metas = compute_time_slots(period)
    valid_slot_metas = [s for s in slot_metas if is_slot_within_campus_hours(s)]
    valid_slot_set = {s.index for s in valid_slot_metas}
    blocks = get_continuous_blocks(slot_metas)
    blocked_set = get_blocked_set(period)
    days = get_effective_days(period)

    active_rooms = [r for r in rooms if r.is_active]
    available_slots_per_room = sum(
        1 for d in days for s in valid_slot_metas if (d, s.index) not in blocked_set
    )

    room_used_slots: dict[int, set[tuple[str, int]]] = defaultdict(set)
    room_student_slot_sum: dict[int, int] = defaultdict(int)
    room_cap_slot_sum: dict[int, int] = defaultdict(int)
    room_waste_sum: dict[int, int] = defaultdict(int)
    room_session_count: dict[int, int] = defaultdict(int)

    heatmap: dict[str, dict[int, int]] = {
        d: {s.index: 0 for s in slot_metas} for d in days
    }

    total_student_slots = 0
    total_cap_slots = 0
    total_seat_waste = 0

    for entry in entries:
        off = offerings_by_id.get(entry.offering_id)
        if off is None:
            continue
        all_cids = [off.class_id] + [c for c in (off.extra_class_ids or []) if c != off.class_id]
        student_count = (
            int(off.student_count_override)
            if off.student_count_override is not None
            else sum(int(classes_by_id[cid].student_count) for cid in all_cids if cid in classes_by_id)
        )
        room = next((r for r in rooms if r.id == entry.room_id), None)
        cap = int(room.capacity) if room else 0
        dur = int(entry.duration_slots)

        room_session_count[entry.room_id] += 1
        room_student_slot_sum[entry.room_id] += student_count * dur
        room_cap_slot_sum[entry.room_id] += cap * dur
        waste = max(0, cap - student_count) * dur
        room_waste_sum[entry.room_id] += waste

        total_student_slots += student_count * dur
        total_cap_slots += cap * dur
        total_seat_waste += waste

        for offset in range(dur):
            tau = entry.start_slot + offset
            room_used_slots[entry.room_id].add((entry.day, tau))
            if entry.day in heatmap and tau in heatmap[entry.day]:
                heatmap[entry.day][tau] += 1

    room_metrics: list[RoomEfficiencyMetric] = []
    total_idle_gaps = 0
    bld_stats: dict[int, dict[str, Any]] = {}

    for r in active_rooms:
        used_set = room_used_slots.get(r.id, set())
        used_cnt = len(used_set)

        # Compute idle gaps inside each continuous block per day
        room_gaps = 0
        for d in days:
            for block in blocks:
                open_block = [
                    s for s in block if s in valid_slot_set and (d, s) not in blocked_set
                ]
                occupied_in_block = [s for s in open_block if (d, s) in used_set]
                if len(occupied_in_block) >= 2:
                    span = max(occupied_in_block) - min(occupied_in_block) + 1
                    # Exclude any blocked slots inside the span
                    valid_between = [
                        s
                        for s in open_block
                        if min(occupied_in_block) <= s <= max(occupied_in_block)
                    ]
                    room_gaps += max(0, len(valid_between) - len(occupied_in_block))
        total_idle_gaps += room_gaps

        util_pct = (
            round((used_cnt / available_slots_per_room) * 100.0, 1)
            if available_slots_per_room > 0
            else 0.0
        )
        cap_slots = room_cap_slot_sum.get(r.id, 0)
        stu_slots = room_student_slot_sum.get(r.id, 0)
        avg_fill = round((stu_slots / cap_slots) * 100.0, 1) if cap_slots > 0 else 0.0
        bld = buildings_by_id.get(r.building_id)
        bld_code = bld.code if bld else "-"
        bld_name = bld.name if bld else "-"

        status = _classify_room(used_cnt, util_pct, avg_fill)
        room_metrics.append(
            RoomEfficiencyMetric(
                room_id=r.id,
                room_code=r.code,
                room_name=r.name,
                building_code=bld_code,
                building_name=bld_name,
                room_type=r.room_type,
                capacity=int(r.capacity),
                used_slots=used_cnt,
                available_slots=available_slots_per_room,
                time_utilization_pct=util_pct,
                avg_seat_fill_pct=avg_fill,
                total_seat_waste=room_waste_sum.get(r.id, 0),
                idle_gap_slots=room_gaps,
                session_count=room_session_count.get(r.id, 0),
                status=status,  # type: ignore[arg-type]
            )
        )

        b_entry = bld_stats.setdefault(
            r.building_id,
            {
                "building_id": r.building_id,
                "building_code": bld_code,
                "building_name": bld_name,
                "room_count": 0,
                "used_slots": 0,
                "available_slots": 0,
                "stu_slots": 0,
                "cap_slots": 0,
            },
        )
        b_entry["room_count"] += 1
        b_entry["used_slots"] += used_cnt
        b_entry["available_slots"] += available_slots_per_room
        b_entry["stu_slots"] += stu_slots
        b_entry["cap_slots"] += cap_slots

    total_available_all = available_slots_per_room * len(active_rooms)
    total_used_all = sum(m.used_slots for m in room_metrics)

    room_time_util_pct = (
        round((total_used_all / total_available_all) * 100.0, 1)
        if total_available_all > 0
        else 0.0
    )
    seat_fill_eff_pct = (
        round((total_student_slots / total_cap_slots) * 100.0, 1)
        if total_cap_slots > 0
        else 0.0
    )
    # Composite Room Efficiency Score (0-100):
    # Focuses strongly on Best-Fit Seat Fill (60%), Low Fragmentation / No Idle Gaps (25%),
    # and Active Room Consolidation (15% - ratio of used slots over active rooms' capacity).
    active_room_count = sum(1 for m in room_metrics if m.used_slots > 0)
    active_avail = active_room_count * available_slots_per_room
    active_consolidation = (
        (total_used_all / active_avail) * 100.0 if active_avail > 0 else 0.0
    )
    gap_penalty_pct = (
        min(100.0, (total_idle_gaps / max(1, total_used_all)) * 100.0)
        if total_used_all > 0
        else 0.0
    )
    gap_health_pct = max(0.0, 100.0 - gap_penalty_pct)
    efficiency_score = (
        round(0.60 * seat_fill_eff_pct + 0.25 * gap_health_pct + 0.15 * active_consolidation, 1)
        if total_used_all > 0
        else 0.0
    )

    building_utilization = []
    for b in bld_stats.values():
        util = round((b["used_slots"] / b["available_slots"]) * 100.0, 1) if b["available_slots"] else 0.0
        fill = round((b["stu_slots"] / b["cap_slots"]) * 100.0, 1) if b["cap_slots"] else 0.0
        building_utilization.append(
            {
                "building_id": b["building_id"],
                "building_code": b["building_code"],
                "building_name": b["building_name"],
                "room_count": b["room_count"],
                "used_slots": b["used_slots"],
                "available_slots": b["available_slots"],
                "time_utilization_pct": util,
                "seat_fill_efficiency_pct": fill,
            }
        )

    return EfficiencySummary(
        period_id=period.id,
        period_name=period.name,
        run_id=run.id if run else None,
        run_status=run.status if run else None,
        preset=run.preset if run else None,
        solve_time_ms=run.solve_time_ms if run else 0,
        total_sessions=len(entries),
        total_rooms=len(active_rooms),
        active_rooms=active_room_count,
        room_time_utilization_pct=room_time_util_pct,
        seat_fill_efficiency_pct=seat_fill_eff_pct,
        total_seat_waste_slots=total_seat_waste,
        idle_gap_count=total_idle_gaps,
        efficiency_score=efficiency_score,
        rooms=sorted(room_metrics, key=lambda m: (m.building_code, m.room_code)),
        heatmap=heatmap,
        building_utilization=building_utilization,
    )
