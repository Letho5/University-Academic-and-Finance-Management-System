"""
seed_demo.py
One-time script to populate the database with demo data
so the dashboard has something to show.

Run with:    python seed_demo.py
Safe to run multiple times — won't duplicate the demo student.
"""

from database import init_database, generate_student_id, get_connection
from modules.fees import setup_fee_account, make_payment
from utils import hash_password


def seed():
    init_database()

    # Don't recreate the demo student if they already exist
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT student_id FROM students WHERE email = ?",
            ("sarah@apex.ac.za",)
        ).fetchone()

    if existing:
        print(f"Demo student already exists: {existing['student_id']}")
        return

    # Create one demo student
    sid = generate_student_id()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO students
                (student_id, name, surname, email, password, year_of_study)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sid, "Sarah", "Mokoena", "sarah@apex.ac.za",
              hash_password("Test1234"), 2))
    print(f"Created student: {sid}")

    # Set up fee account and record three payments
    setup_fee_account(sid, 9250.00)
    make_payment(sid, 4500.00, "EFT", "REF-001")
    make_payment(sid, 1500.00, "Card", "TXN-7842")
    make_payment(sid, 800.00,  "Cash", "")
    print(f"Three payments recorded for {sid}")
    print("Done.")


if __name__ == "__main__":
    seed()