from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


DEFAULT_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
DEFAULT_BREAKS = [
    {"after_slot": 5, "minutes": 50, "label": "ISHOMA"},
]
DEFAULT_BLOCKED_SLOTS = [
    {"day": "Jumat", "slot": 5, "reason": "Persiapan & Sholat Jumat"},
]
DEFAULT_SHIFT_RULES = {
    "Reguler": {
        "Senin": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Selasa": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Rabu": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Kamis": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Jumat": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    },
    "Karyawan": {
        "Senin": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Selasa": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Rabu": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Kamis": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "Jumat": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    },
}


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    year: Mapped[str] = mapped_column(String(32), nullable=False)
    semester_type: Mapped[str] = mapped_column(String(24), nullable=False, default="Ganjil")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    days: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: list(DEFAULT_DAYS))
    start_time: Mapped[str] = mapped_column(String(8), nullable=False, default="08:00")
    slot_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    slots_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    breaks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=lambda: [dict(b) for b in DEFAULT_BREAKS]
    )
    blocked_slots: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=lambda: [dict(b) for b in DEFAULT_BLOCKED_SLOTS]
    )
    shift_rules: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=lambda: dict(DEFAULT_SHIFT_RULES)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    classes: Mapped[list["StudentClass"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    offerings: Mapped[list["CourseOffering"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    schedule_runs: Mapped[list["ScheduleRun"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )
    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(
        back_populates="period", cascade="all, delete-orphan"
    )


class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(24), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    programs: Mapped[list["StudyProgram"]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan"
    )


class StudyProgram(Base):
    __tablename__ = "study_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(24), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(16), nullable=False, default="S1")

    faculty: Mapped["Faculty"] = relationship(back_populates="programs")


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(24), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    floor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    campus_zone: Mapped[str] = mapped_column(String(64), nullable=False, default="Zona Utama")

    rooms: Mapped[list["Room"]] = relationship(
        back_populates="building", cascade="all, delete-orphan"
    )


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    room_type: Mapped[str] = mapped_column(String(48), nullable=False, default="Teori")
    facilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    building: Mapped["Building"] = relationship(back_populates="rooms")


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nidn: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    home_program_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("study_programs.id", ondelete="SET NULL"), nullable=True
    )
    max_sks_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    max_days_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    unavailable_slots: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    preferred_slots: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)


class StudentClass(Base):
    __tablename__ = "student_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_programs.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    shift: Mapped[str] = mapped_column(String(24), nullable=False, default="Reguler")
    student_count: Mapped[int] = mapped_column(Integer, nullable=False, default=35)

    period: Mapped["AcademicPeriod"] = relationship(back_populates="classes")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_programs.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sks: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    course_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Teori")
    required_room_type: Mapped[str] = mapped_column(String(48), nullable=False, default="Teori")
    required_facilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class CourseOffering(Base):
    __tablename__ = "course_offerings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("student_classes.id", ondelete="CASCADE"), nullable=False
    )
    extra_class_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    lecturer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lecturers.id", ondelete="CASCADE"), nullable=False
    )
    co_lecturer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("lecturers.id", ondelete="SET NULL"), nullable=True
    )
    sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    session_duration_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    student_count_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    period: Mapped["AcademicPeriod"] = relationship(back_populates="offerings")
    course: Mapped["Course"] = relationship()
    student_class: Mapped["StudentClass"] = relationship()
    lecturer: Mapped["Lecturer"] = relationship(foreign_keys=[lecturer_id])
    co_lecturer: Mapped["Lecturer | None"] = relationship(foreign_keys=[co_lecturer_id])


class ScheduleRun(Base):
    __tablename__ = "schedule_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    preset: Mapped[str] = mapped_column(String(32), nullable=False, default="balanced")
    weights_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    solve_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    room_time_utilization: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    seat_fill_efficiency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    idle_gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    efficiency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    period: Mapped["AcademicPeriod"] = relationship(back_populates="schedule_runs")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_periods.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("schedule_runs.id", ondelete="SET NULL"), nullable=True
    )
    offering_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False
    )
    session_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    day: Mapped[str] = mapped_column(String(16), nullable=False)
    start_slot: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    period: Mapped["AcademicPeriod"] = relationship(back_populates="schedule_entries")
    offering: Mapped["CourseOffering"] = relationship()
    room: Mapped["Room"] = relationship()
