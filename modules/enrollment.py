"""
Q3 — Student Enrollment
Logic: enroll, list, remove, check capacity.
Rules: max 6 courses per student per (year + semester); no duplicates.
"""
import sqlite3
from datetime import datetime
from database import get_connection
from config import MAX_COURSES_PER_SEMESTER


def enroll_student(student_id, course_id, academic_year, semester):
    if not student_id or not course_id:
        return False, "Student and course are required.", None
    if not academic_year:
        return False, "Academic year is required.", None
    if not semester:
        return False, "Semester is required.", None

    try:
        with get_connection() as conn:
            if not conn.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone():
                return False, f"Student {student_id} not found.", None

            if not conn.execute(
                "SELECT 1 FROM courses WHERE course_id = ?", (course_id,)
            ).fetchone():
                return False, f"Course {course_id} not found.", None

            dup = conn.execute(
                """SELECT 1 FROM enrollments
                   WHERE student_id = ? AND course_id = ?
                     AND academic_year = ? AND semester = ?""",
                (student_id, course_id, academic_year, semester),
            ).fetchone()
            if dup:
                return False, "Student is already enrolled in this course for that semester.", None

            count = conn.execute(
                """SELECT COUNT(*) FROM enrollments
                   WHERE student_id = ? AND academic_year = ? AND semester = ?""",
                (student_id, academic_year, semester),
            ).fetchone()[0]
            if count >= MAX_COURSES_PER_SEMESTER:
                return (
                    False,
                    f"Limit reached: max {MAX_COURSES_PER_SEMESTER} courses per semester.",
                    None,
                )

            enrolled_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                """INSERT INTO enrollments
                   (student_id, course_id, academic_year, semester, enrolled_on)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, course_id, academic_year, semester, enrolled_on),
            )
            conn.commit()
            return True, "Enrollment successful.", cur.lastrowid
    except sqlite3.IntegrityError:
        return False, "Duplicate enrollment (database constraint).", None
    except sqlite3.Error as e:
        return False, f"Database error: {e}", None


def get_all_enrollments():
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT e.id,
                      e.student_id,
                      s.name || ' ' || s.surname AS student_name,
                      e.course_id,
                      c.course_code,
                      c.course_name,
                      e.academic_year,
                      e.semester,
                      e.enrolled_on
               FROM enrollments e
               JOIN students s ON s.student_id = e.student_id
               JOIN courses  c ON c.course_id  = e.course_id
               ORDER BY e.enrolled_on DESC"""
        )
        return [dict(r) for r in cur.fetchall()]


def get_enrollments_for_student(student_id):
    with get_connection() as conn:
        cur = conn.execute(
            """SELECT e.id, e.course_id, c.course_code, c.course_name,
                      c.credits, c.lecturer,
                      e.academic_year, e.semester, e.enrolled_on
               FROM enrollments e
               JOIN courses c ON c.course_id = e.course_id
               WHERE e.student_id = ?
               ORDER BY e.academic_year DESC, e.semester""",
            (student_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def remove_enrollment(enrollment_id):
    if not enrollment_id:
        return False, "Enrollment ID required."
    try:
        with get_connection() as conn:
            marks = conn.execute(
                """SELECT 1 FROM marks m
                   JOIN enrollments e
                     ON e.student_id = m.student_id
                    AND e.course_id  = m.course_id
                   WHERE e.id = ?""",
                (enrollment_id,),
            ).fetchone()
            if marks:
                return False, "Cannot remove: marks have already been captured for this course."

            cur = conn.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
            if cur.rowcount == 0:
                return False, "Enrollment not found."
            conn.commit()
            return True, "Enrollment removed."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"


def get_enrollment_count(student_id, academic_year, semester):
    with get_connection() as conn:
        return conn.execute(
            """SELECT COUNT(*) FROM enrollments
               WHERE student_id = ? AND academic_year = ? AND semester = ?""",
            (student_id, academic_year, semester),
        ).fetchone()[0]