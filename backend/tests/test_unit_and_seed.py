import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base  # noqa: E402
from app.models import (  # noqa: E402
    AcademicPeriod,
    Building,
    Course,
    CourseOffering,
    DEFAULT_BLOCKED_SLOTS,
    DEFAULT_BREAKS,
    DEFAULT_DAYS,
    DEFAULT_SHIFT_RULES,
    Faculty,
    Lecturer,
    Room,
    ScheduleEntry,
    StudentClass,
    StudyProgram,
)
from app.seed import seed_sample_campus  # noqa: E402
from app.services.conflict_checker import validate_entry_move  # noqa: E402
from app.solver.domain import is_room_compatible  # noqa: E402
from app.solver.metrics import compute_efficiency_metrics  # noqa: E402
from app.solver.preflight import run_preflight_audit  # noqa: E402
from app.time_utils import (  # noqa: E402
    compute_time_slots_raw,
    is_interval_valid_for_blocks,
    validate_period_campus_rules,
)


@pytest.fixture()
def db_session(tmp_path):
    db_file = tmp_path / "unit_test.db"
    engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def test_seed_creates_8_faculties_and_passes_preflight(db_session):
    """Seed must populate 8 faculties, 14 programs, 4 buildings, 30 rooms, 32 lecturers, 25 classes, and pass preflight."""
    period = seed_sample_campus(db_session, reset=False)
    assert period.days == ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
    assert period.start_time == "08:00"
    assert period.slots_per_day == 9

    faculties = db_session.query(Faculty).all()
    programs = db_session.query(StudyProgram).all()
    buildings = db_session.query(Building).all()
    rooms = db_session.query(Room).all()
    lecturers = db_session.query(Lecturer).all()
    classes = db_session.query(StudentClass).filter(StudentClass.period_id == period.id).all()
    courses = db_session.query(Course).all()
    offerings = (
        db_session.query(CourseOffering).filter(CourseOffering.period_id == period.id).all()
    )

    assert len(faculties) == 8
    assert len(programs) == 14
    assert len(buildings) == 4
    assert len(rooms) == 30
    assert len(lecturers) == 32
    assert len(classes) == 25
    assert len(courses) >= 45
    assert len(offerings) >= 70

    # Every faculty must have at least 1 program, class, and offering
    prog_ids_by_fac: dict[int, set[int]] = {f.id: set() for f in faculties}
    for p in programs:
        prog_ids_by_fac[p.faculty_id].add(p.id)
    cls_by_id = {c.id: c for c in classes}

    for f in faculties:
        f_progs = prog_ids_by_fac[f.id]
        assert len(f_progs) >= 1
        f_classes = [c for c in classes if c.program_id in f_progs]
        assert len(f_classes) >= 1
        f_offerings = [
            o for o in offerings if cls_by_id[o.class_id].program_id in f_progs
        ]
        assert len(f_offerings) >= 2

    # Idempotency check
    seed_sample_campus(db_session, reset=False)
    assert db_session.query(Faculty).count() == 8

    # Reset check
    seed_sample_campus(db_session, reset=True)
    assert db_session.query(Faculty).count() == 8
    assert db_session.query(Room).count() == 30

    # Preflight feasibility check on full 8-faculty dataset
    fresh_period = db_session.query(AcademicPeriod).first()
    fresh_rooms = db_session.query(Room).all()
    fresh_classes = db_session.query(StudentClass).all()
    fresh_lecturers = db_session.query(Lecturer).all()
    fresh_courses = db_session.query(Course).all()
    fresh_offerings = db_session.query(CourseOffering).all()

    report = run_preflight_audit(
        period=fresh_period,
        rooms=fresh_rooms,
        classes=fresh_classes,
        lecturers=fresh_lecturers,
        courses=fresh_courses,
        offerings=fresh_offerings,
    )
    assert report.feasible is True, f"Preflight errors: {report.issues}"
    assert report.total_sessions == len(fresh_offerings)


def test_time_utils_slots_blocks_and_campus_rules():
    slots = compute_time_slots_raw("08:00", 50, 9, DEFAULT_BREAKS)
    assert len(slots) == 9
    assert slots[0].start_time == "08:00"
    assert slots[0].end_time == "08:50"
    assert slots[4].end_time == "12:10"
    assert slots[5].start_time == "13:00"  # After 50-min ISHOMA break
    assert slots[8].end_time == "16:20"

    slot_map = {s.index: s for s in slots}
    assert is_interval_valid_for_blocks(1, 3, slot_map) is True
    assert is_interval_valid_for_blocks(3, 3, slot_map) is True
    assert is_interval_valid_for_blocks(6, 4, slot_map) is True
    assert is_interval_valid_for_blocks(4, 3, slot_map) is False  # Crosses ISHOMA
    assert is_interval_valid_for_blocks(8, 3, slot_map) is False  # Out of range

    assert validate_period_campus_rules(DEFAULT_DAYS, "08:00", 50, 9, DEFAULT_BREAKS) == []
    assert len(validate_period_campus_rules([], "08:00", 50, 9, DEFAULT_BREAKS)) >= 1
    assert len(validate_period_campus_rules(["Senin", "Sabtu"], "08:00", 50, 9, DEFAULT_BREAKS)) >= 1
    assert len(validate_period_campus_rules(DEFAULT_DAYS, "07:30", 50, 9, DEFAULT_BREAKS)) >= 1
    assert len(validate_period_campus_rules(DEFAULT_DAYS, "08:00", 50, 10, DEFAULT_BREAKS)) >= 1


