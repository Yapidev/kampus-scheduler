from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas import EfficiencySummary, ScheduleEntryOut


DAY_ORDER = {"Senin": 0, "Selasa": 1, "Rabu": 2, "Kamis": 3, "Jumat": 4, "Sabtu": 5, "Minggu": 6}
ICS_BYDAY = {
    "Senin": "MO",
    "Selasa": "TU",
    "Rabu": "WE",
    "Kamis": "TH",
    "Jumat": "FR",
    "Sabtu": "SA",
    "Minggu": "SU",
}


def _sorted_entries(entries: list[ScheduleEntryOut]) -> list[ScheduleEntryOut]:
    return sorted(
        entries,
        key=lambda e: (DAY_ORDER.get(e.day, 99), e.start_slot, e.room_code, e.class_code),
    )


def export_schedule_pdf(
    period_name: str,
    title_scope: str,
    entries: list[ScheduleEntryOut],
    efficiency: EfficiencySummary | None = None,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )
    styles = getSampleStyleSheet()
    elements: list[Any] = []

    elements.append(Paragraph(f"<b>Jadwal Kuliah — {period_name}</b>", styles["Title"]))
    elements.append(Paragraph(f"Cakupan: {title_scope}", styles["Heading3"]))
    if efficiency:
        summary_text = (
            f"Skor Efisiensi Ruangan: <b>{efficiency.efficiency_score}%</b> | "
            f"Seat Fill Efficiency: <b>{efficiency.seat_fill_efficiency_pct}%</b> | "
            f"Utilisasi Waktu Ruang: <b>{efficiency.room_time_utilization_pct}%</b> | "
            f"Idle Gap: <b>{efficiency.idle_gap_count}</b>"
        )
        elements.append(Paragraph(summary_text, styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [
        [
            "Hari",
            "Jam (Slot)",
            "Kode MK",
            "Mata Kuliah",
            "SKS",
            "Kelas",
            "Dosen Pengampu",
            "Ruangan",
            "Keterisian",
        ]
    ]
    for e in _sorted_entries(entries):
        cls_label = e.class_code + (f" + {', '.join(e.extra_class_codes)}" if e.extra_class_codes else "")
        lec_label = e.lecturer_name + (f" / {e.co_lecturer_name}" if e.co_lecturer_name else "")
        data.append(
            [
                e.day,
                f"{e.time_range}\n(Slot {e.start_slot}-{e.start_slot + e.duration_slots - 1})",
                e.course_code,
                e.course_name,
                str(e.sks),
                cls_label,
                lec_label,
                f"{e.room_code} ({e.building_code})",
                f"{e.student_count}/{e.room_capacity}\n({e.seat_fill_pct}%)",
            ]
        )

    if len(data) == 1:
        data.append(["-", "-", "-", "Tidak ada data jadwal pada filter ini", "-", "-", "-", "-", "-"])

    table = Table(
        data,
        colWidths=[54, 86, 62, 165, 32, 82, 145, 86, 68],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return buf.getvalue()


def export_schedule_xlsx(
    period_name: str,
    title_scope: str,
    entries: list[ScheduleEntryOut],
    efficiency: EfficiencySummary | None = None,
) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Jadwal Kuliah"

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(size=14, bold=True)

    ws["A1"] = f"Jadwal Kuliah — {period_name}"
    ws["A1"].font = title_font
    ws["A2"] = f"Cakupan: {title_scope}"

    headers = [
        "Hari",
        "Jam",
        "Slot Mulai",
        "Durasi (Slot)",
        "Prodi",
        "Kode MK",
        "Mata Kuliah",
        "SKS",
        "Kelas",
        "Shift",
        "Dosen Pengampu",
        "Gedung",
        "Ruangan",
        "Tipe Ruang",
        "Jumlah Mhs",
        "Kapasitas Ruang",
        "Seat Fill (%)",
        "Sisa Kursi",
    ]
    ws.append([])
    ws.append(headers)
    header_row = 4
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for e in _sorted_entries(entries):
        cls_label = e.class_code + (f" + {', '.join(e.extra_class_codes)}" if e.extra_class_codes else "")
        lec_label = e.lecturer_name + (f" / {e.co_lecturer_name}" if e.co_lecturer_name else "")
        ws.append(
            [
                e.day,
                e.time_range,
                e.start_slot,
                e.duration_slots,
                e.program_code,
                e.course_code,
                e.course_name,
                e.sks,
                cls_label,
                e.shift,
                lec_label,
                e.building_name,
                e.room_code,
                e.room_type,
                e.student_count,
                e.room_capacity,
                e.seat_fill_pct,
                e.seat_waste,
            ]
        )

    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(40, max(10, max_len + 3))

    if efficiency:
        ws2 = wb.create_sheet(title="Efisiensi Ruangan")
        ws2["A1"] = f"Ringkasan Efisiensi Ruangan — {period_name}"
        ws2["A1"].font = title_font
        ws2.append(["Skor Efisiensi Keseluruhan (%)", efficiency.efficiency_score])
        ws2.append(["Seat Fill Efficiency (%)", efficiency.seat_fill_efficiency_pct])
        ws2.append(["Utilisasi Waktu Ruangan (%)", efficiency.room_time_utilization_pct])
        ws2.append(["Total Idle Gap (Slot)", efficiency.idle_gap_count])
        ws2.append(["Total Seat Waste (Kursi-Slot)", efficiency.total_seat_waste_slots])
        ws2.append([])

        r_headers = [
            "Kode Ruang",
            "Nama Ruang",
            "Gedung",
            "Tipe",
            "Kapasitas",
            "Slot Terpakai",
            "Slot Tersedia",
            "Utilisasi Waktu (%)",
            "Seat Fill (%)",
            "Idle Gap",
            "Status",
        ]
        ws2.append(r_headers)
        for col_idx in range(1, len(r_headers) + 1):
            c = ws2.cell(row=8, column=col_idx)
            c.fill = header_fill
            c.font = header_font

        for rm in efficiency.rooms:
            ws2.append(
                [
                    rm.room_code,
                    rm.room_name,
                    rm.building_code,
                    rm.room_type,
                    rm.capacity,
                    rm.used_slots,
                    rm.available_slots,
                    rm.time_utilization_pct,
                    rm.avg_seat_fill_pct,
                    rm.idle_gap_slots,
                    rm.status,
                ]
            )
        for col in ws2.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws2.column_dimensions[col[0].column_letter].width = min(35, max(10, max_len + 3))

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def export_schedule_ics(
    period_name: str,
    entries: list[ScheduleEntryOut],
    slot_meta_by_idx: dict[int, Any],
    weeks: int = 16,
) -> bytes:
    # Anchor on the Monday of the current week for clean recurring events
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CampusFlow//Jadwal Kampus//ID",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_escape('Jadwal ' + period_name)}",
        "X-WR-TIMEZONE:Asia/Jakarta",
    ]

    for e in _sorted_entries(entries):
        day_offset = DAY_ORDER.get(e.day, 0)
        event_date = monday + timedelta(days=day_offset)
        s_start = slot_meta_by_idx.get(e.start_slot)
        s_end = slot_meta_by_idx.get(e.start_slot + e.duration_slots - 1)
        start_hm = (s_start.start_time if s_start else "08:00").replace(":", "")
        end_hm = (s_end.end_time if s_end else "09:40").replace(":", "")

        dtstart = f"{event_date.strftime('%Y%m%d')}T{start_hm}00"
        dtend = f"{event_date.strftime('%Y%m%d')}T{end_hm}00"
        byday = ICS_BYDAY.get(e.day, "MO")
        cls_label = e.class_code + (f" + {', '.join(e.extra_class_codes)}" if e.extra_class_codes else "")
        desc = (
            f"Mata Kuliah: {e.course_code} - {e.course_name} ({e.sks} SKS)\\n"
            f"Kelas: {cls_label}\\n"
            f"Dosen: {e.lecturer_name}\\n"
            f"Keterisian: {e.student_count}/{e.room_capacity} ({e.seat_fill_pct}%)"
        )

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:campusflow-{e.period_id}-{e.id}@kampus.local",
                f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;TZID=Asia/Jakarta:{dtstart}",
                f"DTEND;TZID=Asia/Jakarta:{dtend}",
                f"RRULE:FREQ=WEEKLY;COUNT={weeks};BYDAY={byday}",
                f"SUMMARY:{_ics_escape(f'[{e.course_code}] {e.course_name} ({cls_label})')}",
                f"LOCATION:{_ics_escape(f'{e.room_code} - {e.building_name}')}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")
