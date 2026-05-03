"""
Q6 — Academic Risk Detection
Combines academic performance + financial standing into a risk profile per student.
"""
from database import get_connection
from modules.fees import get_fee_account


HIGH_BALANCE_THRESHOLD = 5000.00
MEDIUM_BALANCE_THRESHOLD = 1000.00


def _academic_summary(conn, student_id):
    """Aggregate marks for one student."""
    rows = conn.execute(
        """SELECT final_mark, grade
           FROM marks
           WHERE student_id = ?""",
        (student_id,),
    ).fetchall()

    if not rows:
        return {
            "courses_assessed": 0,
            "average": None,
            "fails": 0,
            "supplementary": 0,
            "passes": 0,
            "distinctions": 0,
        }

    finals = [float(r["final_mark"]) for r in rows]
    return {
        "courses_assessed": len(rows),
        "average": round(sum(finals) / len(finals), 2),
        "fails": sum(1 for r in rows if r["grade"] == "Fail"),
        "supplementary": sum(1 for r in rows if r["grade"] == "Supplementary"),
        "passes": sum(1 for r in rows if r["grade"] == "Pass"),
        "distinctions": sum(1 for r in rows if r["grade"] == "Distinction"),
    }


def _classify(avg, fails, supp, balance):
    """Return (level, reasons[])."""
    reasons = []

    # HIGH triggers
    if fails > 0:
        reasons.append(f"{fails} failed course(s)")
    if avg is not None and avg < 50:
        reasons.append(f"Average below 50% ({avg}%)")
    if balance >= HIGH_BALANCE_THRESHOLD:
        reasons.append(f"High outstanding balance (R {balance:,.2f})")

    if reasons:
        return "HIGH", reasons

    # MEDIUM triggers
    if supp > 0:
        reasons.append(f"{supp} supplementary result(s)")
    if avg is not None and 50 <= avg < 60:
        reasons.append(f"Average in marginal range ({avg}%)")
    if MEDIUM_BALANCE_THRESHOLD <= balance < HIGH_BALANCE_THRESHOLD:
        reasons.append(f"Outstanding balance (R {balance:,.2f})")

    if reasons:
        return "MEDIUM", reasons

    # LOW triggers
    if avg is not None and avg < 75:
        reasons.append(f"Average below distinction ({avg}%)")
        return "LOW", reasons

    if avg is None:
        return "NONE", ["No marks captured yet"]

    return "NONE", ["Performing well; account in good standing"]


def get_student_risk(student_id):
    """Risk profile for a single student."""
    with get_connection() as conn:
        student = conn.execute(
            """SELECT student_id, name, surname, email,
                      qualification, year_of_study
               FROM students WHERE student_id = ?""",
            (student_id,),
        ).fetchone()
        if not student:
            return None

        academic = _academic_summary(conn, student_id)

    account = get_fee_account(student_id)
    balance = float(account["balance"]) if account else 0.0

    level, reasons = _classify(
        academic["average"],
        academic["fails"],
        academic["supplementary"],
        balance,
    )

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "surname": student["surname"],
        "email": student["email"],
        "qualification": student["qualification"],
        "year_of_study": student["year_of_study"],
        "courses_assessed": academic["courses_assessed"],
        "average": academic["average"],
        "fails": academic["fails"],
        "supplementary": academic["supplementary"],
        "passes": academic["passes"],
        "distinctions": academic["distinctions"],
        "balance": balance,
        "risk_level": level,
        "reasons": reasons,
    }


def get_all_risk_profiles():
    """Risk profile for every student in the database."""
    with get_connection() as conn:
        ids = [r["student_id"] for r in conn.execute(
            "SELECT student_id FROM students ORDER BY surname, name"
        ).fetchall()]

    return [p for p in (get_student_risk(sid) for sid in ids) if p]


def get_at_risk_students(min_level="MEDIUM"):
    """Students at MEDIUM+ risk (used by warnings module)."""
    order = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
    threshold = order.get(min_level.upper(), 2)
    return [
        p for p in get_all_risk_profiles()
        if order.get(p["risk_level"], 0) >= threshold
    ]


def get_risk_summary():
    profiles = get_all_risk_profiles()
    return {
        "total": len(profiles),
        "high": sum(1 for p in profiles if p["risk_level"] == "HIGH"),
        "medium": sum(1 for p in profiles if p["risk_level"] == "MEDIUM"),
        "low": sum(1 for p in profiles if p["risk_level"] == "LOW"),
        "none": sum(1 for p in profiles if p["risk_level"] == "NONE"),
    }