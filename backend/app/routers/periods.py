from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AcademicPeriod,
    DEFAULT_BLOCKED_SLOTS,
    DEFAULT_BREAKS,
    DEFAULT_SHIFT_RULES,
)
from app.routers.helpers import format_period_out
from app.schemas import AcademicPeriodCreate, AcademicPeriodOut, AcademicPeriodUpdate
from app.seed import seed_sample_campus
from app.time_utils import validate_period_campus_rules


router = APIRouter(prefix="/api", tags=["Periods & Seed"])


@router.get("/periods", response_model=list[AcademicPeriodOut])
def list_periods(db: Session = Depends(get_db)):
    rows = db.query(AcademicPeriod).order_by(AcademicPeriod.id.desc()).all()
    return [format_period_out(r) for r in rows]


@router.post("/periods", response_model=AcademicPeriodOut, status_code=201)
def create_period(payload: AcademicPeriodCreate, db: Session = Depends(get_db)):
    if db.query(AcademicPeriod).filter(AcademicPeriod.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Nama periode akademik sudah ada.")
    if payload.is_active:
        db.query(AcademicPeriod).update({"is_active": False})
    data = payload.model_dump()
    if not data["breaks"]:
        data["breaks"] = [dict(b) for b in DEFAULT_BREAKS]
    if not data["blocked_slots"]:
        data["blocked_slots"] = [dict(b) for b in DEFAULT_BLOCKED_SLOTS]
    if not data["shift_rules"]:
        data["shift_rules"] = {
            k: {dk: list(dv) for dk, dv in v.items()} for k, v in DEFAULT_SHIFT_RULES.items()
        }

    rule_errors = validate_period_campus_rules(
        days=list(data["days"]),
        start_time=str(data["start_time"]),
        slot_minutes=int(data["slot_minutes"]),
        slots_per_day=int(data["slots_per_day"]),
        breaks=list(data["breaks"]),
    )
    if rule_errors:
        raise HTTPException(status_code=422, detail=" ".join(rule_errors))

    row = AcademicPeriod(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return format_period_out(row)


@router.put("/periods/{period_id}", response_model=AcademicPeriodOut)
def update_period(period_id: int, payload: AcademicPeriodUpdate, db: Session = Depends(get_db)):
    row = db.get(AcademicPeriod, period_id)
    if not row:
        raise HTTPException(status_code=404, detail="Periode akademik tidak ditemukan.")
    updates = payload.model_dump(exclude_unset=True)
    next_days = updates.get("days", row.days)
    next_start = updates.get("start_time", row.start_time)
    next_slot_min = updates.get("slot_minutes", row.slot_minutes)
    next_slots = updates.get("slots_per_day", row.slots_per_day)
    next_breaks = updates.get("breaks", row.breaks)

    rule_errors = validate_period_campus_rules(
        days=list(next_days),
        start_time=str(next_start),
        slot_minutes=int(next_slot_min),
        slots_per_day=int(next_slots),
        breaks=list(next_breaks),
    )
    if rule_errors:
        raise HTTPException(status_code=422, detail=" ".join(rule_errors))

    if updates.get("is_active") is True:
        db.query(AcademicPeriod).filter(AcademicPeriod.id != period_id).update({"is_active": False})
    for k, v in updates.items():
        setattr(row, k, v)
    # Keep shift_rules aligned with active days & slots_per_day
    if row.shift_rules and ("days" in updates or "slots_per_day" in updates):
        valid_slots = list(range(1, int(row.slots_per_day) + 1))
        row.shift_rules = {
            sh: {
                d: [s for s in slots if s <= int(row.slots_per_day)] or list(valid_slots)
                for d in row.days
                for slots in [dmap.get(d, valid_slots)]
            }
            for sh, dmap in row.shift_rules.items()
        }
    db.commit()
    db.refresh(row)
    return format_period_out(row)


@router.post("/periods/{period_id}/activate", response_model=AcademicPeriodOut)
def activate_period(period_id: int, db: Session = Depends(get_db)):
    row = db.get(AcademicPeriod, period_id)
    if not row:
        raise HTTPException(status_code=404, detail="Periode akademik tidak ditemukan.")
    db.query(AcademicPeriod).update({"is_active": False})
    row.is_active = True
    db.commit()
    db.refresh(row)
    return format_period_out(row)


@router.post("/periods/{period_id}/publish", response_model=AcademicPeriodOut)
def toggle_publish_period(period_id: int, db: Session = Depends(get_db)):
    row = db.get(AcademicPeriod, period_id)
    if not row:
        raise HTTPException(status_code=404, detail="Periode akademik tidak ditemukan.")
    row.status = "published" if row.status != "published" else "draft"
    db.commit()
    db.refresh(row)
    return format_period_out(row)


@router.delete("/periods/{period_id}", status_code=204)
def delete_period(period_id: int, db: Session = Depends(get_db)):
    row = db.get(AcademicPeriod, period_id)
    if not row:
        raise HTTPException(status_code=404, detail="Periode akademik tidak ditemukan.")
    db.delete(row)
    db.commit()


@router.post("/seed", response_model=AcademicPeriodOut)
def reset_seed_data(db: Session = Depends(get_db)):
    period = seed_sample_campus(db, reset=True)
    return format_period_out(period)
