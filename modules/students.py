"""
modules/students.py
Business logic for student registration & queries.
Q1: Student Registration Module.
"""

from database import get_connection, generate_student_id
from utils import (
    hash_password, validate_email, validate_dob, validate_password
)


def register_student(
    name: str, surname: str, dob: str, gender: str,
    email: str, phone: str, qualification: str,
    year_of_study: int, password: str, password2: str
) -> tuple[bool, str, str]:
    """
    Validate and insert a new student.
    Returns: (success, message, student_id).
    """
    # Required fields
    if not all([name, surname, dob, email, password, password2]):
        return False, "All required fields must be filled in.", ""

    if not name.replace(" ", "").isalpha():
        return False, "First name must contain letters only.", ""
    if not surname.replace(" ", "").isalpha():
        return False, "Surname must contain letters only.", ""

    dob_ok, dob_val = validate_dob(dob)
    if not dob_ok:
        return False, dob_val, ""

    if not validate_email(email):
        return False, "Please enter a valid email address.", ""

    pw_ok, pw_err = validate_password(password)
    if not pw_ok:
        return False, pw_err, ""
    if password != password2:
        return False, "Passwords do not match.", ""

    sid = generate_student_id()
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO students
                    (student_id, name, surname, date_of_birth, gender,
                     email, phone, password, qualification, year_of_study)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, name, surname, dob_val, gender,
                  email.lower(), phone, hash_password(password),
                  qualification, year_of_study))
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "That email address is already registered.", ""
        return False, f"Database error: {e}", ""

    return True, f"Student registered: {sid}", sid


def get_all_students() -> list[dict]:
    """Return all students as a list of dicts."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT student_id, name, surname, date_of_birth, gender,
                   email, phone, qualification, year_of_study, registered_on
            FROM students ORDER BY student_id
        """).fetchall()
    return [dict(r) for r in rows]


def delete_student(student_id: str) -> tuple[bool, str]:
    """Delete a student. Cascades to enrolments, marks, fees, etc."""
    with get_connection() as conn:
        result = conn.execute(
            "DELETE FROM students WHERE student_id = ?", (student_id,)
        )
        if result.rowcount == 0:
            return False, f"Student {student_id} not found."
    return True, f"Student {student_id} deleted."


def get_student_count() -> int:
    """Return total number of registered students."""
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]