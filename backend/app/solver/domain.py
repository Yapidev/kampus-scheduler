from dataclasses import dataclass
from typing import Any

from app.time_utils import (
    TimeSlotMeta,
    compute_time_slots,
    get_allowed_slots_for_shift,
    get_blocked_set,
    get_effective_days,
    is_interval_valid_for_blocks,
    is_slot_within_campus_hours,
)


PRESET_WEIGHTS: dict[str, dict[str, int]] = {
    "balanced": {
        "w_seat": 10,
        "w_gap": 80,
        "w_pack": 40,
        "w_building": 25,
        "w_pref": 15,
    },
    "best_fit": {
        "w_seat": 28,
        "w_gap": 45,
        "w_pack": 20,
        "w_building": 15,
        "w_pref": 10,
    },
    "compact_rooms": {
        "w_seat": 8,
        "w_gap": 150,
        "w_pack": 110,
        "w_building": 25,
        "w_pref": 10,
    },
}


@dataclass
class SessionTask:
    task_idx: int
    offering_id: int
    session_index: int
    course_id: int
    course_code: str
    course_name: str
    sks: int
    required_room_type: str
    required_facilities: list[str]
    class_ids: list[int]
    class_codes: list[str]
    shift: str
    student_count: int
    lecturer_ids: list[int]
    duration_slots: int
    locked_assignment: tuple[str, int, int] | None = None  # (day, start_slot, room_id)


def is_room_compatible(room: Any, course: Any, student_count: int) -> tuple[bool, str | None]:
    """Single source of truth for checking room capacity, type, and facilities."""
    if not room.is_active:
        return False, f"Ruangan {room.code} berstatus non-aktif"
    if room.capacity < student_count:
        return (
            False,
            f"Kapasitas {room.code} ({room.capacity}) lebih kecil dari jumlah mahasiswa ({student_count})",
        )
    req_type = course.required_room_type
    if room.room_type != req_type:
        # Allow Aula for large general theory classes (>60 students)
        if not (req_type == "Teori" and room.room_type == "Aula" and student_count > 60):
            return (
                False,
                f"Tipe ruangan {room.code} ({room.room_type}) tidak sesuai kebutuhan mata kuliah ({req_type})",
            )
    room_fac = set(room.facilities or [])
    req_fac = set(course.required_facilities or [])
    missing = req_fac - room_fac
    if missing:
        return (
            False,
            f"Ruangan {room.code} kekurangan fasilitas: {', '.join(sorted(missing))}",
        )
    return True, None


def get_lecturer_unavailable_set(lecturer: Any) -> set[tuple[str, int]]:
    return {(str(s["day"]), int(s["slot"])) for s in (lecturer.unavailable_slots or [])}


def get_lecturer_preferred_set(lecturer: Any) -> set[tuple[str, int]]:
    return {(str(s["day"]), int(s["slot"])) for s in (lecturer.preferred_slots or [])}


def build_session_tasks(
    period: Any,
    offerings: list[Any],
    classes_by_id: dict[int, Any],
    courses_by_id: dict[int, Any],
    locked_by_key: dict[tuple[int, int], tuple[str, int, int]] | None = None,
) -> list[SessionTask]:
    tasks: list[SessionTask] = []
    locked_map = locked_by_key or {}
    idx = 0
    for off in offerings:
        course = courses_by_id[off.course_id]
        primary_cls = classes_by_id[off.class_id]
        all_class_ids: list[int] = [off.class_id]
        for cid in off.extra_class_ids or []:
            if cid not in all_class_ids and cid in classes_by_id:
                all_class_ids.append(cid)
        class_codes = [classes_by_id[cid].code for cid in all_class_ids]
        student_count = (
            int(off.student_count_override)
            if off.student_count_override is not None
            else sum(int(classes_by_id[cid].student_count) for cid in all_class_ids)
        )
        lecturer_ids = [off.lecturer_id]
        if off.co_lecturer_id and off.co_lecturer_id != off.lecturer_id:
            lecturer_ids.append(off.co_lecturer_id)

        for sess_idx in range(1, int(off.sessions_per_week) + 1):
            locked_val = locked_map.get((off.id, sess_idx))
            tasks.append(
                SessionTask(
                    task_idx=idx,
                    offering_id=off.id,
                    session_index=sess_idx,
                    course_id=course.id,
                    course_code=course.code,
                    course_name=course.name,
                    sks=int(course.sks),
                    required_room_type=course.required_room_type,
                    required_facilities=list(course.required_facilities or []),
                    class_ids=all_class_ids,
                    class_codes=class_codes,
                    shift=primary_cls.shift,
                    student_count=student_count,
                    lecturer_ids=lecturer_ids,
                    duration_slots=int(off.session_duration_slots),
                    locked_assignment=locked_val,
                )
            )
            idx += 1
    return tasks


def build_valid_placements(
    task: SessionTask,
    period: Any,
    slot_metas: list[TimeSlotMeta],
    slot_meta_by_idx: dict[int, TimeSlotMeta],
    blocked_set: set[tuple[str, int]],
    rooms: list[Any],
    courses_by_id: dict[int, Any],
    classes_by_id: dict[int, Any],
    lecturers_by_id: dict[int, Any],
) -> list[tuple[str, int, int]]:
    """Return all valid (day, start_slot, room_id) placements for a task."""
    if task.locked_assignment is not None:
        return [task.locked_assignment]

    course = courses_by_id[task.course_id]
    compatible_rooms = [
        r for r in rooms if is_room_compatible(r, course, task.student_count)[0]
    ]
    if not compatible_rooms:
        return []

    unavail_union: set[tuple[str, int]] = set()
    for lid in task.lecturer_ids:
        unavail_union |= get_lecturer_unavailable_set(lecturers_by_id[lid])

    shifts = {classes_by_id[cid].shift for cid in task.class_ids}
    days = get_effective_days(period)
    placements: list[tuple[str, int, int]] = []

    for day in days:
        allowed_day_slots: set[int] | None = None
        for sh in shifts:
            sh_slots = get_allowed_slots_for_shift(period, sh, day)
            allowed_day_slots = sh_slots if allowed_day_slots is None else (allowed_day_slots & sh_slots)
        if not allowed_day_slots:
            continue

        for sm in slot_metas:
            t = sm.index
            if not is_interval_valid_for_blocks(t, task.duration_slots, slot_meta_by_idx):
                continue
            interval = [t + off for off in range(task.duration_slots)]
            if any(not is_slot_within_campus_hours(slot_meta_by_idx[tau]) for tau in interval):
                continue
            if any(tau not in allowed_day_slots for tau in interval):
                continue
            if any((day, tau) in blocked_set or (day, tau) in unavail_union for tau in interval):
                continue
            for r in compatible_rooms:
                placements.append((day, t, r.id))

    return placements
