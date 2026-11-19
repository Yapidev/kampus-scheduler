from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.helpers import PeriodContext, filter_and_format_entries, load_period_context
from app.services.exporter import export_schedule_ics, export_schedule_pdf, export_schedule_xlsx
from app.solver.metrics import compute_efficiency_metrics
from app.time_utils import compute_time_slots


router = APIRouter(prefix="/api/export", tags=["Export"])


def _scope_label(
    ctx: PeriodContext,
    program_id: int | None,
    class_id: int | None,
    lecturer_id: int | None,
    room_id: int | None,
) -> str:
    parts: list[str] = []
    if program_id and program_id in ctx.programs_by_id:
        p = ctx.programs_by_id[program_id]
        parts.append(f"Prodi {p.name}")
    if class_id and class_id in ctx.classes_by_id:
        parts.append(f"Kelas {ctx.classes_by_id[class_id].code}")
    if lecturer_id and lecturer_id in ctx.lecturers_by_id:
        parts.append(f"Dosen {ctx.lecturers_by_id[lecturer_id].name}")
    if room_id and room_id in ctx.rooms_by_id:
        parts.append(f"Ruangan {ctx.rooms_by_id[room_id].code}")
    return " | ".join(parts) if parts else "Seluruh Kampus"


@router.get("/pdf")
def download_pdf(
    period_id: int | None = None,
    program_id: int | None = None,
    class_id: int | None = None,
    lecturer_id: int | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
):
    ctx = load_period_context(db, period_id)
    entries = filter_and_format_entries(ctx, program_id, class_id, lecturer_id, room_id)
    eff = compute_efficiency_metrics(
        period=ctx.period,
        rooms=ctx.rooms,
        buildings_by_id=ctx.buildings_by_id,
        entries=ctx.entries,
        offerings_by_id=ctx.offerings_by_id,
        classes_by_id=ctx.classes_by_id,
        run=ctx.latest_run,
    )
    scope = _scope_label(ctx, program_id, class_id, lecturer_id, room_id)
    pdf_bytes = export_schedule_pdf(ctx.period.name, scope, entries, eff)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="jadwal-kampus.pdf"'},
    )


@router.get("/xlsx")
def download_xlsx(
    period_id: int | None = None,
    program_id: int | None = None,
    class_id: int | None = None,
    lecturer_id: int | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
):
    ctx = load_period_context(db, period_id)
    entries = filter_and_format_entries(ctx, program_id, class_id, lecturer_id, room_id)
    eff = compute_efficiency_metrics(
        period=ctx.period,
        rooms=ctx.rooms,
        buildings_by_id=ctx.buildings_by_id,
        entries=ctx.entries,
        offerings_by_id=ctx.offerings_by_id,
        classes_by_id=ctx.classes_by_id,
        run=ctx.latest_run,
    )
    scope = _scope_label(ctx, program_id, class_id, lecturer_id, room_id)
    xlsx_bytes = export_schedule_xlsx(ctx.period.name, scope, entries, eff)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="jadwal-kampus.xlsx"'},
    )


@router.get("/ics")
def download_ics(
    period_id: int | None = None,
    program_id: int | None = None,
    class_id: int | None = None,
    lecturer_id: int | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
):
    ctx = load_period_context(db, period_id)
    entries = filter_and_format_entries(ctx, program_id, class_id, lecturer_id, room_id)
    slot_meta_by_idx = {s.index: s for s in compute_time_slots(ctx.period)}
    ics_bytes = export_schedule_ics(ctx.period.name, entries, slot_meta_by_idx)
    return Response(
        content=ics_bytes,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="jadwal-kampus.ics"'},
    )
