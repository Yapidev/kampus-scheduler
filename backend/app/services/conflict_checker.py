from typing import Any

from app.schemas import MoveValidationResponse, ScheduleEntryOut
from app.solver.domain import get_lecturer_unavailable_set, is_room_compatible
from app.time_utils import (
    CAMPUS_ALLOWED_DAYS,
    CAMPUS_EARLIEST_START,
    CAMPUS_LATEST_END,
    compute_time_slots,
    get_allowed_slots_for_shift,
    get_blocked_reason_map,
    is_interval_valid_for_blocks,
    is_slot_within_campus_hours,
)


def _offering_classes_and_students(
    off: Any, classes_by_id: dict[int, Any]
) -> tuple[list[Any], int]:
    cids = [off.class_id] + [c for c in (off.extra_class_ids or []) if c != off.class_id]
    cls_objs = [classes_by_id[c] for c in cids if c in classes_by_id]
    stu_cnt = (
        int(off.student_count_override)
        if off.student_count_override is not None
        else sum(int(c.student_count) for c in cls_objs)
    )
    return cls_objs, stu_cnt


def format_schedule_entry(
    entry: Any,
    period: Any,
    rooms_by_id: dict[int, Any],
    buildings_by_id: dict[int, Any],
    offerings_by_id: dict[int, Any],
    courses_by_id: dict[int, Any],
    classes_by_id: dict[int, Any],
    programs_by_id: dict[int, Any],
    lecturers_by_id: dict[int, Any],
    slot_meta_by_idx: dict[int, Any] | None = None,
) -> ScheduleEntryOut:
    if slot_meta_by_idx is None:
        slot_meta_by_idx = {s.index: s for s in compute_time_slots(period)}

    room = rooms_by_id[entry.room_id]
    building = buildings_by_id[room.building_id]
    off = offerings_by_id[entry.offering_id]
    course = courses_by_id[off.course_id]
    cls_objs, student_count = _offering_classes_and_students(off, classes_by_id)
    primary_cls = cls_objs[0]
    program = programs_by_id[primary_cls.program_id]
    lec = lecturers_by_id[off.lecturer_id]
    co_lec = lecturers_by_id.get(off.co_lecturer_id) if off.co_lecturer_id else None

    s_start = slot_meta_by_idx.get(entry.start_slot)
    s_end = slot_meta_by_idx.get(entry.start_slot + entry.duration_slots - 1)
    time_range = (
        f"{s_start.start_time}-{s_end.end_time}"
        if s_start and s_end
        else f"Slot {entry.start_slot}-{entry.start_slot + entry.duration_slots - 1}"
    )

    cap = int(room.capacity)
    fill_pct = round(min(100.0, (student_count / cap) * 100.0), 1) if cap > 0 else 0.0
    waste = max(0, cap - student_count)

    return ScheduleEntryOut(
        id=entry.id,
        period_id=entry.period_id,
        run_id=entry.run_id,
        offering_id=entry.offering_id,
        session_index=entry.session_index,
        room_id=room.id,
        room_code=room.code,
        room_name=room.name,
        room_capacity=cap,
        room_type=room.room_type,
        building_id=building.id,
        building_code=building.code,
        building_name=building.name,
        day=entry.day,
        start_slot=entry.start_slot,
        duration_slots=entry.duration_slots,
        time_range=time_range,
        is_locked=entry.is_locked,
        is_manual_override=entry.is_manual_override,
        course_code=course.code,
        course_name=course.name,
        sks=int(course.sks),
        required_room_type=course.required_room_type,
        class_id=primary_cls.id,
        class_code=primary_cls.code,
        extra_class_ids=[c.id for c in cls_objs[1:]],
        extra_class_codes=[c.code for c in cls_objs[1:]],
        shift=primary_cls.shift,
        program_id=program.id,
        program_code=program.code,
        program_name=program.name,
        student_count=student_count,
        seat_fill_pct=fill_pct,
        seat_waste=waste,
        lecturer_id=lec.id,
        lecturer_name=lec.name,
        co_lecturer_id=co_lec.id if co_lec else None,
        co_lecturer_name=co_lec.name if co_lec else None,
    )


