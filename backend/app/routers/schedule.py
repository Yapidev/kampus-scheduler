import threading
import time
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.models import ScheduleEntry, ScheduleRun
from app.routers.helpers import filter_and_format_entries, load_period_context
from app.schemas import (
    GenerateScheduleRequest,
    MoveEntryRequest,
    MoveValidationRequest,
    MoveValidationResponse,
    PreflightReport,
    ScheduleEntryOut,
    ScheduleJobOut,
)
from app.services.conflict_checker import validate_entry_move
from app.solver.engine import solve_schedule
from app.solver.metrics import compute_efficiency_metrics
from app.solver.preflight import run_preflight_audit


router = APIRouter(prefix="/api/schedule", tags=["Schedule & Solver"])

_JOBS_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}


def _prune_jobs() -> None:
    if len(_JOBS) <= 50:
        return
    finished = [
        jid for jid, j in _JOBS.items() if j["status"] in ("completed", "failed")
    ]
    for jid in finished[: max(0, len(_JOBS) - 40)]:
        _JOBS.pop(jid, None)


def _run_preflight_and_validate(db: Session, payload: GenerateScheduleRequest):
    ctx = load_period_context(db, payload.period_id)
    locked = [e for e in ctx.entries if e.is_locked] if payload.respect_locked else []
    preflight = run_preflight_audit(
        period=ctx.period,
        rooms=ctx.rooms,
        classes=ctx.classes,
        lecturers=ctx.lecturers,
        courses=ctx.courses,
        offerings=ctx.offerings,
        locked_entries=locked,
    )
    if not preflight.feasible:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Data belum layak untuk digenerate. Perbaiki masalah pre-flight berikut.",
                "issues": [i.model_dump() for i in preflight.issues],
            },
        )
    return ctx, locked


def _execute_solve_and_persist(
    db: Session, payload: GenerateScheduleRequest
) -> dict[str, Any]:
    ctx, locked = _run_preflight_and_validate(db, payload)
    manual_flags = {
        (e.offering_id, e.session_index): e.is_manual_override for e in locked
    }

    solve_out = solve_schedule(
        period=ctx.period,
        rooms=ctx.rooms,
        classes=ctx.classes,
        lecturers=ctx.lecturers,
        courses=ctx.courses,
        offerings=ctx.offerings,
        locked_entries=locked,
        preset=payload.preset,
        custom_weights=payload.weights,
        time_limit_seconds=payload.time_limit_seconds,
    )

    if solve_out.status == "INFEASIBLE":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Tidak ditemukan solusi jadwal yang bebas bentrok.",
                "errors": solve_out.errors,
            },
        )

    db.query(ScheduleEntry).filter(ScheduleEntry.period_id == ctx.period.id).delete()

    run = ScheduleRun(
        period_id=ctx.period.id,
        status=solve_out.status,
        preset=payload.preset,
        weights_json=solve_out.weights_used,
        solve_time_ms=solve_out.solve_time_ms,
        total_sessions=len(solve_out.placements),
    )
    db.add(run)
    db.flush()

    new_entries: list[ScheduleEntry] = []
    for p in solve_out.placements:
        entry = ScheduleEntry(
            period_id=ctx.period.id,
            run_id=run.id,
            offering_id=p.offering_id,
            session_index=p.session_index,
            room_id=p.room_id,
            day=p.day,
            start_slot=p.start_slot,
            duration_slots=p.duration_slots,
            is_locked=p.is_locked,
            is_manual_override=manual_flags.get((p.offering_id, p.session_index), False),
        )
        new_entries.append(entry)
    db.add_all(new_entries)
    db.flush()

    efficiency = compute_efficiency_metrics(
        period=ctx.period,
        rooms=ctx.rooms,
        buildings_by_id=ctx.buildings_by_id,
        entries=new_entries,
        offerings_by_id=ctx.offerings_by_id,
        classes_by_id=ctx.classes_by_id,
        run=run,
    )

    run.room_time_utilization = efficiency.room_time_utilization_pct
    run.seat_fill_efficiency = efficiency.seat_fill_efficiency_pct
    run.idle_gap_count = efficiency.idle_gap_count
    run.efficiency_score = efficiency.efficiency_score
    run.metrics_json = efficiency.model_dump()
    db.commit()

    fresh_ctx = load_period_context(db, ctx.period.id)
    entries_out = filter_and_format_entries(fresh_ctx)
    return {
        "run_id": run.id,
        "status": run.status,
        "preset": run.preset,
        "solve_time_ms": run.solve_time_ms,
        "efficiency": efficiency.model_dump(),
        "entries": [e.model_dump() for e in entries_out],
    }


