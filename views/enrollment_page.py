"""
Q3 — Student Enrollment page
Tabs: Enroll Student | Enrollments Register
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.enrollment import (
    enroll_student,
    get_all_enrollments,
    get_enrollments_for_student,
    remove_enrollment,
    get_enrollment_count,
)
from modules.students import get_all_students
from modules.courses import get_all_courses
from config import MAX_COURSES_PER_SEMESTER


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-person-check-fill"></i> Student Enrollment'
        '</h2>',
        unsafe_allow_html=True,
    )

    tab_enroll, tab_list = st.tabs(
        ["  Enroll Student  ", "  Enrollments Register  "]
    )

    with tab_enroll:
        _render_enroll_form()

    with tab_list:
        _render_register()


# ------------------------------------------------------------------ #
def _render_enroll_form():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-plus-square"></i> New Enrollment'
        '</h3>',
        unsafe_allow_html=True,
    )

    students = get_all_students()
    courses = get_all_courses()

    if not students:
        st.warning("No students registered yet. Add a student first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    if not courses:
        st.warning("No courses available yet. Add a course first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    student_opts = {
        f"{s['student_id']} — {s['name']} {s['surname']}": s["student_id"]
        for s in students
    }
    course_opts = {
        f"{c['course_id']} — {c['course_code']} · {c['course_name']}": c["course_id"]
        for c in courses
    }

    current_year = datetime.now().year
    year_choices = [str(y) for y in range(current_year - 1, current_year + 2)]

    with st.form("enroll_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            student_label = st.selectbox("Student *", list(student_opts.keys()))
            academic_year = st.selectbox(
                "Academic Year *", year_choices, index=1
            )
        with c2:
            course_label = st.selectbox("Course *", list(course_opts.keys()))
            semester = st.selectbox(
                "Semester *", ["Semester 1", "Semester 2", "Year-long"]
            )

        # Live capacity preview
        current_count = get_enrollment_count(
            student_opts[student_label], academic_year, semester
        )
        st.markdown(
            f"<p style='color:#8A8AA8; font-size:0.88rem; margin:0.25rem 0 0.75rem 0;'>"
            f"Current load for this student / semester: "
            f"<strong style='color:#6A3DE8;'>{current_count}</strong> / "
            f"{MAX_COURSES_PER_SEMESTER} courses"
            f"</p>",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "Enroll Student", use_container_width=True
        )
        if submitted:
            ok, msg, _ = enroll_student(
                student_opts[student_label],
                course_opts[course_label],
                academic_year,
                semester,
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_register():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-list-columns-reverse"></i> Enrollments Register'
        '</h3>',
        unsafe_allow_html=True,
    )

    students = get_all_students()
    if not students:
        st.info("No students yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    filter_opts = {"All students": None}
    filter_opts.update(
        {
            f"{s['student_id']} — {s['name']} {s['surname']}": s["student_id"]
            for s in students
        }
    )
    label = st.selectbox("Filter by student", list(filter_opts.keys()))
    student_id = filter_opts[label]

    rows = (
        get_enrollments_for_student(student_id)
        if student_id
        else get_all_enrollments()
    )

    if not rows:
        st.info("No enrollments to display.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)

    if student_id:
        df_display = df[
            [
                "course_id", "course_code", "course_name",
                "credits", "lecturer", "academic_year",
                "semester", "enrolled_on",
            ]
        ].copy()
        df_display.columns = [
            "Course ID", "Code", "Course Name", "Credits",
            "Lecturer", "Year", "Semester", "Enrolled On",
        ]
    else:
        df_display = df[
            [
                "id", "student_id", "student_name",
                "course_code", "course_name",
                "academic_year", "semester", "enrolled_on",
            ]
        ].copy()
        df_display.columns = [
            "#", "Student ID", "Student", "Code",
            "Course Name", "Year", "Semester", "Enrolled On",
        ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Total enrollments: <strong style='color:#6A3DE8;'>{len(rows)}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Remove section ----
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-x-octagon"></i> Remove Enrollment'
        '</h3>',
        unsafe_allow_html=True,
    )

    all_rows = get_all_enrollments()
    if not all_rows:
        st.info("Nothing to remove.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    options = {
        f"#{r['id']} · {r['student_id']} — {r['course_code']} "
        f"({r['semester']} {r['academic_year']})": r["id"]
        for r in all_rows
    }
    sel = st.selectbox(
        "Select enrollment to remove",
        list(options.keys()),
        key="enr_del_select",
    )
    confirm = st.checkbox(
        "I understand this action cannot be undone",
        key="enr_del_confirm",
    )

    if st.button(
        "Remove Enrollment",
        disabled=not confirm,
        key="enr_del_btn",
    ):
        ok, msg = remove_enrollment(options[sel])
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)