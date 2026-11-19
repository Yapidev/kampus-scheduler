from dataclasses import dataclass
from typing import Any


CAMPUS_ALLOWED_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
CAMPUS_EARLIEST_START = "08:00"
CAMPUS_LATEST_END = "16:20"


@dataclass(frozen=True)
class TimeSlotMeta:
    index: int
    start_time: str
    end_time: str
    label: str
    block_index: int
    break_after_minutes: int
    break_after_label: str | None


def parse_hhmm_minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.strip().split(":"))
    return h * 60 + m


def _fmt_minutes(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def compute_time_slots_raw(
    start_time: str,
    slot_minutes: int,
    slots_per_day: int,
    breaks: list[dict[str, Any]] | None,
) -> list[TimeSlotMeta]:
    """Compute ordered daily slot definitions with break & continuous block info."""
    breaks_map = {int(b["after_slot"]): b for b in (breaks or [])}
    cur = parse_hhmm_minutes(start_time or CAMPUS_EARLIEST_START)
    slot_min = int(slot_minutes or 50)
    total_slots = int(slots_per_day or 9)

    result: list[TimeSlotMeta] = []
    block_idx = 0
    for idx in range(1, total_slots + 1):
        end = cur + slot_min
        b_info = breaks_map.get(idx)
        b_min = int(b_info["minutes"]) if b_info else 0
        b_label = b_info.get("label") if b_info else None
        start_str = _fmt_minutes(cur)
        end_str = _fmt_minutes(end)
        result.append(
            TimeSlotMeta(
                index=idx,
                start_time=start_str,
                end_time=end_str,
                label=f"{start_str}-{end_str}",
                block_index=block_idx,
                break_after_minutes=b_min,
                break_after_label=b_label,
            )
        )
        cur = end + b_min
        if b_min >= 20:
            block_idx += 1
    return result


def compute_time_slots(period: Any) -> list[TimeSlotMeta]:
    return compute_time_slots_raw(
        start_time=period.start_time or CAMPUS_EARLIEST_START,
        slot_minutes=int(period.slot_minutes or 50),
        slots_per_day=int(period.slots_per_day or 9),
        breaks=list(period.breaks or []),
    )


def get_effective_days(period: Any) -> list[str]:
    """Enforce Monday-Friday campus lecture days."""
    allowed_set = set(CAMPUS_ALLOWED_DAYS)
    return [d for d in (period.days or []) if d in allowed_set]


def is_slot_within_campus_hours(
    slot_meta: TimeSlotMeta,
    earliest: str = CAMPUS_EARLIEST_START,
    latest: str = CAMPUS_LATEST_END,
) -> bool:
    """Ensure a slot starts >= 08:00 and ends <= 16:20."""
    return (
        parse_hhmm_minutes(slot_meta.start_time) >= parse_hhmm_minutes(earliest)
        and parse_hhmm_minutes(slot_meta.end_time) <= parse_hhmm_minutes(latest)
    )


def validate_period_campus_rules(
    days: list[str],
    start_time: str,
    slot_minutes: int,
    slots_per_day: int,
    breaks: list[dict[str, Any]] | None,
) -> list[str]:
    """Validate AcademicPeriod time settings against campus rules (Senin-Jumat, 08:00-16:20)."""
    errors: list[str] = []
    if not days:
        errors.append("Minimal satu hari kuliah harus dipilih (Senin–Jumat).")
    invalid_days = [d for d in days if d not in CAMPUS_ALLOWED_DAYS]
    if invalid_days:
        errors.append(
            f"Perkuliahan hanya diperbolehkan hari Senin–Jumat. Hari tidak valid: {', '.join(invalid_days)}."
        )

    try:
        start_min = parse_hhmm_minutes(start_time)
    except Exception:
        errors.append("Format jam mulai harus HH:MM (contoh: 08:00).")
        return errors

    earliest_min = parse_hhmm_minutes(CAMPUS_EARLIEST_START)
    latest_min = parse_hhmm_minutes(CAMPUS_LATEST_END)

    if start_min < earliest_min:
        errors.append(
            f"Jam mulai perkuliahan paling pagi adalah {CAMPUS_EARLIEST_START} (input: {start_time})."
        )

    slots = compute_time_slots_raw(start_time, slot_minutes, slots_per_day, breaks)
    if slots:
        last_end = parse_hhmm_minutes(slots[-1].end_time)
        if last_end > latest_min:
            errors.append(
                f"Slot terakhir selesai pukul {slots[-1].end_time}, melebihi batas paling akhir {CAMPUS_LATEST_END}."
            )
    return errors


def get_continuous_blocks(slots: list[TimeSlotMeta]) -> list[list[int]]:
    """Group slot indices into continuous blocks separated by major breaks."""
    blocks: dict[int, list[int]] = {}
    for s in slots:
        blocks.setdefault(s.block_index, []).append(s.index)
    return [blocks[k] for k in sorted(blocks.keys())]


def get_blocked_set(period: Any) -> set[tuple[str, int]]:
    return {(str(b["day"]), int(b["slot"])) for b in (period.blocked_slots or [])}


def get_blocked_reason_map(period: Any) -> dict[tuple[str, int], str]:
    return {
        (str(b["day"]), int(b["slot"])): str(b.get("reason") or "Slot diblokir")
        for b in (period.blocked_slots or [])
    }


def get_allowed_slots_for_shift(period: Any, shift: str, day: str) -> set[int]:
    if day not in CAMPUS_ALLOWED_DAYS:
        return set()
    rules = period.shift_rules or {}
    if shift in rules:
        day_slots = rules[shift].get(day)
        if day_slots is not None:
            return {int(x) for x in day_slots}
        return set()
    # Fallback when custom shift is undefined: allow all slots on configured days
    return set(range(1, int(period.slots_per_day or 9) + 1))


def is_interval_valid_for_blocks(
    start_slot: int,
    duration: int,
    slot_meta_by_idx: dict[int, TimeSlotMeta],
) -> bool:
    """Ensure [start_slot, start_slot + duration - 1] stays within one continuous block."""
    if duration <= 0:
        return False
    first = slot_meta_by_idx.get(start_slot)
    if first is None:
        return False
    for offset in range(duration):
        meta = slot_meta_by_idx.get(start_slot + offset)
        if meta is None or meta.block_index != first.block_index:
            return False
    return True
