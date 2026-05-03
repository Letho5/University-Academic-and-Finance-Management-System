"""
Q8 — Warning Letter Generation (ReportLab PDF)
Issues a formal academic warning letter for at-risk students.
Logs to warning_letters table; saves PDF to warnings/ folder.
"""
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfgen import canvas

from database import get_connection
from modules.risk import get_student_risk
from config import format_currency


WARNINGS_DIR = Path("warnings")
WARNINGS_DIR.mkdir(exist_ok=True)


# Brand palette
PURPLE_DARK = colors.HexColor("#6A3DE8")
PURPLE_LIGHT = colors.HexColor("#8B5FBF")
PINK = colors.HexColor("#FF6B9D")
TEXT_DARK = colors.HexColor("#2D2D44")
TEXT_MUTED = colors.HexColor("#8A8AA8")
LAVENDER = colors.HexColor("#EDE7F6")
WHITE = colors.HexColor("#FFFFFF")
WARN_BG = colors.HexColor("#FFF1F5")  # soft pink background for the warning panel


# ------------------------------------------------------------------ #
def _draw_header_footer(canv: canvas.Canvas, doc):
    """Gradient header bar + page footer (matches transcript style)."""
    width, height = A4

    band_height = 2.2 * cm
    y0 = height - band_height
    steps = 60
    for i in range(steps):
        t = i / (steps - 1)
        r = (1 - t) * 0.416 + t * 1.0
        g = (1 - t) * 0.239 + t * 0.420
        b = (1 - t) * 0.910 + t * 0.616
        canv.setFillColorRGB(r, g, b)
        canv.rect(
            (i / steps) * width, y0,
            (width / steps) + 1, band_height,
            stroke=0, fill=1,
        )

    canv.setFillColor(WHITE)
    canv.setFont("Helvetica-Bold", 18)
    canv.drawString(2 * cm, height - 1.25 * cm, "APEX UNIVERSITY")
    canv.setFont("Helvetica", 9)
    canv.drawString(2 * cm, height - 1.75 * cm, "Office of the Registrar")

    canv.setFont("Helvetica", 9)
    canv.drawRightString(
        width - 2 * cm, height - 1.25 * cm,
        "OFFICIAL ACADEMIC WARNING",
    )
    canv.drawRightString(
        width - 2 * cm, height - 1.75 * cm,
        datetime.now().strftime("Issued: %d %B %Y"),
    )

    canv.setStrokeColor(PURPLE_LIGHT)
    canv.setLineWidth(0.6)
    canv.line(2 * cm, 1.6 * cm, width - 2 * cm, 1.6 * cm)
    canv.setFillColor(TEXT_MUTED)
    canv.setFont("Helvetica", 8)
    canv.drawString(2 * cm, 1.1 * cm, "APEX UNIVERSITY  ·  Office of the Registrar  ·  Confidential — addressee only.")
    canv.drawRightString(width - 2 * cm, 1.1 * cm, f"Page {doc.page}")


# ------------------------------------------------------------------ #
def _get_student(student_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    for key in ("email", "phone", "qualification", "year_of_study"):
        data.setdefault(key, None)
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
            fontName="Helvetica", fontSize=10.5,
            textColor=TEXT_DARK, leading=15, spaceAfter=8,
        ),
        "warn_title": ParagraphStyle(
            "warn_title", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=11,
            textColor=PINK, spaceAfter=6,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=TEXT_MUTED, leading=13,
        ),
    }


def _addressee_block(student, profile, styles):
    full_name = f"{student['name']} {student['surname']}"
    rows = [
        ["Student", full_name],
        ["Student ID", student["student_id"]],
        ["Qualification", student.get("qualification") or "—"],
        ["Year of Study", str(student.get("year_of_study") or "—")],
        ["Email", student.get("email") or "—"],
        ["Risk Level", profile["risk_level"]],
    ]
    t = Table(rows, colWidths=[3.5 * cm, 13.3 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MUTED),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LAVENDER, WHITE]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.4, PURPLE_LIGHT),
    ]))

    # Highlight risk level cell
    risk_color = PINK if profile["risk_level"] == "HIGH" else PURPLE_DARK
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (1, 5), (1, 5), risk_color),
    ]))
    return t


def _indicators_panel(profile, styles):
    """Soft pink panel listing the risk indicators."""
    avg = f"{profile['average']:.1f}%" if profile["average"] is not None else "—"
    bal = format_currency(profile["balance"])

    indicators_html = "".join(
        f"<br/>•&nbsp;&nbsp;{r}" for r in profile["reasons"]
    )

    text = (
        f"<b>Risk Indicators</b>"
        f"<br/><font color='#8A8AA8'>Academic average: <b>{avg}</b> &nbsp;·&nbsp; "
        f"Failed courses: <b>{profile['fails']}</b> &nbsp;·&nbsp; "
        f"Supplementary: <b>{profile['supplementary']}</b> &nbsp;·&nbsp; "
        f"Outstanding: <b>{bal}</b></font>"
        f"{indicators_html}"
    )

    panel_style = ParagraphStyle(
        "panel", fontName="Helvetica", fontSize=10,
        textColor=TEXT_DARK, leading=15,
    )
    para = Paragraph(text, panel_style)

    wrap = Table([[para]], colWidths=[16.8 * cm])
    wrap.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARN_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, PINK),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return wrap