def test_domain_is_room_compatible():
    crs_teori = Course(
        id=1, program_id=1, code="MK1", name="Teori", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=["Proyektor"]
    )
    crs_lab = Course(
        id=2, program_id=1, code="MK2", name="Lab", sks=3, course_type="Praktikum", required_room_type="Lab Komputer", required_facilities=["PC Workstation"]
    )
    r_small = Room(
        id=1, building_id=1, code="A-101", name="Small", floor=1, capacity=28, room_type="Teori", facilities=["Proyektor"], is_active=True
    )
    r_inactive = Room(
        id=2, building_id=1, code="A-102", name="Off", floor=1, capacity=50, room_type="Teori", facilities=["Proyektor"], is_active=False
    )
    r_aula = Room(
        id=3, building_id=1, code="AULA", name="Aula", floor=1, capacity=120, room_type="Aula", facilities=["Proyektor"], is_active=True
    )
    r_lab_no_pc = Room(
        id=4, building_id=1, code="LAB", name="Lab", floor=1, capacity=40, room_type="Lab Komputer", facilities=["Proyektor"], is_active=True
    )

    assert is_room_compatible(r_small, crs_teori, 25)[0] is True
    assert is_room_compatible(r_small, crs_teori, 30)[0] is False  # Capacity too small
    assert is_room_compatible(r_inactive, crs_teori, 20)[0] is False  # Inactive
    assert is_room_compatible(r_aula, crs_teori, 30)[0] is False  # Small class should not spill into Aula
    assert is_room_compatible(r_aula, crs_teori, 75)[0] is True   # Large merged class (>60) allowed in Aula
    assert is_room_compatible(r_lab_no_pc, crs_lab, 25)[0] is False  # Missing PC Workstation


def test_metrics_efficiency_gap_and_status_classification():
    period = AcademicPeriod(
        id=1,
        name="Metrics Test",
        year="2026/2027",
        semester_type="Ganjil",
        days=["Senin"],
        start_time="08:00",
        slot_minutes=50,
        slots_per_day=5,
        breaks=[],
        blocked_slots=[],
        shift_rules={"Reguler": {"Senin": [1, 2, 3, 4, 5]}},
    )
    bld = Building(id=1, code="GDA", name="Gedung A", floor_count=2, campus_zone="Utama")
    r_opt = Room(id=1, building_id=1, code="R-1", name="R1", floor=1, capacity=30, room_type="Teori", facilities=[], is_active=True)
    r_over = Room(id=2, building_id=1, code="R-2", name="R2", floor=1, capacity=80, room_type="Teori", facilities=[], is_active=True)
    r_idle = Room(id=3, building_id=1, code="R-3", name="R3", floor=1, capacity=40, room_type="Teori", facilities=[], is_active=True)

    c_27 = StudentClass(id=1, period_id=1, program_id=1, code="C1", semester=1, shift="Reguler", student_count=27)
    c_20 = StudentClass(id=2, period_id=1, program_id=1, code="C2", semester=1, shift="Reguler", student_count=20)
    o1 = CourseOffering(id=1, period_id=1, course_id=1, class_id=1, extra_class_ids=[], lecturer_id=1, sessions_per_week=1, session_duration_slots=2)
    o2 = CourseOffering(id=2, period_id=1, course_id=2, class_id=2, extra_class_ids=[], lecturer_id=2, sessions_per_week=1, session_duration_slots=2)

    # Place o1 at slots 1-2 and o2 at slots 4-5 in R-1 -> leaves slot 3 as 1 idle gap!
    # Also place another session in R-2 (80 cap) with 20 students -> Oversized Match
    o3 = CourseOffering(id=3, period_id=1, course_id=3, class_id=2, extra_class_ids=[], lecturer_id=3, sessions_per_week=1, session_duration_slots=2)
    entries = [
        ScheduleEntry(id=1, period_id=1, offering_id=1, session_index=1, room_id=1, day="Senin", start_slot=1, duration_slots=2, is_locked=False, is_manual_override=False),
        ScheduleEntry(id=2, period_id=1, offering_id=2, session_index=1, room_id=1, day="Senin", start_slot=4, duration_slots=2, is_locked=False, is_manual_override=False),
        ScheduleEntry(id=3, period_id=1, offering_id=3, session_index=1, room_id=2, day="Senin", start_slot=1, duration_slots=2, is_locked=False, is_manual_override=False),
    ]
    summary = compute_efficiency_metrics(
        period=period,
        rooms=[r_opt, r_over, r_idle],
        buildings_by_id={1: bld},
        entries=entries,
        offerings_by_id={1: o1, 2: o2, 3: o3},
        classes_by_id={1: c_27, 2: c_20},
    )
    by_code = {m.room_code: m for m in summary.rooms}
    assert by_code["R-1"].idle_gap_slots == 1
    assert by_code["R-1"].status == "Optimal"
    assert by_code["R-2"].status == "Oversized Match"
    assert by_code["R-3"].status == "Idle"
    assert summary.idle_gap_count == 1
    assert summary.active_rooms == 2


