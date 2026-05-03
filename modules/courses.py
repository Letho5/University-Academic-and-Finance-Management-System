"""
Q2 — Course Management
Pure logic: add, list, search, delete courses.
Returns (success: bool, message: str, data) tuples.
"""
import sqlite3
from database import get_connection
from utils import validate_fee, validate_duration


def _next_course_id(conn):
    cur = conn.execute(
        "SELECT course_id FROM courses ORDER BY course_id DESC LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        return "CRS001"
    last = int(row[0].replace("CRS", ""))
    return f"CRS{last + 1:03d}"


def add_course(course_name, course_code, duration, credits, semester, fee, lecturer):
    if not course_name or not course_name.strip():
        return False, "Course name is required.", None
    if not course_code or not course_code.strip():
        return False, "Course code is required.", None
    if not lecturer or not lecturer.strip():
        return False, "Lecturer name is required.", None

        # Fee comes from st.number_input as float — validate directly
    try:
        fee = float(fee)
        if fee < 0:
            return False, "Fee cannot be negative.", None
    except (ValueError, TypeError):
        return False, "Fee must be a valid number.", None

    ok, msg = validate_duration(duration)
    if not ok:
        return False, msg, None

    try:
        credits = int(credits)
        if credits <= 0:
            return False, "Credits must be a positive integer.", None
    except (ValueError, TypeError):
        return False, "Credits must be a valid integer.", None

    try:
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT course_id FROM courses WHERE UPPER(course_code) = ?",
                (course_code.upper().strip(),),
            )
            if cur.fetchone():
                return False, f"Course code '{course_code.upper()}' already exists.", None

            course_id = _next_course_id(conn)
            conn.execute(
                """INSERT INTO courses
                   (course_id, course_name, course_code, duration, credits,
                    semester, fee, lecturer)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    course_id,
                    course_name.strip(),
                    course_code.upper().strip(),
                    duration.strip(),
                    credits,
                    semester,
                    float(fee),
                    lecturer.strip(),
                ),
            )
            conn.commit()
            return True, f"Course {course_id} added successfully.", course_id
    except sqlite3.Error as e:
        return False, f"Database error: {e}", None


def get_all_courses():
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT course_id, course_code, course_name, duration, credits,
                      semester, fee, lecturer
               FROM courses ORDER BY course_id"""
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows] if rows else []


def search_courses(query):
    if not query or not query.strip():
        return get_all_courses()
    q = f"%{query.strip().lower()}%"
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT course_id, course_code, course_name, duration, credits,
                      semester, fee, lecturer
               FROM courses
               WHERE LOWER(course_id)   LIKE ?
                  OR LOWER(course_code) LIKE ?
                  OR LOWER(course_name) LIKE ?
                  OR LOWER(lecturer)    LIKE ?
               ORDER BY course_id""",
            (q, q, q, q),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows] if rows else []


def delete_course(course_id):
    if not course_id:
        return False, "Course ID is required."
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM enrollments WHERE course_id = ?", (course_id,)
            )
            count = cur.fetchone()[0]
            if count > 0:
                return False, f"Cannot delete: {count} enrollment(s) reference this course."

            cur = conn.execute(
                "SELECT course_id FROM courses WHERE course_id = ?", (course_id,)
            )
            if not cur.fetchone():
                return False, f"Course {course_id} not found."

            conn.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
            conn.commit()
            return True, f"Course {course_id} deleted."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"


def get_course(course_id):
    """Helper used later by enrollment / marks modules."""
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT course_id, course_code, course_name, duration, credits,
                      semester, fee, lecturer
               FROM courses WHERE course_id = ?""",
            (course_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None