def validate_entry_move(
    period: Any,
    moving_entry: Any,
    target_day: str,
    target_start_slot: int,
    target_room: Any | None,
    all_entries: list[Any],
    offerings_by_id: dict[int, Any],
    courses_by_id: dict[int, Any],
    classes_by_id: dict[int, Any],
    lecturers_by_id: dict[int, Any],
    rooms_by_id: dict[int, Any],
) -> MoveValidationResponse:
    conflicts: list[str] = []
    warnings: list[str] = []

    if target_day not in CAMPUS_ALLOWED_DAYS:
        conflicts.append("Perkuliahan hanya diperbolehkan pada hari Senin hingga Jumat.")
    elif target_day not in (period.days or []):
        conflicts.append(f"Hari '{target_day}' tidak aktif pada periode akademik ini.")

    if target_room is None:
        conflicts.append("Ruangan tujuan tidak ditemukan.")
        return MoveValidationResponse(valid=False, conflicts=conflicts)

    off = offerings_by_id[moving_entry.offering_id]
    course = courses_by_id[off.course_id]
    cls_objs, student_count = _offering_classes_and_students(off, classes_by_id)
    cls_ids = {c.id for c in cls_objs}

    lec_ids = [off.lecturer_id]
    if off.co_lecturer_id and off.co_lecturer_id != off.lecturer_id:
        lec_ids.append(off.co_lecturer_id)

    slot_metas = compute_time_slots(period)
    slot_meta_by_idx = {s.index: s for s in slot_metas}
    blocked_reasons = get_blocked_reason_map(period)

    dur = int(moving_entry.duration_slots)
    target_interval = [target_start_slot + off_s for off_s in range(dur)]

    if not is_interval_valid_for_blocks(target_start_slot, dur, slot_meta_by_idx):
        conflicts.append(
            f"Durasi {dur} slot dari slot {target_start_slot} keluar batas atau memotong jam istirahat."
        )

    out_of_hours = [
        tau
        for tau in target_interval
        if tau in slot_meta_by_idx and not is_slot_within_campus_hours(slot_meta_by_idx[tau])
    ]
    if out_of_hours:
        conflicts.append(
            f"Jam perkuliahan harus berada pada rentang {CAMPUS_EARLIEST_START} hingga {CAMPUS_LATEST_END}."
        )

    for tau in target_interval:
        if (target_day, tau) in blocked_reasons:
            conflicts.append(
                f"Slot {tau} hari {target_day} diblokir ({blocked_reasons[(target_day, tau)]})."
            )

    for c in cls_objs:
        allowed = get_allowed_slots_for_shift(period, c.shift, target_day)
        bad_slots = [tau for tau in target_interval if tau not in allowed]
        if bad_slots:
            conflicts.append(
                f"Slot {bad_slots} hari {target_day} di luar jam shift {c.shift} untuk kelas {c.code}."
            )

    room_ok, room_reason = is_room_compatible(target_room, course, student_count)
    if not room_ok and room_reason:
        conflicts.append(room_reason)

    for lid in lec_ids:
        lec = lecturers_by_id[lid]
        unavail = get_lecturer_unavailable_set(lec)
        hit = [tau for tau in target_interval if (target_day, tau) in unavail]
        if hit:
            conflicts.append(f"Dosen {lec.name} tidak tersedia pada {target_day} slot {hit}.")

    target_set = set(target_interval)
    lec_day_load = dur
    lec_active_days: set[str] = {target_day}

    for other in all_entries:
        if other.id == moving_entry.id:
            continue
        other_off = offerings_by_id.get(other.offering_id)
        if not other_off:
            continue
        other_course = courses_by_id[other_off.course_id]
        other_cls_objs, _ = _offering_classes_and_students(other_off, classes_by_id)
        other_cls_ids = {c.id for c in other_cls_objs}
        other_lec_ids = [other_off.lecturer_id] + (
            [other_off.co_lecturer_id] if other_off.co_lecturer_id else []
        )

        # Check lecturer load stats across week
        if any(lid in other_lec_ids for lid in lec_ids):
            lec_active_days.add(other.day)
            if other.day == target_day:
                lec_day_load += int(other.duration_slots)

        if other.day != target_day:
            continue

        other_slots = set(range(other.start_slot, other.start_slot + other.duration_slots))
        overlap = sorted(target_set & other_slots)

        if other.offering_id == moving_entry.offering_id:
            warnings.append(
                f"Mata kuliah {course.code} memiliki sesi lain pada hari {target_day}."
            )

        if not overlap:
            continue

        if other.room_id == target_room.id:
            conflicts.append(
                f"Bentrok ruangan {target_room.code} dengan {other_course.code} ({', '.join(c.code for c in other_cls_objs)}) di slot {overlap}."
            )

        shared_lecs = [lecturers_by_id[lid].name for lid in lec_ids if lid in other_lec_ids]
        if shared_lecs:
            conflicts.append(
                f"Bentrok dosen ({', '.join(shared_lecs)}) yang sedang mengajar {other_course.code} di slot {overlap}."
            )

        shared_cls = [classes_by_id[cid].code for cid in cls_ids if cid in other_cls_ids]
        if shared_cls:
            conflicts.append(
                f"Bentrok kelas ({', '.join(shared_cls)}) dengan {other_course.code} di slot {overlap}."
            )

    for lid in lec_ids:
        lec = lecturers_by_id[lid]
        if lec_day_load > int(lec.max_sks_per_day):
            warnings.append(
                f"Beban dosen {lec.name} pada {target_day} menjadi {lec_day_load} slot (batas: {lec.max_sks_per_day})."
            )
        if len(lec_active_days) > int(lec.max_days_per_week):
            warnings.append(
                f"Hari mengajar dosen {lec.name} menjadi {len(lec_active_days)} hari (batas: {lec.max_days_per_week})."
            )

    cap = int(target_room.capacity)
    fill_pct = round(min(100.0, (student_count / cap) * 100.0), 1) if cap > 0 else 0.0
    waste = max(0, cap - student_count)
    if room_ok and fill_pct < 55.0:
        warnings.append(
            f"Efisiensi ruangan rendah: keterisian {fill_pct}% ({student_count}/{cap} kursi, sisa {waste} kursi)."
        )

    return MoveValidationResponse(
        valid=len(conflicts) == 0,
        conflicts=conflicts,
        warnings=warnings,
        projected_seat_fill_pct=fill_pct,
        projected_seat_waste=waste,
    )
