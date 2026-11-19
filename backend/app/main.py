from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, init_db
from app.models import (
    AcademicPeriod,
    DEFAULT_BLOCKED_SLOTS,
    DEFAULT_BREAKS,
    DEFAULT_DAYS,
    DEFAULT_SHIFT_RULES,
    Lecturer,
    ScheduleEntry,
)
from app.routers import analytics, export, master_data, periods, schedule
from app.seed import seed_sample_campus


def _migrate_legacy_campus_window(db) -> None:
    """Align any legacy seeded period (Sabtu / 07:30 / 14 slots) to Senin-Jumat 08:00-16:20."""
    legacy_periods = (
        db.query(AcademicPeriod)
        .filter(AcademicPeriod.start_time == "07:30", AcademicPeriod.slots_per_day == 14)
        .all()
    )
    if not legacy_periods:
        return
    for p in legacy_periods:
        p.days = list(DEFAULT_DAYS)
        p.start_time = "08:00"
        p.slot_minutes = 50
        p.slots_per_day = 9
        p.breaks = [dict(b) for b in DEFAULT_BREAKS]
        p.blocked_slots = [dict(b) for b in DEFAULT_BLOCKED_SLOTS]
        p.shift_rules = {
            k: {dk: list(dv) for dk, dv in v.items()} for k, v in DEFAULT_SHIFT_RULES.items()
        }
        db.query(ScheduleEntry).filter(ScheduleEntry.period_id == p.id).delete()

    for lec in db.query(Lecturer).all():
        if lec.max_days_per_week > 5:
            lec.max_days_per_week = 5
        if lec.unavailable_slots:
            lec.unavailable_slots = [
                s for s in lec.unavailable_slots if s.get("day") in DEFAULT_DAYS and int(s.get("slot", 0)) <= 9
            ]
    db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    if settings.auto_seed:
        db = SessionLocal()
        try:
            seed_sample_campus(db, reset=False)
            _migrate_legacy_campus_window(db)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(periods.router)
app.include_router(master_data.router)
app.include_router(schedule.router)
app.include_router(analytics.router)
app.include_router(export.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}
