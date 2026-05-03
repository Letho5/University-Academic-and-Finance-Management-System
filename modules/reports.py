"""
Q7 — Academic Report Generation (ReportLab PDF)
Generates a professional transcript per student.
Saves to reports/ and returns the file path.
"""
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import get_connection
from modules.marks import get_marks_for_student
from modules.fees import get_fee_account
from config import format_currency


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


# Brand palette (matches the app)
PURPLE_DARK = colors.HexColor("#6A3DE8")
PURPLE_LIGHT = colors.HexColor("#8B5FBF")
PINK = colors.HexColor("#FF6B9D")
TEXT_DARK = colors.HexColor("#2D2D44")
TEXT_MUTED = colors.HexColor("#8A8AA8")
LAVENDER = colors.HexColor("#EDE7F6")
WHITE = colors.HexColor("#FFFFFF")


# ------------------------------------------------------------------ #
def _draw_header_footer(canv: canvas.Canvas, doc):
    """Gradient header bar + page footer."""
    width, height = A4

    # --- Header gradient band (simulated with horizontal slices) ---
    band_height = 2.2 * cm
    y0 = height - band_height
    steps = 60
    for i in range(steps):
        t = i / (steps - 1)
        # Interpolate purple → pink
        r = (1 - t) * 0.416 + t * 1.0     # 0x6A → 0xFF
        g = (1 - t) * 0.239 + t * 0.420   # 0x3D → 0x6B
        b = (1 - t) * 0.910 + t * 0.616   # 0xE8 → 0x9D
        canv.setFillColorRGB(r, g, b)
        canv.rect(
            (i / steps) * width, y0,
            (width / steps) + 1, band_height,
            stroke=0, fill=1,
        )

    # Header text
    canv.setFillColor(WHITE)
    canv.setFont("Helvetica-Bold", 18)
    canv.drawString(2 * cm, height - 1.25 * cm, "APEX UNIVERSITY")
    canv.setFont("Helvetica", 9)
    canv.drawString(2 * cm, height - 1.75 * cm, "Academic Records Office")

    canv.setFont("Helvetica", 9)
    canv.drawRightString(
        width - 2 * cm, height - 1.25 * cm,
        "OFFICIAL ACADEMIC TRANSCRIPT",
    )
    canv.drawRightString(
        width - 2 * cm, height - 1.75 * cm,
        datetime.now().strftime("Issued: %d %B %Y"),
    )

    # --- Footer ---
    canv.setStrokeColor(PURPLE_LIGHT)
    canv.setLineWidth(0.6)
    canv.line(2 * cm, 1.6 * cm, width - 2 * cm, 1.6 * cm)
    canv.setFillColor(TEXT_MUTED)
    canv.setFont("Helvetica", 8)
    canv.drawString(2 * cm, 1.1 * cm, "APEX UNIVERSITY  ·  Academic Records  ·  This is a system-generated document.")
    canv.drawRightString(width - 2 * cm, 1.1 * cm, f"Page {doc.page}")


# ------------------------------------------------------------------ #
def _get_student(student_id):
    """Schema-tolerant student lookup — uses only columns that exist."""
    with get_connection() as conn:
        cols = [c["name"] for c in conn.execute(
            "PRAGMA table_info(students)"
        ).fetchall()]
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,),
        ).fetchone()

    if not row:
        return None

    data = dict(row)
    # Provide safe defaults for any fields the template references
    for key in ("dob", "gender", "email", "phone",
                "qualification", "year_of_study", "registered_on"):
        if key not in data:
            data[key] = None
    return data


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=16,
            textColor=TEXT_DARK, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_MUTED, spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=12,
            textColor=PURPLE_DARK, spaceBefore=10, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=14,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=TEXT_MUTED,
        ),
    }


# ------------------------------------------------------------------ #
def _student_info_table(student, styles):
    full_name = f"{student['name']} {student['surname']}"
    rows = [
        ["Student ID", student["student_id"], "Qualification", student.get("qualification") or "—"],
        ["Full Name", full_name, "Year of Study", str(student.get("year_of_study") or "—")],
        ["Email", student.get("email") or "—", "Phone", student.get("phone") or "—"],
        ["Date of Birth", student.get("dob") or "—", "Registered", student.get("registered_on") or "—"],
    ]
    t = Table(rows, colWidths=[3.2*cm, 5.5*cm, 3.2*cm, 5.1*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), TEXT_MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
        ("TEXTCOLOR", (3, 0), (3, -1), TEXT_DARK),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LAVENDER, WHITE]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.4, PURPLE_LIGHT),
    ]))
    return t


