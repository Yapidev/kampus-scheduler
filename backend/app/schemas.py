from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BreakConfig(BaseModel):
    after_slot: int = Field(..., ge=1)
    minutes: int = Field(..., ge=0, le=240)
    label: str = "Istirahat"


class BlockedSlotConfig(BaseModel):
    day: str
    slot: int = Field(..., ge=1)
    reason: str = "Diblokir"


class SlotCoord(BaseModel):
    day: str
    slot: int = Field(..., ge=1)


class TimeSlotOut(BaseModel):
    index: int
    start_time: str
    end_time: str
    label: str
    block_index: int
    break_after_minutes: int
    break_after_label: str | None = None


class AcademicPeriodBase(BaseModel):
    name: str
    year: str
    semester_type: Literal["Ganjil", "Genap", "Pendek"] = "Ganjil"
    is_active: bool = True
    status: Literal["draft", "published"] = "draft"
    days: list[str] = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
    start_time: str = "08:00"
    slot_minutes: int = Field(default=50, ge=20, le=180)
    slots_per_day: int = Field(default=9, ge=1, le=24)
    breaks: list[BreakConfig] = []
    blocked_slots: list[BlockedSlotConfig] = []
    shift_rules: dict[str, dict[str, list[int]]] = {}


class AcademicPeriodCreate(AcademicPeriodBase):
    pass


class AcademicPeriodUpdate(BaseModel):
    name: str | None = None
    year: str | None = None
    semester_type: Literal["Ganjil", "Genap", "Pendek"] | None = None
    is_active: bool | None = None
    status: Literal["draft", "published"] | None = None
    days: list[str] | None = None
    start_time: str | None = None
    slot_minutes: int | None = Field(default=None, ge=20, le=180)
    slots_per_day: int | None = Field(default=None, ge=1, le=24)
    breaks: list[BreakConfig] | None = None
    blocked_slots: list[BlockedSlotConfig] | None = None
    shift_rules: dict[str, dict[str, list[int]]] | None = None


class AcademicPeriodOut(AcademicPeriodBase):
    id: int
    created_at: datetime
    time_slots: list[TimeSlotOut] = []

    model_config = ConfigDict(from_attributes=True)


class FacultyBase(BaseModel):
    code: str
    name: str


class FacultyCreate(FacultyBase):
    pass


