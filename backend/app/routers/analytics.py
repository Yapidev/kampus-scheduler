from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.helpers import load_period_context
from app.schemas import EfficiencySummary
from app.solver.metrics import compute_efficiency_metrics


router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/efficiency", response_model=EfficiencySummary)
def get_efficiency_analytics(period_id: int | None = None, db: Session = Depends(get_db)):
    ctx = load_period_context(db, period_id)
    return compute_efficiency_metrics(
        period=ctx.period,
        rooms=ctx.rooms,
        buildings_by_id=ctx.buildings_by_id,
        entries=ctx.entries,
        offerings_by_id=ctx.offerings_by_id,
        classes_by_id=ctx.classes_by_id,
        run=ctx.latest_run,
    )