def _marks_table(marks):
    if not marks:
        return None
    header = ["Code", "Course", "Assign 1", "Assign 2", "Exam", "Final %", "Grade"]
    body = []
    for m in marks:
        body.append([
            m["course_code"],
            m["course_name"][:38],
            f"{m['assignment1']:.0f}",
            f"{m['assignment2']:.0f}",
            f"{m['exam']:.0f}",
            f"{m['final_mark']:.1f}",
            m["grade"],
        ])

    t = Table(
        [header] + body,
        colWidths=[2*cm, 6.5*cm, 1.8*cm, 1.8*cm, 1.6*cm, 1.8*cm, 2.5*cm],
        repeatRows=1,
    )

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_DARK),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LAVENDER]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BOX", (0, 0), (-1, -1), 0.4, PURPLE_LIGHT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, PURPLE_DARK),
    ]

    # Highlight grade column
    for i, m in enumerate(marks, start=1):
        g = m["grade"]
        if g == "Distinction":
            style_cmds.append(("TEXTCOLOR", (6, i), (6, i), PURPLE_DARK))
            style_cmds.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
        elif g == "Fail":
            style_cmds.append(("TEXTCOLOR", (6, i), (6, i), PINK))
            style_cmds.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
        elif g == "Supplementary":
            style_cmds.append(("TEXTCOLOR", (6, i), (6, i), PINK))

    t.setStyle(TableStyle(style_cmds))
    return t


def _summary_table(marks, account):
    if marks:
        finals = [m["final_mark"] for m in marks]
        avg = sum(finals) / len(finals)
        passed = sum(1 for m in marks if m["grade"] in ("Pass", "Distinction"))
        dist = sum(1 for m in marks if m["grade"] == "Distinction")
        supp = sum(1 for m in marks if m["grade"] == "Supplementary")
        failed = sum(1 for m in marks if m["grade"] == "Fail")
        avg_str = f"{avg:.1f}%"
    else:
        avg_str = "—"
        passed = dist = supp = failed = 0

    bal_str = format_currency(account["balance"]) if account else "No account"
    paid_str = format_currency(account["total_paid"]) if account else "—"

    rows = [
        ["Courses Assessed", str(len(marks)), "Average", avg_str],
        ["Distinctions", str(dist), "Passes", str(passed)],
        ["Supplementary", str(supp), "Fails", str(failed)],
        ["Fees Paid", paid_str, "Outstanding", bal_str],
    ]
    t = Table(rows, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), TEXT_MUTED),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, -1), PURPLE_DARK),
        ("TEXTCOLOR", (3, 0), (3, -1), PURPLE_DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LAVENDER]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BOX", (0, 0), (-1, -1), 0.4, PURPLE_LIGHT),
    ]))
    return t


# ------------------------------------------------------------------ #
def generate_academic_report(student_id):
    """Build a transcript PDF and return (success, message, file_path)."""
    student = _get_student(student_id)
    if not student:
        return False, f"Student {student_id} not found.", None

    marks = get_marks_for_student(student_id)
    account = get_fee_account(student_id)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcript_{student_id}_{timestamp}.pdf"
    filepath = REPORTS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=3*cm, bottomMargin=2.2*cm,
        title=f"Academic Transcript - {student_id}",
        author="APEX UNIVERSITY",
    )

    styles = _styles()
    story = []

    full_name = f"{student['name']} {student['surname']}"
    story.append(Paragraph("Academic Transcript", styles["title"]))
    story.append(Paragraph(
        f"This document certifies the academic record of <b>{full_name}</b> "
        f"as held by APEX University on "
        f"{datetime.now().strftime('%d %B %Y')}.",
        styles["subtitle"],
    ))

    story.append(Paragraph("Student Information", styles["section"]))
    story.append(_student_info_table(student, styles))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Course Marks", styles["section"]))
    marks_tbl = _marks_table(marks)
    if marks_tbl:
        story.append(marks_tbl)
    else:
        story.append(Paragraph(
            "No marks have been captured for this student to date.",
            styles["muted"],
        ))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Summary", styles["section"]))
    story.append(_summary_table(marks, account))
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph(
        "Issued by the Academic Records Office, APEX University. "
        "This transcript is valid only when accompanied by the official institutional seal.",
        styles["muted"],
    ))

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)

    return True, f"Transcript generated: {filename}", str(filepath)


def list_generated_reports():
    """Return list of dicts of all PDFs in reports/ folder."""
    if not REPORTS_DIR.exists():
        return []
    items = []
    for p in sorted(REPORTS_DIR.glob("*.pdf"), key=os.path.getmtime, reverse=True):
        stat = p.stat()
        items.append({
            "filename": p.name,
            "path": str(p),
            "size_kb": round(stat.st_size / 1024, 1),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return items