import os
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
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
    StudentClass,
    StudyProgram,
)
from app.seed import seed_sample_campus  # noqa: E402
from app.solver.engine import solve_schedule  # noqa: E402


@pytest.fixture()
def test_client(tmp_path):
    db_file = tmp_path / "test_kampus.db"
    engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    seed_sample_campus(db, reset=True)
    db.close()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    engine.dispose()


def test_solver_best_fit_room_efficiency():
    """Class of 22 students must pick the 25-seat room over 100-seat room (Best-Fit)."""
    period = AcademicPeriod(
        id=1,
        name="Test Period",
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
    room_small = Room(
        id=1, building_id=1, code="R-25", name="Small", floor=1, capacity=25, room_type="Teori", facilities=[], is_active=True
    )
    room_large = Room(
        id=2, building_id=1, code="R-100", name="Large", floor=1, capacity=100, room_type="Teori", facilities=[], is_active=True
    )
    lec = Lecturer(
        id=1, nidn="001", name="Dosen A", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[]
    )
    cls_small = StudentClass(
        id=1, period_id=1, program_id=1, code="IF-A", semester=1, shift="Reguler", student_count=22
    )
    course = Course(
        id=1, program_id=1, code="MK1", name="Matkul 1", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=[]
    )
    offering = CourseOffering(
        id=1, period_id=1, course_id=1, class_id=1, extra_class_ids=[], lecturer_id=1, sessions_per_week=1, session_duration_slots=2
    )

    out = solve_schedule(
        period=period,
        rooms=[room_large, room_small],
        classes=[cls_small],
        lecturers=[lec],
        courses=[course],
        offerings=[offering],
        preset="best_fit",
        time_limit_seconds=5.0,
    )
    assert out.status == "OPTIMAL"
    assert len(out.placements) == 1
    assert out.placements[0].room_id == 1


def test_solver_gap_compaction_on_single_room():
    """Two classes of 25 students in identical rooms should pack without idle gaps."""
    period = AcademicPeriod(
        id=1,
        name="Test Gap",
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
    room1 = Room(id=1, building_id=1, code="R-1", name="R1", floor=1, capacity=30, room_type="Teori", facilities=[], is_active=True)
    room2 = Room(id=2, building_id=1, code="R-2", name="R2", floor=1, capacity=30, room_type="Teori", facilities=[], is_active=True)
    l1 = Lecturer(id=1, nidn="01", name="L1", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[])
    l2 = Lecturer(id=2, nidn="02", name="L2", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[])
    c1 = StudentClass(id=1, period_id=1, program_id=1, code="C1", semester=1, shift="Reguler", student_count=25)
    c2 = StudentClass(id=2, period_id=1, program_id=1, code="C2", semester=1, shift="Reguler", student_count=25)
    mk1 = Course(id=1, program_id=1, code="MK1", name="MK1", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=[])
    mk2 = Course(id=2, program_id=1, code="MK2", name="MK2", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=[])
    o1 = CourseOffering(id=1, period_id=1, course_id=1, class_id=1, extra_class_ids=[], lecturer_id=1, sessions_per_week=1, session_duration_slots=2)
    o2 = CourseOffering(id=2, period_id=1, course_id=2, class_id=2, extra_class_ids=[], lecturer_id=2, sessions_per_week=1, session_duration_slots=2)

    out = solve_schedule(
        period=period,
        rooms=[room1, room2],
        classes=[c1, c2],
        lecturers=[l1, l2],
        courses=[mk1, mk2],
        offerings=[o1, o2],
        preset="compact_rooms",
        time_limit_seconds=5.0,
    )
    assert out.status == "OPTIMAL"
    assert len(out.placements) == 2
    # Must consolidate into the same room with zero gap
    assert out.placements[0].room_id == out.placements[1].room_id
    starts = sorted(p.start_slot for p in out.placements)
    assert starts[1] - starts[0] == 2


def test_full_api_generate_conflicts_analytics_and_exports(test_client: TestClient):
    # 1. Preflight check on seeded campus data
    res_pre = test_client.get("/api/schedule/preflight")
    assert res_pre.status_code == 200
    pre_data = res_pre.json()
    assert pre_data["feasible"] is True
    assert pre_data["total_sessions"] > 20

    # 2. Generate optimal/feasible schedule
    res_gen = test_client.post(
        "/api/schedule/generate",
        json={"preset": "balanced", "time_limit_seconds": 15.0, "respect_locked": True},
    )
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["status"] in ("OPTIMAL", "FEASIBLE")
    entries = gen_data["entries"]
    assert len(entries) == pre_data["total_sessions"]

    # Verify zero collisions across room, lecturer, and class + Monday-Friday 08:00-16:20 rules
    allowed_days = {"Senin", "Selasa", "Rabu", "Kamis", "Jumat"}
    occ_room, occ_lec, occ_cls = set(), set(), set()
    for e in entries:
        assert e["day"] in allowed_days
        start_hm, end_hm = e["time_range"].split("-")
        assert start_hm >= "08:00"
        assert end_hm <= "16:20"
        for offset in range(e["duration_slots"]):
            slot = e["start_slot"] + offset
            r_key = (e["room_id"], e["day"], slot)
            assert r_key not in occ_room
            occ_room.add(r_key)

            l_key = (e["lecturer_id"], e["day"], slot)
            assert l_key not in occ_lec
            occ_lec.add(l_key)
            if e["co_lecturer_id"]:
                cl_key = (e["co_lecturer_id"], e["day"], slot)
                assert cl_key not in occ_lec
                occ_lec.add(cl_key)

            for cid in [e["class_id"], *e["extra_class_ids"]]:
                c_key = (cid, e["day"], slot)
                assert c_key not in occ_cls
                occ_cls.add(c_key)

    # 3. Efficiency Analytics endpoint
    res_eff = test_client.get("/api/analytics/efficiency")
    assert res_eff.status_code == 200
    eff = res_eff.json()
    assert eff["seat_fill_efficiency_pct"] >= 70.0
    assert eff["efficiency_score"] > 0.0
    assert len(eff["rooms"]) == 30

    # 4. Conflict detection when moving entry onto another entry's room & time
    first, second = entries[0], entries[1]
    res_val = test_client.post(
        "/api/schedule/validate-move",
        json={
            "entry_id": first["id"],
            "target_day": second["day"],
            "target_start_slot": second["start_slot"],
            "target_room_id": second["room_id"],
        },
    )
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["valid"] is False
    assert len(val_data["conflicts"]) >= 1

    # 5. Lock entry and regenerate -> locked entry remains unchanged
    res_lock = test_client.post(f"/api/schedule/entries/{first['id']}/lock?locked=true")
    assert res_lock.status_code == 200
    assert res_lock.json()["is_locked"] is True

    res_regen = test_client.post(
        "/api/schedule/generate",
        json={"preset": "best_fit", "time_limit_seconds": 15.0, "respect_locked": True},
    )
    assert res_regen.status_code == 200
    matched = [
        e for e in res_regen.json()["entries"]
        if e["offering_id"] == first["offering_id"] and e["session_index"] == first["session_index"]
    ]
    assert len(matched) == 1
    assert matched[0]["day"] == first["day"]
    assert matched[0]["start_slot"] == first["start_slot"]
    assert matched[0]["room_id"] == first["room_id"]
    assert matched[0]["is_locked"] is True

    # 6. Export PDF, XLSX, ICS
    for ep, mime in [
        ("/api/export/pdf", "application/pdf"),
        ("/api/export/xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("/api/export/ics", "text/calendar"),
    ]:
        r = test_client.get(ep)
        assert r.status_code == 200
        assert mime in r.headers["content-type"]
        assert len(r.content) > 100


def test_campus_hours_and_weekdays_rules_enforced(test_client: TestClient):
    """Enforce Senin-Jumat and 08:00-16:20 rules across period API, conflict validator, and solver."""
    periods = test_client.get("/api/periods").json()
    pid = periods[0]["id"]

    # Reject Saturday
    r_sat = test_client.put(
        f"/api/periods/{pid}",
        json={"days": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]},
    )
    assert r_sat.status_code == 422

    # Reject start time before 08:00
    r_early = test_client.put(f"/api/periods/{pid}", json={"start_time": "07:30"})
    assert r_early.status_code == 422

    # Reject slots_per_day pushing end time past 16:20
    r_late = test_client.put(f"/api/periods/{pid}", json={"slots_per_day": 10})
    assert r_late.status_code == 422

    # Reject manual move to Saturday
    res_gen = test_client.post(
        "/api/schedule/generate",
        json={"preset": "balanced", "time_limit_seconds": 15.0, "respect_locked": True},
    )
    assert res_gen.status_code == 200
    first = res_gen.json()["entries"][0]
    r_move_sat = test_client.post(
        "/api/schedule/validate-move",
        json={
            "entry_id": first["id"],
            "target_day": "Sabtu",
            "target_start_slot": 1,
            "target_room_id": first["room_id"],
        },
    )
    assert r_move_sat.status_code == 200
    assert r_move_sat.json()["valid"] is False

    # Solver ignores out-of-window slots & Saturday even if manually supplied on model
    period = AcademicPeriod(
        id=99,
        name="Raw Window Test",
        year="2026/2027",
        semester_type="Ganjil",
        days=["Senin", "Sabtu"],
        start_time="07:00",
        slot_minutes=50,
        slots_per_day=12,
        breaks=[],
        blocked_slots=[],
        shift_rules={"Reguler": {"Senin": list(range(1, 13)), "Sabtu": list(range(1, 13))}},
    )
    room = Room(id=1, building_id=1, code="R1", name="R1", floor=1, capacity=30, room_type="Teori", facilities=[], is_active=True)
    lec = Lecturer(id=1, nidn="99", name="Dosen", max_sks_per_day=6, max_days_per_week=5, unavailable_slots=[], preferred_slots=[])
    cls = StudentClass(id=1, period_id=99, program_id=1, code="IF-X", semester=1, shift="Reguler", student_count=20)
    crs = Course(id=1, program_id=1, code="MKX", name="Test", sks=2, course_type="Teori", required_room_type="Teori", required_facilities=[])
    off = CourseOffering(id=1, period_id=99, course_id=1, class_id=1, extra_class_ids=[], lecturer_id=1, sessions_per_week=1, session_duration_slots=2)

    out = solve_schedule(
        period=period,
        rooms=[room],
        classes=[cls],
        lecturers=[lec],
        courses=[crs],
        offerings=[off],
        time_limit_seconds=5.0,
    )
    assert out.status == "OPTIMAL"
    assert len(out.placements) == 1
    p = out.placements[0]
    assert p.day == "Senin"
    # 07:00 -> slot 1 (07:00-07:50), slot 2 (07:50-08:40) -> earliest valid >= 08:00 is slot 3 (08:40)
    # Latest ending <= 16:20 -> slot 11 ends 16:10, slot 12 ends 17:00 -> start_slot must be in [3..10]
    assert 3 <= p.start_slot <= 10


def test_async_generate_job_and_polling(test_client: TestClient):
    """Async generate endpoint returns 202 immediately and polling returns the completed schedule."""
    res_start = test_client.post(
        "/api/schedule/generate-async",
        json={"preset": "balanced", "time_limit_seconds": 10.0, "respect_locked": True},
    )
    assert res_start.status_code == 202
    job = res_start.json()
    job_id = job["job_id"]
    assert job["status"] in ("pending", "running", "completed")
    assert job["period_id"] > 0

    final_job = job
    deadline = time.time() + 25.0
    while time.time() < deadline:
        poll = test_client.get(f"/api/schedule/jobs/{job_id}")
        assert poll.status_code == 200
        final_job = poll.json()
        if final_job["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)

    assert final_job["status"] == "completed", final_job.get("error_message")
    assert final_job["result"] is not None
    assert len(final_job["result"]["entries"]) == 75
    assert final_job["result"]["efficiency"]["seat_fill_efficiency_pct"] > 50.0
    assert final_job["elapsed_ms"] >= 0

    r_missing = test_client.get("/api/schedule/jobs/nonexistent-job-id")
    assert r_missing.status_code == 404


