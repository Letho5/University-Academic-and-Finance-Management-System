"""
APEX UNIVERSITY - Shared Database Layer
=========================================
This file is the FOUNDATION of the entire system.
Every module (Q1 through Q9) uses these tables.

Used by: Everyone

DO NOT modify table structures without team approval.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

# ---------------------------------------------------------
# DATABASE FILE LOCATION
# ---------------------------------------------------------
# The database lives inside the 'data' folder.
# This folder is auto-created if missing.
# ---------------------------------------------------------
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "apex.db"


# ---------------------------------------------------------
# CONNECTION HELPER
# ---------------------------------------------------------
# Every module uses this to open the database safely.
# It auto-commits on success and rolls back on errors.
#
# USAGE EXAMPLE (in any module):
#
#     from database import get_connection
#
#     with get_connection() as conn:
#         conn.execute("INSERT INTO students ...")
#
# ---------------------------------------------------------
@contextmanager
def get_connection():
    """Safe context-managed database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row          # Lets us access columns by name
    conn.execute("PRAGMA foreign_keys = ON") # Enforces table relationships
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
# Creates all tables if they don't exist yet.
# Safe to call every time the app starts.
# ---------------------------------------------------------
def init_database():
    """Create all tables on first run."""
    with get_connection() as conn:
        cur = conn.cursor()

        # =====================================================
        # STUDENTS TABLE  (used by Q1: Student Registration)
        # =====================================================
        # Stores all registered students.
        # student_id is the unique identifier used everywhere.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id      TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                surname         TEXT NOT NULL,
                date_of_birth   TEXT,
                gender          TEXT,
                email           TEXT UNIQUE NOT NULL,
                phone           TEXT,
                password        TEXT NOT NULL,
                qualification   TEXT,
                year_of_study   INTEGER DEFAULT 1,
                registered_on   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # COURSES TABLE  (used by Q2: Course Management)
        # =====================================================
        # Stores all courses offered.
        # course_id is auto-generated; course_code is for display.
        # 'fee' column is REQUIRED — used by the fee module.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id       TEXT PRIMARY KEY,
                course_name     TEXT NOT NULL,
                course_code     TEXT UNIQUE NOT NULL,
                duration        TEXT,
                credits         INTEGER DEFAULT 12,
                semester        TEXT DEFAULT 'S1',
                fee             REAL DEFAULT 1850.00,
                lecturer        TEXT
            )
        """)

        # =====================================================
        # ENROLLMENTS TABLE  (used by Q3: Enrollment)
        # =====================================================
        # Links students to courses they registered for.
        # UNIQUE constraint prevents duplicate enrollments.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      TEXT NOT NULL,
                course_id       TEXT NOT NULL,
                academic_year   INTEGER NOT NULL,
                semester        TEXT NOT NULL,
                enrolled_on     TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id, academic_year, semester),
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE
            )
        """)

        # =====================================================
        # MARKS TABLE  (used by Q4: Marks Management, Q6: Risk)
        # =====================================================
        # Stores marks for each student per course.
        # Q6 (Risk Detection) reads from this table.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      TEXT NOT NULL,
                course_id       TEXT NOT NULL,
                assignment1     REAL DEFAULT 0,
                assignment2     REAL DEFAULT 0,
                exam            REAL DEFAULT 0,
                final_mark      REAL DEFAULT 0,
                grade           TEXT,
                captured_on     TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE
            )
        """)

        # =====================================================
        # FEE_ACCOUNTS TABLE  (used by Q5: Fees - YOUR module)
        # =====================================================
        # One row per student. Tracks total billed, paid, balance.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fee_accounts (
                student_id              TEXT PRIMARY KEY,
                total_billed            REAL DEFAULT 0,
                total_paid              REAL DEFAULT 0,
                balance                 REAL DEFAULT 0,
                last_payment_date       TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            )
        """)

        # =====================================================
        # PAYMENTS TABLE  (used by Q5: Fees - YOUR module)
        # =====================================================
        # Records every individual payment as a transaction.
        # Never deleted — provides full audit history.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number  TEXT UNIQUE NOT NULL,
                student_id      TEXT NOT NULL,
                amount          REAL NOT NULL,
                payment_method  TEXT,
                reference       TEXT,
                payment_date    TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            )
        """)

        # =====================================================
        # WARNING_LETTERS TABLE  (used by Q8: Warning Letters)
        # =====================================================
        # Logs every warning letter issued to at-risk students.
        # =====================================================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warning_letters (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      TEXT NOT NULL,
                reason          TEXT,
                file_path       TEXT,
                issued_on       TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            )
        """)


# ---------------------------------------------------------
# ID GENERATORS
# ---------------------------------------------------------
# Helper functions to auto-generate sequential IDs.
# Q1 uses generate_student_id()
# Q2 uses generate_course_id()
# Q5 uses generate_receipt_number()
# ---------------------------------------------------------
def generate_student_id() -> str:
    """Returns next student ID like STU00001, STU00002..."""
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM students").fetchone()
        count = row[0] + 1
    return f"STU{count:05d}"


def generate_course_id() -> str:
    """Returns next course ID like CRS001, CRS002..."""
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM courses").fetchone()
        count = row[0] + 1
    return f"CRS{count:03d}"


def generate_receipt_number() -> str:
    """Returns next receipt number like REC-2026-00001."""
    from datetime import datetime
    year = datetime.now().year
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM payments").fetchone()
        count = row[0] + 1
    return f"REC-{year}-{count:05d}"


# ---------------------------------------------------------
# UTILITY: RESET (for testing only)
# ---------------------------------------------------------
def reset_database():
    """Wipe and recreate all tables. USE WITH CARE."""
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_database()