def test_conflict_checker_co_lecturer_and_merged_classes():
    period = AcademicPeriod(
        id=1,
        name="Conflict Test",
        year="2026/2027",
        semester_type="Ganjil",
        days=list(DEFAULT_DAYS),
        start_time="08:00",
        slot_minutes=50,
        slots_per_day=9,
        breaks=list(DEFAULT_BREAKS),
        blocked_slots=list(DEFAULT_BLOCKED_SLOTS),
        shift_rules=DEFAULT_SHIFT_RULES,
    )
    r1 = Room(id=1, building_id=1, code="R-1", name="R1", floor=1, capacity=100, room_type="Teori", facilities=[], is_active=True)
    r2 = Room(id=2, building_id=1, code="R-2", name="R2", floor=1, capacity=100, room_type="Teori", facilities=[], is_active=True)
    l1 = Lecturer(id=1, nidn="01", name="Dosen Utama", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[])
    l2 = Lecturer(id=2, nidn="02", name="Co Dosen", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[])
    l3 = Lecturer(id=3, nidn="03", name="Dosen Lain", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[{"day": "Selasa", "slot": 1}], preferred_slots=[])

    c1 = StudentClass(id=1, period_id=1, program_id=1, code="IF-1A", semester=1, shift="Reguler", student_count=35)
    c2 = StudentClass(id=2, period_id=1, program_id=1, code="IF-1B", semester=1, shift="Reguler", student_count=35)

    mk1 = Course(id=1, program_id=1, code="MK1", name="MK1", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=[])
    mk2 = Course(id=2, program_id=1, code="MK2", name="MK2", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=[])

    # Offering 1 teaches IF-1A + IF-1B with co-lecturer l2 at Senin slot 1-2 in R-1
    o1 = CourseOffering(id=1, period_id=1, course_id=1, class_id=1, extra_class_ids=[2], lecturer_id=1, co_lecturer_id=2, sessions_per_week=1, session_duration_slots=2)
    # Offering 2 teaches IF-1B with co-lecturer l2 / primary l3 at Senin slot 6-7 in R-2
    o2 = CourseOffering(id=2, period_id=1, course_id=2, class_id=2, extra_class_ids=[], lecturer_id=3, co_lecturer_id=2, sessions_per_week=1, session_duration_slots=2)

    e1 = ScheduleEntry(id=1, period_id=1, offering_id=1, session_index=1, room_id=1, day="Senin", start_slot=1, duration_slots=2, is_locked=False, is_manual_override=False)
    e2 = ScheduleEntry(id=2, period_id=1, offering_id=2, session_index=1, room_id=2, day="Senin", start_slot=6, duration_slots=2, is_locked=False, is_manual_override=False)

    # Moving e2 onto Senin slot 1 in R-2 should catch BOTH co-lecturer (l2) & merged class (IF-1B) conflicts!
    res = validate_entry_move(
        period=period,
        moving_entry=e2,
        target_day="Senin",
        target_start_slot=1,
        target_room=r2,
        all_entries=[e1, e2],
        offerings_by_id={1: o1, 2: o2},
        courses_by_id={1: mk1, 2: mk2},
        classes_by_id={1: c1, 2: c2},
        lecturers_by_id={1: l1, 2: l2, 3: l3},
        rooms_by_id={1: r1, 2: r2},
    )
    assert res.valid is False
    assert any("Co Dosen" in c for c in res.conflicts)
    assert any("IF-1B" in c for c in res.conflicts)

    # Moving e2 onto Jumat slot 5 must be rejected (blocked Sholat Jumat)
    res_fri = validate_entry_move(
        period=period,
        moving_entry=e2,
        target_day="Jumat",
        target_start_slot=4,
        target_room=r2,
        all_entries=[e1, e2],
        offerings_by_id={1: o1, 2: o2},
        courses_by_id={1: mk1, 2: mk2},
        classes_by_id={1: c1, 2: c2},
        lecturers_by_id={1: l1, 2: l2, 3: l3},
        rooms_by_id={1: r1, 2: r2},
    )
    assert res_fri.valid is False
    assert any("diblokir" in c.lower() for c in res_fri.conflicts)