def _build_letter_body(student, profile, custom_reason, styles):
    full_name = f"{student['name']} {student['surname']}"
    risk = profile["risk_level"]

    if risk == "HIGH":
        severity = (
            "Your current academic and/or financial standing places you at "
            "<b>HIGH RISK</b> of academic exclusion."
        )
        actions = (
            "You are required to <b>meet with your academic advisor within 7 working days</b> "
            "of receipt of this letter to develop a remediation plan. Failure to do so may "
            "result in the suspension of your registration for the next academic period."
        )
    elif risk == "MEDIUM":
        severity = (
            "Your current standing indicates a <b>MEDIUM</b> level of academic risk that "
            "requires your immediate attention."
        )
        actions = (
            "You are strongly encouraged to consult with your academic advisor and the "
            "Finance Office to address the matters listed below before the end of the term."
        )
    else:
        severity = (
            "This letter serves as a courtesy notice regarding aspects of your academic "
            "record that warrant attention."
        )
        actions = (
            "We recommend that you review the indicators below and take corrective action "
            "during this academic period."
        )

    reason_block = ""
    if custom_reason and custom_reason.strip():
        reason_block = (
            f"<br/><br/><b>Specific Reason:</b> {custom_reason.strip()}"
        )

    body_text = (
        f"Dear {full_name},"
        f"<br/><br/>"
        f"{severity}{reason_block}"
        f"<br/><br/>"
        f"{actions}"
        f"<br/><br/>"
        f"APEX University is committed to your success. Support services — including "
        f"academic advising, tutoring, counselling, and financial aid guidance — are "
        f"available to all students. Please engage with these resources at your earliest "
        f"opportunity."
        f"<br/><br/>"
        f"This letter has been added to your official student record."
    )
    return Paragraph(body_text, styles["body"])


def _signature_block(styles):
    text = (
        "<br/><br/>Yours sincerely,"
        "<br/><br/><br/>"
        "<b>The Registrar</b><br/>"
        "Office of the Registrar<br/>"
        "APEX University"
    )
    return Paragraph(text, styles["body"])


# ------------------------------------------------------------------ #
def _log_warning(student_id, reason, file_path):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO warning_letters (student_id, reason, file_path, issued_on)
               VALUES (?, ?, ?, ?)""",
            (
                student_id,
                reason or "Academic risk warning",
                file_path,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()


def generate_warning_letter(student_id, custom_reason=""):
    """Build a warning letter PDF and return (success, message, file_path)."""
    student = _get_student(student_id)
    if not student:
        return False, f"Student {student_id} not found.", None

    profile = get_student_risk(student_id)
    if not profile:
        return False, "Could not compute risk profile.", None

    if profile["risk_level"] == "NONE":
        return False, (
            "This student is in good standing — no warning indicators found. "
            "You can still issue one by adding a custom reason if required."
        ), None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"warning_{student_id}_{timestamp}.pdf"
    filepath = WARNINGS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=3 * cm, bottomMargin=2.2 * cm,
        title=f"Academic Warning - {student_id}",
        author="APEX UNIVERSITY",
    )

    styles = _styles()
    story = []

    story.append(Paragraph("Notice of Academic Warning", styles["title"]))
    story.append(Paragraph(
        f"Reference: <b>WARN-{student_id}-{datetime.now().strftime('%Y%m%d')}</b> &nbsp;·&nbsp; "
        f"Date: {datetime.now().strftime('%d %B %Y')}",
        styles["subtitle"],
    ))

    story.append(Paragraph("Addressee", styles["section"]))
    story.append(_addressee_block(student, profile, styles))
    story.append(Spacer(1, 0.4 * cm))

    story.append(_build_letter_body(student, profile, custom_reason, styles))
    story.append(Spacer(1, 0.2 * cm))

    story.append(_indicators_panel(profile, styles))
    story.append(Spacer(1, 0.3 * cm))

    story.append(_signature_block(styles))

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)

    # Log to DB
    try:
        _log_warning(student_id, custom_reason, str(filepath))
    except sqlite3.Error as e:
        return True, f"Letter generated but DB log failed: {e}", str(filepath)

    return True, f"Warning letter issued: {filename}", str(filepath)


def get_warning_log():
    """All warnings issued, newest first, with student name joined."""
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT w.id, w.student_id,
                   s.name || ' ' || s.surname AS student_name,
                   w.reason, w.file_path, w.issued_on
            FROM warning_letters w
            LEFT JOIN students s ON s.student_id = w.student_id
            ORDER BY w.issued_on DESC
        """)
        return [dict(r) for r in cur.fetchall()]


def list_generated_warnings():
    """List all PDFs currently on disk."""
    if not WARNINGS_DIR.exists():
        return []
    items = []
    for p in sorted(WARNINGS_DIR.glob("*.pdf"), key=os.path.getmtime, reverse=True):
        stat = p.stat()
        items.append({
            "filename": p.name,
            "path": str(p),
            "size_kb": round(stat.st_size / 1024, 1),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return items