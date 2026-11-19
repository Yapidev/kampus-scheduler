from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    AcademicPeriod,
    Building,
    Course,
    CourseOffering,
    Lecturer,
    Room,
    ScheduleEntry,
    ScheduleRun,
    StudentClass,
    StudyProgram,
)
from app.schemas import AcademicPeriodOut, ScheduleEntryOut, TimeSlotOut
from app.services.conflict_checker import format_schedule_entry
from app.time_utils import compute_time_slots


@dataclass
class PeriodContext:
    period: AcademicPeriod
    buildings_by_id: dict[int, Building]
    rooms: list[Room]
    rooms_by_id: dict[int, Room]
    programs_by_id: dict[int, StudyProgram]
    lecturers: list[Lecturer]
    lecturers_by_id: dict[int, Lecturer]
    classes: list[StudentClass]
    classes_by_id: dict[int, StudentClass]
    courses: list[Course]
    courses_by_id: dict[int, Course]
    offerings: list[CourseOffering]
    offerings_by_id: dict[int, CourseOffering]
    entries: list[ScheduleEntry]
    latest_run: ScheduleRun | None


def resolve_period(db: Session, period_id: int | None = None) -> AcademicPeriod:
    if period_id is not None:
        period = db.get(AcademicPeriod, period_id)
        if not period:
            raise HTTPException(status_code=404, detail="Periode akademik tidak ditemukan.")
        return period
    period = db.query(AcademicPeriod).filter(AcademicPeriod.is_active.is_(True)).first()
    if not period:
        period = db.query(AcademicPeriod).order_by(AcademicPeriod.id.desc()).first()
    if not period:
        raise HTTPException(status_code=404, detail="Belum ada periode akademik.")
    return period


def format_period_out(period: AcademicPeriod) -> AcademicPeriodOut:
    slots = compute_time_slots(period)
    data = AcademicPeriodOut.model_validate(period)
    data.time_slots = [
        TimeSlotOut(
            index=s.index,
            start_time=s.start_time,
            end_time=s.end_time,
            label=s.label,
            block_index=s.block_index,
            break_after_minutes=s.break_after_minutes,
            break_after_label=s.break_after_label,
        )
        for s in slots
    ]
    return data


def load_period_context(db: Session, period_id: int | None = None) -> PeriodContext:
    period = resolve_period(db, period_id)
    buildings = db.query(Building).all()
    rooms = db.query(Room).order_by(Room.code).all()
    programs = db.query(StudyProgram).all()
    lecturers = db.query(Lecturer).order_by(Lecturer.name).all()
    classes = db.query(StudentClass).filter(StudentClass.period_id == period.id).order_by(StudentClass.code).all()
    courses = db.query(Course).order_by(Course.code).all()
    offerings = db.query(CourseOffering).filter(CourseOffering.period_id == period.id).all()
    entries = db.query(ScheduleEntry).filter(ScheduleEntry.period_id == period.id).all()
    latest_run = (
        db.query(ScheduleRun)
        .filter(ScheduleRun.period_id == period.id)
        .order_by(ScheduleRun.id.desc())
        .first()
    )
    return PeriodContext(
        period=period,
        buildings_by_id={b.id: b for b in buildings},
        rooms=rooms,
        rooms_by_id={r.id: r for r in rooms},
        programs_by_id={p.id: p for p in programs},
        lecturers=lecturers,
        lecturers_by_id={l.id: l for l in lecturers},
        classes=classes,
        classes_by_id={c.id: c for c in classes},
        courses=courses,
        courses_by_id={c.id: c for c in courses},
        offerings=offerings,
        offerings_by_id={o.id: o for o in offerings},
        entries=entries,
        latest_run=latest_run,
    )


def filter_and_format_entries(
    ctx: PeriodContext,
    program_id: int | None = None,
    class_id: int | None = None,
    lecturer_id: int | None = None,
    room_id: int | None = None,
) -> list[ScheduleEntryOut]:
    slot_meta_by_idx = {s.index: s for s in compute_time_slots(ctx.period)}
    formatted = [
        format_schedule_entry(
            entry=e,
            period=ctx.period,
            rooms_by_id=ctx.rooms_by_id,
            buildings_by_id=ctx.buildings_by_id,
            offerings_by_id=ctx.offerings_by_id,
            courses_by_id=ctx.courses_by_id,
            classes_by_id=ctx.classes_by_id,
            programs_by_id=ctx.programs_by_id,
            lecturers_by_id=ctx.lecturers_by_id,
            slot_meta_by_idx=slot_meta_by_idx,
        )
        for e in ctx.entries
        if e.offering_id in ctx.offerings_by_id and e.room_id in ctx.rooms_by_id
    ]
    if program_id is not None:
        formatted = [f for f in formatted if f.program_id == program_id]
    if class_id is not None:
        formatted = [
            f for f in formatted if f.class_id == class_id or class_id in f.extra_class_ids
        ]
    if lecturer_id is not None:
        formatted = [
            f for f in formatted if f.lecturer_id == lecturer_id or f.co_lecturer_id == lecturer_id
        ]
    if room_id is not None:
        formatted = [f for f in formatted if f.room_id == room_id]
    return formatted