def _serialize_job(job: dict[str, Any]) -> ScheduleJobOut:
    elapsed = (
        int((time.monotonic() - job["started_mono"]) * 1000)
        if job["status"] in ("pending", "running")
        else int(job["final_elapsed_ms"])
    )
    return ScheduleJobOut(
        job_id=job["job_id"],
        period_id=job["period_id"],
        status=job["status"],
        preset=job["preset"],
        time_limit_seconds=job["time_limit_seconds"],
        elapsed_ms=elapsed,
        error_message=job.get("error_message"),
        result=job.get("result"),
    )


@router.get("/preflight", response_model=PreflightReport)
def preflight_check(
    period_id: int | None = None,
    respect_locked: bool = True,
    db: Session = Depends(get_db),
):
    ctx = load_period_context(db, period_id)
    locked = [e for e in ctx.entries if e.is_locked] if respect_locked else []
    return run_preflight_audit(
        period=ctx.period,
        rooms=ctx.rooms,
        classes=ctx.classes,
        lecturers=ctx.lecturers,
        courses=ctx.courses,
        offerings=ctx.offerings,
        locked_entries=locked,
    )


@router.post("/generate")
def generate_schedule(payload: GenerateScheduleRequest, db: Session = Depends(get_db)):
    return _execute_solve_and_persist(db, payload)


@router.post("/generate-async", response_model=ScheduleJobOut, status_code=202)
def generate_schedule_async(payload: GenerateScheduleRequest, db: Session = Depends(get_db)):
    ctx, _locked = _run_preflight_and_validate(db, payload)
    period_id = ctx.period.id

    with _JOBS_LOCK:
        for existing in _JOBS.values():
            if existing["period_id"] == period_id and existing["status"] in ("pending", "running"):
                raise HTTPException(
                    status_code=409,
                    detail="Proses generate jadwal sedang berjalan untuk periode ini.",
                )

        _prune_jobs()
        job_id = uuid.uuid4().hex
        job_record: dict[str, Any] = {
            "job_id": job_id,
            "period_id": period_id,
            "status": "pending",
            "preset": payload.preset,
            "time_limit_seconds": payload.time_limit_seconds,
            "started_mono": time.monotonic(),
            "final_elapsed_ms": 0,
            "error_message": None,
            "result": None,
        }
        _JOBS[job_id] = job_record

    bind = db.get_bind()
    WorkerSession = sessionmaker(bind=bind, autoflush=False, autocommit=False, expire_on_commit=False)
    job_payload = payload.model_copy(update={"period_id": period_id})

    def _worker():
        worker_db = WorkerSession()
        with _JOBS_LOCK:
            _JOBS[job_id]["status"] = "running"
        try:
            res = _execute_solve_and_persist(worker_db, job_payload)
            with _JOBS_LOCK:
                _JOBS[job_id]["status"] = "completed"
                _JOBS[job_id]["final_elapsed_ms"] = int(
                    (time.monotonic() - _JOBS[job_id]["started_mono"]) * 1000
                )
                _JOBS[job_id]["result"] = res
        except HTTPException as exc:
            msg = (
                exc.detail.get("message")
                if isinstance(exc.detail, dict)
                else str(exc.detail)
            )
            with _JOBS_LOCK:
                _JOBS[job_id]["status"] = "failed"
                _JOBS[job_id]["final_elapsed_ms"] = int(
                    (time.monotonic() - _JOBS[job_id]["started_mono"]) * 1000
                )
                _JOBS[job_id]["error_message"] = msg or "Generate jadwal gagal."
        except Exception as exc:
            with _JOBS_LOCK:
                _JOBS[job_id]["status"] = "failed"
                _JOBS[job_id]["final_elapsed_ms"] = int(
                    (time.monotonic() - _JOBS[job_id]["started_mono"]) * 1000
                )
                _JOBS[job_id]["error_message"] = str(exc) or "Terjadi kesalahan internal solver."
        finally:
            worker_db.close()

    threading.Thread(target=_worker, daemon=True).start()
    with _JOBS_LOCK:
        return _serialize_job(_JOBS[job_id])


@router.get("/jobs/{job_id}", response_model=ScheduleJobOut)
def get_generate_job_status(job_id: str):
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job generate tidak ditemukan.")
        return _serialize_job(job)


