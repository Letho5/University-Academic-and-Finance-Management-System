"""
Q4 — Marks Management
Capture and update marks; auto-calculate final mark & grade.

Weighting:
  Assignment 1 = 20%
  Assignment 2 = 20%
  Exam         = 60%

Grade scale:
  >= 75   Distinction
  >= 50   Pass
  >= 40   Supplementary
  <  40   Fail
"""
import sqlite3
from datetime import datetime
from database import get_connection
from config import PASS_MARK, DISTINCTION_MARK, SUPPLEMENTARY_MIN


def calculate_final_mark(a1, a2, exam):
    """Weighted final: 20% + 20% + 60%."""
    return round((a1 * 0.20) + (a2 * 0.20) + (exam * 0.60), 2)


def calculate_grade(final_mark):
    if final_mark >= DISTINCTION_MARK:
        return "Distinction"
    if final_mark >= PASS_MARK:
        return "Pass"
    if final_mark >= SUPPLEMENTARY_MIN:
        return "Supplementary"
    return "Fail"


def _validate_mark(name, value):
    try:
        v = float(value)
    except (ValueError, TypeError):
        return False, f"{name} must be a number.", None
    if v < 0 or v > 100:
        return False, f"{name} must be between 0 and 100.", None
    return True, "", v


def capture_marks(student_id, course_id, assignment1, assignment2, exam):
    """Insert or update marks for a (student, course) pair."""
    if not student_id or not course_id:
        return False, "Student and course are required.", None

    for label, val in (
        ("Assignment 1", assignment1),
        ("Assignment 2", assignment2),
        ("Exam", exam),
    ):
        ok, msg, _ = _validate_mark(label, val)
        if not ok:
            return False, msg, None

    a1 = float(assignment1)
    a2 = float(assignment2)
    ex = float(exam)
    final_mark = calculate_final_mark(a1, a2, ex)
    grade = calculate_grade(final_mark)
    captured_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_connection() as conn:
            # Verify student & course exist
            if not conn.execute(
                "SELECT 1 FROM students WHERE student_id = ?", (student_id,)
            ).fetchone():
                return False, f"Student {student_id} not found.", None
            if not conn.execute(
                "SELECT 1 FROM courses WHERE course_id = ?", (course_id,)
            ).fetchone():
                return False, f"Course {course_id} not found.", None

            # Verify enrollment exists (must be enrolled to receive marks)
            if not conn.execute(
                """SELECT 1 FROM enrollments
                   WHERE student_id = ? AND course_id = ?""",
                (student_id, course_id),
            ).fetchone():
                return False, "Student is not enrolled in this course.", None

            # Upsert: update if exists, else insert
            existing = conn.execute(
                "SELECT id FROM marks WHERE student_id = ? AND course_id = ?",
                (student_id, course_id),
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE marks
                       SET assignment1 = ?, assignment2 = ?, exam = ?,
                           final_mark = ?, grade = ?, captured_on = ?
                       WHERE id = ?""",
                    (a1, a2, ex, final_mark, grade, captured_on, existing["id"]),
                )
                action = "updated"
            else:
                conn.execute(
                    """INSERT INTO marks
                       (student_id, course_id, assignment1, assignment2,
                        exam, final_mark, grade, captured_on)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (student_id, course_id, a1, a2, ex, final_mark, grade, captured_on),
                )
                action = "captured"

            conn.commit()
            return True, (
                f"Marks {action} successfully. "
                f"Final: {final_mark}% — {grade}."
            ), {"final_mark": final_mark, "grade": grade}
    except sqlite3.Error as e:
        return False, f"Database error: {e}", None


def get_all_marks():
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT m.id, m.student_id,
                   s.name || ' ' || s.surname AS student_name,
                   m.course_id, c.course_code, c.course_name,
                   m.assignment1, m.assignment2, m.exam,
                   m.final_mark, m.grade, m.captured_on
            FROM marks m
            JOIN students s ON s.student_id = m.student_id
            JOIN courses  c ON c.course_id  = m.course_id
            ORDER BY m.captured_on DESC
        """)
        return [dict(r) for r in cur.fetchall()]


def get_marks_for_student(student_id):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT m.id, m.course_id, c.course_code, c.course_name,
                   c.credits,
                   m.assignment1, m.assignment2, m.exam,
                   m.final_mark, m.grade, m.captured_on
            FROM marks m
            JOIN courses c ON c.course_id = m.course_id
            WHERE m.student_id = ?
            ORDER BY m.captured_on DESC
        """, (student_id,))
        return [dict(r) for r in cur.fetchall()]


def get_marks_for_course(course_id):
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT m.id, m.student_id,
                   s.name || ' ' || s.surname AS student_name,
                   m.assignment1, m.assignment2, m.exam,
                   m.final_mark, m.grade, m.captured_on
            FROM marks m
            JOIN students s ON s.student_id = m.student_id
            WHERE m.course_id = ?
            ORDER BY m.final_mark DESC
        """, (course_id,))
        return [dict(r) for r in cur.fetchall()]


def get_existing_marks(student_id, course_id):
    """Used by UI to pre-fill form when updating."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT assignment1, assignment2, exam, final_mark, grade
               FROM marks WHERE student_id = ? AND course_id = ?""",
            (student_id, course_id),
        ).fetchone()
        return dict(row) if row else None


def delete_marks(mark_id):
    if not mark_id:
        return False, "Mark ID required."
    try:
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM marks WHERE id = ?", (mark_id,))
            if cur.rowcount == 0:
                return False, "Mark record not found."
            conn.commit()
            return True, "Mark record deleted."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"