class FacultyOut(FacultyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StudyProgramBase(BaseModel):
    faculty_id: int
    code: str
    name: str
    degree_level: Literal["D3", "D4", "S1", "S2", "S3"] = "S1"


class StudyProgramCreate(StudyProgramBase):
    pass


class StudyProgramOut(StudyProgramBase):
    id: int
    faculty_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class BuildingBase(BaseModel):
    code: str
    name: str
    floor_count: int = Field(default=3, ge=1, le=30)
    campus_zone: str = "Zona Utama"


class BuildingCreate(BuildingBase):
    pass


class BuildingOut(BuildingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RoomBase(BaseModel):
    building_id: int
    code: str
    name: str
    floor: int = Field(default=1, ge=1)
    capacity: int = Field(default=40, ge=5, le=1000)
    room_type: str = "Teori"
    facilities: list[str] = []
    is_active: bool = True


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    building_id: int | None = None
    code: str | None = None
    name: str | None = None
    floor: int | None = Field(default=None, ge=1)
    capacity: int | None = Field(default=None, ge=5, le=1000)
    room_type: str | None = None
    facilities: list[str] | None = None
    is_active: bool | None = None


class RoomOut(RoomBase):
    id: int
    building_code: str | None = None
    building_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class LecturerBase(BaseModel):
    nidn: str
    name: str
    email: str | None = None
    home_program_id: int | None = None
    max_sks_per_day: int = Field(default=6, ge=1, le=16)
    max_days_per_week: int = Field(default=5, ge=1, le=6)
    unavailable_slots: list[SlotCoord] = []
    preferred_slots: list[SlotCoord] = []


class LecturerCreate(LecturerBase):
    pass


class LecturerUpdate(BaseModel):
    nidn: str | None = None
    name: str | None = None
    email: str | None = None
    home_program_id: int | None = None
    max_sks_per_day: int | None = Field(default=None, ge=1, le=16)
    max_days_per_week: int | None = Field(default=None, ge=1, le=6)
    unavailable_slots: list[SlotCoord] | None = None
    preferred_slots: list[SlotCoord] | None = None


class LecturerOut(LecturerBase):
    id: int
    program_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class StudentClassBase(BaseModel):
    period_id: int
    program_id: int
    code: str
    semester: int = Field(default=1, ge=1, le=14)
    shift: Literal["Reguler", "Karyawan"] = "Reguler"
    student_count: int = Field(default=35, ge=1, le=500)


class StudentClassCreate(StudentClassBase):
    pass


class StudentClassUpdate(BaseModel):
    program_id: int | None = None
    code: str | None = None
    semester: int | None = Field(default=None, ge=1, le=14)
    shift: Literal["Reguler", "Karyawan"] | None = None
    student_count: int | None = Field(default=None, ge=1, le=500)


class StudentClassOut(StudentClassBase):
    id: int
    program_code: str | None = None
    program_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CourseBase(BaseModel):
    program_id: int
    code: str
    name: str
    sks: int = Field(default=3, ge=1, le=8)
    course_type: Literal["Teori", "Praktikum", "Teori+Praktikum"] = "Teori"
    required_room_type: str = "Teori"
    required_facilities: list[str] = []


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    program_id: int | None = None
    code: str | None = None
    name: str | None = None
    sks: int | None = Field(default=None, ge=1, le=8)
    course_type: Literal["Teori", "Praktikum", "Teori+Praktikum"] | None = None
    required_room_type: str | None = None
    required_facilities: list[str] | None = None


class CourseOut(CourseBase):
    id: int
    program_code: str | None = None
    program_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CourseOfferingBase(BaseModel):
    period_id: int
    course_id: int
    class_id: int
    extra_class_ids: list[int] = []
    lecturer_id: int
    co_lecturer_id: int | None = None
    sessions_per_week: int = Field(default=1, ge=1, le=4)
    session_duration_slots: int = Field(default=3, ge=1, le=6)
    student_count_override: int | None = Field(default=None, ge=1)
    notes: str | None = None


class CourseOfferingCreate(CourseOfferingBase):
    pass


class CourseOfferingUpdate(BaseModel):
    course_id: int | None = None
    class_id: int | None = None
    extra_class_ids: list[int] | None = None
    lecturer_id: int | None = None
    co_lecturer_id: int | None = None
    sessions_per_week: int | None = Field(default=None, ge=1, le=4)
    session_duration_slots: int | None = Field(default=None, ge=1, le=6)
    student_count_override: int | None = Field(default=None, ge=1)
    notes: str | None = None


class CourseOfferingOut(CourseOfferingBase):
    id: int
    course_code: str | None = None
    course_name: str | None = None
    sks: int | None = None
    required_room_type: str | None = None
    class_code: str | None = None
    extra_class_codes: list[str] = []
    shift: str | None = None
    effective_student_count: int = 0
    lecturer_name: str | None = None
    co_lecturer_name: str | None = None
    program_code: str | None = None
    model_config = ConfigDict(from_attributes=True)


class OptimizationWeights(BaseModel):
    w_seat: int = Field(default=10, ge=0, le=500)
    w_gap: int = Field(default=80, ge=0, le=500)
    w_pack: int = Field(default=40, ge=0, le=500)
    w_building: int = Field(default=25, ge=0, le=500)
    w_pref: int = Field(default=15, ge=0, le=500)


class GenerateScheduleRequest(BaseModel):
    period_id: int | None = None
    preset: Literal["balanced", "best_fit", "compact_rooms", "custom"] = "balanced"
    weights: OptimizationWeights | None = None
    time_limit_seconds: float = Field(default=15.0, ge=1.0, le=300.0)
    respect_locked: bool = True


class ScheduleJobOut(BaseModel):
    job_id: str
    period_id: int
    status: Literal["pending", "running", "completed", "failed"]
    preset: str
    time_limit_seconds: float
    elapsed_ms: int
    error_message: str | None = None
    result: dict[str, Any] | None = None


class PreflightIssue(BaseModel):
    severity: Literal["error", "warning"]
    category: str
    message: str
    entity_ref: str | None = None


class PreflightReport(BaseModel):
    feasible: bool
    total_sessions: int
    total_required_slots: int
    total_available_room_slots: int
    issues: list[PreflightIssue] = []


class ScheduleEntryOut(BaseModel):
    id: int
    period_id: int
    run_id: int | None = None
    offering_id: int
    session_index: int
    room_id: int
    room_code: str
    room_name: str
    room_capacity: int
    room_type: str
    building_id: int
    building_code: str
    building_name: str
    day: str
    start_slot: int
    duration_slots: int
    time_range: str
    is_locked: bool
    is_manual_override: bool
    course_code: str
    course_name: str
    sks: int
    required_room_type: str
    class_id: int
    class_code: str
    extra_class_ids: list[int] = []
    extra_class_codes: list[str] = []
    shift: str
    program_id: int
    program_code: str
    program_name: str
    student_count: int
    seat_fill_pct: float
    seat_waste: int
    lecturer_id: int
    lecturer_name: str
    co_lecturer_id: int | None = None
    co_lecturer_name: str | None = None


class RoomEfficiencyMetric(BaseModel):
    room_id: int
    room_code: str
    room_name: str
    building_code: str
    building_name: str
    room_type: str
    capacity: int
    used_slots: int
    available_slots: int
    time_utilization_pct: float
    avg_seat_fill_pct: float
    total_seat_waste: int
    idle_gap_slots: int
    session_count: int
    status: Literal["Optimal", "Underutilized", "Oversized Match", "High Load", "Idle"]


class EfficiencySummary(BaseModel):
    period_id: int
    period_name: str
    run_id: int | None = None
    run_status: str | None = None
    preset: str | None = None
    solve_time_ms: int = 0
    total_sessions: int = 0
    total_rooms: int = 0
    active_rooms: int = 0
    room_time_utilization_pct: float = 0.0
    seat_fill_efficiency_pct: float = 0.0
    total_seat_waste_slots: int = 0
    idle_gap_count: int = 0
    efficiency_score: float = 0.0
    rooms: list[RoomEfficiencyMetric] = []
    heatmap: dict[str, dict[int, int]] = {}
    building_utilization: list[dict[str, Any]] = []


class MoveValidationRequest(BaseModel):
    entry_id: int
    target_day: str
    target_start_slot: int = Field(..., ge=1)
    target_room_id: int


class MoveValidationResponse(BaseModel):
    valid: bool
    conflicts: list[str] = []
    warnings: list[str] = []
    projected_seat_fill_pct: float = 0.0
    projected_seat_waste: int = 0


class MoveEntryRequest(BaseModel):
    target_day: str
    target_start_slot: int = Field(..., ge=1)
    target_room_id: int
    lock_after_move: bool = False
