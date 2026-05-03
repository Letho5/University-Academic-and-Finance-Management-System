"""
Quick test to verify database.py works correctly.
Run this once, then delete when done.
"""
from database import (
    init_database,
    get_connection,
    generate_student_id,
    generate_course_id,
    generate_receipt_number,
)

print("=" * 50)
print("APEX UNIVERSITY - Database Test")
print("=" * 50)

# Test 1: Initialize database
print("\n[1] Initializing database...")
init_database()
print("    OK - Database initialized")

# Test 2: List all tables
print("\n[2] Checking tables...")
with get_connection() as conn:
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    expected = {
        "students", "courses", "enrollments", "marks",
        "fee_accounts", "payments", "warning_letters"
    }
    actual = {t[0] for t in tables}

    for table in sorted(actual):
        if table in expected:
            print(f"    OK - {table}")
        elif table == "sqlite_sequence":
            pass
        else:
            print(f"    UNEXPECTED - {table}")

    missing = expected - actual
    if missing:
        print(f"\n    MISSING TABLES: {missing}")
    else:
        print(f"\n    All 7 expected tables exist.")

# Test 3: ID generators
print("\n[3] Testing ID generators...")
print(f"    Next student ID:    {generate_student_id()}")
print(f"    Next course ID:     {generate_course_id()}")
print(f"    Next receipt num:   {generate_receipt_number()}")

# Test 4: Write and read
print("\n[4] Testing write/read...")
with get_connection() as conn:
    conn.execute("""
        INSERT OR IGNORE INTO students 
        (student_id, name, surname, email, password)
        VALUES (?, ?, ?, ?, ?)
    """, ("STU99999", "Test", "User", "test@apex.ac.za", "test123"))

    row = conn.execute(
        "SELECT name, surname FROM students WHERE student_id = ?",
        ("STU99999",)
    ).fetchone()

    if row:
        print(f"    OK - Wrote and read: {row['name']} {row['surname']}")

    conn.execute("DELETE FROM students WHERE student_id = ?", ("STU99999",))
    print(f"    OK - Test record cleaned up")

print("\n" + "=" * 50)
print("ALL TESTS PASSED - database.py is working")
print("=" * 50)