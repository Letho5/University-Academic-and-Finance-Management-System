"""
modules/analytics.py
Read-only queries for the dashboard.
Returns plain Python types (dict, list) — UI-framework agnostic.
"""

from datetime import datetime, timedelta
from database import get_connection


def get_dashboard_kpis() -> dict:
    """
    Headline numbers for the dashboard top row.

    Returns:
        {
            "students":    int   -- total registered students
            "courses":     int   -- total courses in catalogue
            "revenue":     float -- total amount ever collected
            "outstanding": float -- total balance still owed
        }
    """
    with get_connection() as conn:
        students = conn.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        courses = conn.execute(
            "SELECT COUNT(*) FROM courses"
        ).fetchone()[0]

        # COALESCE handles the empty-table case (NULL becomes 0)
        revenue = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments"
        ).fetchone()[0]

        outstanding = conn.execute(
            "SELECT COALESCE(SUM(balance), 0) FROM fee_accounts"
        ).fetchone()[0]

    return {
        "students":    int(students),
        "courses":     int(courses),
        "revenue":     float(revenue),
        "outstanding": float(outstanding),
    }


def get_payments_timeseries(days: int = 30) -> list[dict]:
    """
    Daily payment totals for the last `days` days.

    Days with no payments are filled in with zero so the chart line
    is continuous instead of skipping dates.

    Returns:
        [{"date": "2026-04-15", "total": 0.0}, ...]
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT DATE(payment_date) AS day,
                   COALESCE(SUM(amount), 0) AS total
            FROM payments
            WHERE DATE(payment_date) >= DATE('now', ?)
            GROUP BY DATE(payment_date)
            ORDER BY day
        """, (f'-{days} days',)).fetchall()

    # Map of day -> total for fast lookup
    by_day = {row["day"]: float(row["total"]) for row in rows}

    # Fill every day in the range, zero where no payments exist
    today = datetime.now().date()
    series = []
    for offset in range(days, -1, -1):
        d = (today - timedelta(days=offset)).isoformat()
        series.append({"date": d, "total": by_day.get(d, 0.0)})
    return series


def get_recent_payments(limit: int = 5) -> list[dict]:
    """
    Most recent N payments with student names attached.
    Returns empty list if no payments exist.
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.receipt_number,
                   p.amount,
                   p.payment_method,
                   p.payment_date,
                   s.student_id,
                   s.name,
                   s.surname
            FROM payments p
            JOIN students s ON p.student_id = s.student_id
            ORDER BY p.payment_date DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [
        {
            "receipt_number": r["receipt_number"],
            "amount":         float(r["amount"]),
            "method":         r["payment_method"],
            "date":           r["payment_date"],
            "student_id":     r["student_id"],
            "student_name":   f"{r['name']} {r['surname']}",
        }
        for r in rows
    ]