@router.get("", response_model=list[ScheduleEntryOut])
def get_schedule(
    period_id: int | None = None,
    program_id: int | None = None,
    class_id: int | None = None,
    lecturer_id: int | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
):
    ctx = load_period_context(db, period_id)
    return filter_and_format_entries(
        ctx=ctx,
        program_id=program_id,
        class_id=class_id,
        lecturer_id=lecturer_id,
        room_id=room_id,
    )


@router.get("/runs")
def list_schedule_runs(period_id: int | None = None, db: Session = Depends(get_db)):
    ctx = load_period_context(db, period_id)
    runs = (
        db.query(ScheduleRun)
        .filter(ScheduleRun.period_id == ctx.period.id)
        .order_by(ScheduleRun.id.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": r.id,
            "period_id": r.period_id,
            "status": r.status,
            "preset": r.preset,
            "weights_json": r.weights_json,
            "solve_time_ms": r.solve_time_ms,
            "total_sessions": r.total_sessions,
            "room_time_utilization": r.room_time_utilization,
            "seat_fill_efficiency": r.seat_fill_efficiency,
            "idle_gap_count": r.idle_gap_count,
            "efficiency_score": r.efficiency_score,
            "created_at": r.created_at,
        }
        for r in runs
    ]


@router.post("/validate-move", response_model=MoveValidationResponse)
def validate_move(payload: MoveValidationRequest, db: Session = Depends(get_db)):
    entry = db.get(ScheduleEntry, payload.entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri jadwal tidak ditemukan.")
    ctx = load_period_context(db, entry.period_id)
    target_room = ctx.rooms_by_id.get(payload.target_room_id)
    return validate_entry_move(
        period=ctx.period,
        moving_entry=entry,
        target_day=payload.target_day,
        target_start_slot=payload.target_start_slot,
        target_room=target_room,
        all_entries=ctx.entries,
        offerings_by_id=ctx.offerings_by_id,
        courses_by_id=ctx.courses_by_id,
        classes_by_id=ctx.classes_by_id,
        lecturers_by_id=ctx.lecturers_by_id,
        rooms_by_id=ctx.rooms_by_id,
    )


@router.patch("/entries/{entry_id}", response_model=ScheduleEntryOut)
def move_entry(entry_id: int, payload: MoveEntryRequest, db: Session = Depends(get_db)):
    entry = db.get(ScheduleEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri jadwal tidak ditemukan.")
    ctx = load_period_context(db, entry.period_id)
    target_room = ctx.rooms_by_id.get(payload.target_room_id)
    check = validate_entry_move(
        period=ctx.period,
        moving_entry=entry,
        target_day=payload.target_day,
        target_start_slot=payload.target_start_slot,
        target_room=target_room,
        all_entries=ctx.entries,
        offerings_by_id=ctx.offerings_by_id,
        courses_by_id=ctx.courses_by_id,
        classes_by_id=ctx.classes_by_id,
        lecturers_by_id=ctx.lecturers_by_id,
        rooms_by_id=ctx.rooms_by_id,
    )
    if not check.valid:
        raise HTTPException(
            status_code=409,
            detail={"message": "Perpindahan jadwal memicu bentrok.", "conflicts": check.conflicts},
        )

    entry.day = payload.target_day
    entry.start_slot = payload.target_start_slot
    entry.room_id = payload.target_room_id
    entry.is_manual_override = True
    if payload.lock_after_move:
        entry.is_locked = True
    db.commit()
    db.refresh(entry)

    fresh_ctx = load_period_context(db, entry.period_id)
    formatted = filter_and_format_entries(fresh_ctx)
    match = next((x for x in formatted if x.id == entry.id), None)
    assert match is not None
    return match


@router.post("/entries/{entry_id}/lock", response_model=ScheduleEntryOut)
def toggle_lock_entry(entry_id: int, locked: bool | None = None, db: Session = Depends(get_db)):
    entry = db.get(ScheduleEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entri jadwal tidak ditemukan.")
    entry.is_locked = (not entry.is_locked) if locked is None else locked
    db.commit()
    fresh_ctx = load_period_context(db, entry.period_id)
    formatted = filter_and_format_entries(fresh_ctx)
    match = next((x for x in formatted if x.id == entry.id), None)
    assert match is not None
    return match


@router.delete("", status_code=204)
def clear_schedule(
    period_id: int | None = None,
    include_locked: bool = False,
    db: Session = Depends(get_db),
):
    ctx = load_period_context(db, period_id)
    q = db.query(ScheduleEntry).filter(ScheduleEntry.period_id == ctx.period.id)
    if not include_locked:
        q = q.filter(ScheduleEntry.is_locked.is_(False))
    q.delete(synchronize_session=False)
    db.commit()
