from collections import defaultdict
from typing import Any

from app.schemas import PreflightIssue, PreflightReport
from app.solver.domain import (
    build_session_tasks,
    build_valid_placements,
    get_lecturer_unavailable_set,
    is_room_compatible,
)
from app.time_utils import (
    compute_time_slots,
    get_allowed_slots_for_shift,
    get_blocked_set,
    get_effective_days,
    is_slot_within_campus_hours,
    validate_period_campus_rules,
)


def run_preflight_audit(
    period: Any,
    rooms: list[Any],
    classes: list[Any],
    lecturers: list[Any],
    courses: list[Any],
    offerings: list[Any],
    locked_entries: list[Any] | None = None,
) -> PreflightReport:
    slot_metas = compute_time_slots(period)
    slot_meta_by_idx = {s.index: s for s in slot_metas}
    blocked_set = get_blocked_set(period)

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

    issues: list[PreflightIssue] = []
    for rule_err in validate_period_campus_rules(
        days=list(period.days or []),
        start_time=period.start_time,
        slot_minutes=int(period.slot_minutes),
        slots_per_day=int(period.slots_per_day),
        breaks=list(period.breaks or []),
    ):
        issues.append(
            PreflightIssue(
                severity="error",
                category="Aturan Waktu Kampus",
                message=rule_err,
            )
        )

    if not tasks:
        issues.append(
            PreflightIssue(
                severity="error",
                category="Data Kosong",
                message="Belum ada penawaran mata kuliah (Course Offering) pada periode akademik ini.",
            )
        )

    active_rooms = [r for r in rooms if r.is_active]
    days = get_effective_days(period)
    valid_slot_metas = [s for s in slot_metas if is_slot_within_campus_hours(s)]
    total_available_room_slots = 0
    for r in active_rooms:
        for d in days:
            for s in valid_slot_metas:
                if (d, s.index) not in blocked_set:
                    total_available_room_slots += 1

    total_required_slots = sum(t.duration_slots for t in tasks)

    # 1. Check per-task valid placement existence
    room_type_required_slots: dict[str, int] = defaultdict(int)
    lecturer_required_slots: dict[int, int] = defaultdict(int)
    class_required_slots: dict[int, int] = defaultdict(int)

    for task in tasks:
        room_type_required_slots[task.required_room_type] += task.duration_slots
        for lid in task.lecturer_ids:
            lecturer_required_slots[lid] += task.duration_slots
        for cid in task.class_ids:
            class_required_slots[cid] += task.duration_slots

        if task.locked_assignment is not None:
            d, t0, rid = task.locked_assignment
            r = rooms_by_id.get(rid)
            course = courses_by_id[task.course_id]
            if r is None:
                issues.append(
                    PreflightIssue(
                        severity="error",
                        category="Jadwal Terkunci",
                        message=f"Ruangan terkunci untuk {task.course_code} ({', '.join(task.class_codes)}) tidak ditemukan.",
                        entity_ref=task.course_code,
                    )
                )
            else:
                ok, reason = is_room_compatible(r, course, task.student_count)
                if not ok:
                    issues.append(
                        PreflightIssue(
                            severity="warning",
                            category="Jadwal Terkunci",
                            message=f"Jadwal terkunci {task.course_code} di {r.code}: {reason}",
                            entity_ref=task.course_code,
                        )
                    )
            continue

        placements = build_valid_placements(
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
        if not placements:
            comp_rooms = [
                r
                for r in active_rooms
                if is_room_compatible(r, courses_by_id[task.course_id], task.student_count)[0]
            ]
            if not comp_rooms:
                msg = (
                    f"{task.course_code} - {task.course_name} ({', '.join(task.class_codes)}, "
                    f"{task.student_count} mhs) tidak punya ruangan tipe '{task.required_room_type}' "
                    f"dengan kapasitas & fasilitas memadai."
                )
            else:
                msg = (
                    f"{task.course_code} - {task.course_name} ({', '.join(task.class_codes)}, "
                    f"{task.duration_slots} slot berurutan) tidak punya slot waktu valid sesuai shift kelas dan ketersediaan dosen."
                )
            issues.append(
                PreflightIssue(
                    severity="error",
                    category="Domain Kosong",
                    message=msg,
                    entity_ref=task.course_code,
                )
            )

    # 2. Check aggregate room capacity per room_type
    room_type_supply: dict[str, int] = defaultdict(int)
    for r in active_rooms:
        available_for_r = sum(
            1 for d in days for s in valid_slot_metas if (d, s.index) not in blocked_set
        )
        room_type_supply[r.room_type] += available_for_r

    for rtype, req in room_type_required_slots.items():
        supply = room_type_supply.get(rtype, 0)
        if req > supply:
            issues.append(
                PreflightIssue(
                    severity="error",
                    category="Kapasitas Tipe Ruangan",
                    message=f"Kebutuhan slot ruangan tipe '{rtype}' ({req} slot) melebihi total slot tersedia ({supply} slot).",
                    entity_ref=rtype,
                )
            )
        elif supply > 0 and req / supply > 0.85:
            issues.append(
                PreflightIssue(
                    severity="warning",
                    category="Kepadatan Tinggi",
                    message=f"Okupansi ruangan tipe '{rtype}' sangat padat ({req}/{supply} slot = {round(req / supply * 100)}%).",
                    entity_ref=rtype,
                )
            )

    # 3. Check lecturer capacity against max_sks_per_day * max_days_per_week and unavailabilities
    for lid, req in lecturer_required_slots.items():
        lec = lecturers_by_id[lid]
        max_weekly = int(lec.max_sks_per_day) * int(lec.max_days_per_week)
        unavail = get_lecturer_unavailable_set(lec)
        avail_slots = sum(
            1
            for d in days
            for s in valid_slot_metas
            if (d, s.index) not in blocked_set and (d, s.index) not in unavail
        )
        if req > max_weekly:
            issues.append(
                PreflightIssue(
                    severity="error",
                    category="Beban Dosen",
                    message=f"Dosen {lec.name} dibebani {req} slot/minggu, melebihi batas maksimal ({lec.max_sks_per_day} slot/hari × {lec.max_days_per_week} hari = {max_weekly}).",
                    entity_ref=lec.nidn,
                )
            )
        if req > avail_slots:
            issues.append(
                PreflightIssue(
                    severity="error",
                    category="Ketersediaan Dosen",
                    message=f"Dosen {lec.name} membutuhkan {req} slot tetapi hanya tersedia {avail_slots} slot aktif.",
                    entity_ref=lec.nidn,
                )
            )

    # 4. Check class shift capacity
    for cid, req in class_required_slots.items():
        cls = classes_by_id[cid]
        avail_cls = sum(
            1
            for d in days
            for s_idx in get_allowed_slots_for_shift(period, cls.shift, d)
            if (d, s_idx) not in blocked_set
        )
        if req > avail_cls:
            issues.append(
                PreflightIssue(
                    severity="error",
                    category="Kapasitas Shift Kelas",
                    message=f"Kelas {cls.code} ({cls.shift}) memiliki total {req} slot kuliah, melebihi slot tersedia ({avail_cls} slot).",
                    entity_ref=cls.code,
                )
            )

    # 5. Check conflicts among locked entries themselves
    locked_tasks = [t for t in tasks if t.locked_assignment is not None]
    occ_room: dict[tuple[int, str, int], str] = {}
    occ_lec: dict[tuple[int, str, int], str] = {}
    occ_cls: dict[tuple[int, str, int], str] = {}
    for lt in locked_tasks:
        assert lt.locked_assignment is not None
        d, t0, rid = lt.locked_assignment
        for offset in range(lt.duration_slots):
            tau = t0 + offset
            if (rid, d, tau) in occ_room:
                issues.append(
                    PreflightIssue(
                        severity="error",
                        category="Bentrok Jadwal Terkunci",
                        message=f"Jadwal terkunci {lt.course_code} bentrok ruangan dengan {occ_room[(rid, d, tau)]} pada {d} slot {tau}.",
                    )
                )
            occ_room[(rid, d, tau)] = lt.course_code
            for lid in lt.lecturer_ids:
                if (lid, d, tau) in occ_lec:
                    issues.append(
                        PreflightIssue(
                            severity="error",
                            category="Bentrok Jadwal Terkunci",
                            message=f"Jadwal terkunci {lt.course_code} bentrok dosen dengan {occ_lec[(lid, d, tau)]} pada {d} slot {tau}.",
                        )
                    )
                occ_lec[(lid, d, tau)] = lt.course_code
            for cid in lt.class_ids:
                if (cid, d, tau) in occ_cls:
                    issues.append(
                        PreflightIssue(
                            severity="error",
                            category="Bentrok Jadwal Terkunci",
                            message=f"Jadwal terkunci {lt.course_code} bentrok kelas dengan {occ_cls[(cid, d, tau)]} pada {d} slot {tau}.",
                        )
                    )
                occ_cls[(cid, d, tau)] = lt.course_code

    feasible = not any(issue.severity == "error" for issue in issues)
    return PreflightReport(
        feasible=feasible,
        total_sessions=len(tasks),
        total_required_slots=total_required_slots,
        total_available_room_slots=total_available_room_slots,
        issues=issues,
    )
