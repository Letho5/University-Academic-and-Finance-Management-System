"""
Q4 — Marks Management page
Tabs: Capture Marks | Marks Register | Course Performance
"""
import streamlit as st
import pandas as pd

from modules.marks import (
    capture_marks,
    get_all_marks,
    get_marks_for_student,
    get_marks_for_course,
    get_existing_marks,
    delete_marks,
    calculate_final_mark,
    calculate_grade,
)
from modules.students import get_all_students
from modules.courses import get_all_courses
from modules.enrollment import get_enrollments_for_student


def _grade_pill(grade):
    cls_map = {
        "Distinction": "settled",
        "Pass": "settled",
        "Supplementary": "partial",
        "Fail": "unpaid",
    }
    return cls_map.get(grade, "partial")


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-clipboard2-check"></i> Marks Management'
        '</h2>',
        unsafe_allow_html=True,
    )

    tab_capture, tab_register, tab_course = st.tabs([
        "  Capture Marks  ",
        "  Marks Register  ",
        "  Course Performance  ",
    ])

    with tab_capture:
        _render_capture_form()
    with tab_register:
        _render_register()
    with tab_course:
        _render_course_performance()


# ------------------------------------------------------------------ #
def _render_capture_form():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-pencil-square"></i> Capture / Update Marks'
        '</h3>',
        unsafe_allow_html=True,
    )

    students = get_all_students()
    if not students:
        st.warning("No students registered.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    student_opts = {
        f"{s['student_id']} — {s['name']} {s['surname']}": s["student_id"]
        for s in students
    }
    student_label = st.selectbox(
        "Student *", list(student_opts.keys()), key="marks_student"
    )
    student_id = student_opts[student_label]

    # Only show courses this student is actually enrolled in
    enrollments = get_enrollments_for_student(student_id)
    if not enrollments:
        st.warning("This student is not enrolled in any course. Enroll them first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    course_opts = {
        f"{e['course_id']} — {e['course_code']} · {e['course_name']}": e["course_id"]
        for e in enrollments
    }
    course_label = st.selectbox(
        "Course *", list(course_opts.keys()), key="marks_course"
    )
    course_id = course_opts[course_label]

    # Pre-fill if marks already exist
    existing = get_existing_marks(student_id, course_id)
    default_a1 = float(existing["assignment1"]) if existing else 0.0
    default_a2 = float(existing["assignment2"]) if existing else 0.0
    default_ex = float(existing["exam"]) if existing else 0.0

    if existing:
        st.info(
            f"Existing marks found — final {existing['final_mark']}% "
            f"({existing['grade']}). Submitting will update them."
        )

    with st.form("marks_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            a1 = st.number_input(
                "Assignment 1 (20%)",
                min_value=0.0, max_value=100.0,
                value=default_a1, step=1.0, format="%.2f",
            )
        with c2:
            a2 = st.number_input(
                "Assignment 2 (20%)",
                min_value=0.0, max_value=100.0,
                value=default_a2, step=1.0, format="%.2f",
            )
        with c3:
            exam = st.number_input(
                "Exam (60%)",
                min_value=0.0, max_value=100.0,
                value=default_ex, step=1.0, format="%.2f",
            )

        # Live preview
        preview_final = calculate_final_mark(a1, a2, exam)
        preview_grade = calculate_grade(preview_final)
        pill_cls = _grade_pill(preview_grade)
        st.markdown(
            f"""
            <div style="margin:0.75rem 0; padding:0.85rem 1rem;
                        background:rgba(255,255,255,0.55); border-radius:14px;
                        display:flex; gap:1.5rem; align-items:center;">
                <div>
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Preview Final</p>
                    <p style="color:#6A3DE8; font-size:1.4rem; font-weight:600; margin:0.15rem 0 0 0;">{preview_final}%</p>
                </div>
                <div>
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Grade</p>
                    <span class="status-pill {pill_cls}" style="margin-top:0.3rem; display:inline-block;">{preview_grade}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "Save Marks", use_container_width=True
        )
        if submitted:
            ok, msg, _ = capture_marks(student_id, course_id, a1, a2, exam)
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
        '<i class="bi bi-table"></i> Marks Register'
        '</h3>',
        unsafe_allow_html=True,
    )

    students = get_all_students()
    filter_opts = {"All students": None}
    filter_opts.update({
        f"{s['student_id']} — {s['name']} {s['surname']}": s["student_id"]
        for s in students
    })
    label = st.selectbox("Filter by student", list(filter_opts.keys()))
    sid = filter_opts[label]

    rows = get_marks_for_student(sid) if sid else get_all_marks()

    if not rows:
        st.info("No marks captured yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)

    if sid:
        df_display = df[[
            "course_id", "course_code", "course_name",
            "assignment1", "assignment2", "exam",
            "final_mark", "grade", "captured_on"
        ]].copy()
        df_display.columns = [
            "Course ID", "Code", "Course Name",
            "Assign 1", "Assign 2", "Exam",
            "Final %", "Grade", "Captured"
        ]
    else:
        df_display = df[[
            "student_id", "student_name",
            "course_code", "course_name",
            "assignment1", "assignment2", "exam",
            "final_mark", "grade", "captured_on"
        ]].copy()
        df_display.columns = [
            "Student ID", "Student",
            "Code", "Course Name",
            "Assign 1", "Assign 2", "Exam",
            "Final %", "Grade", "Captured"
        ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Quick stats
    if rows:
        total = len(rows)
        passed = sum(1 for r in rows if r["grade"] in ("Pass", "Distinction"))
        dist = sum(1 for r in rows if r["grade"] == "Distinction")
        supp = sum(1 for r in rows if r["grade"] == "Supplementary")
        failed = sum(1 for r in rows if r["grade"] == "Fail")
        pass_rate = (passed / total * 100) if total else 0
        st.markdown(
            f"""
            <p style='color:#8A8AA8; margin-top:0.5rem;'>
                Records: <strong style='color:#6A3DE8;'>{total}</strong> ·
                Distinctions: <strong style='color:#6A3DE8;'>{dist}</strong> ·
                Passes: <strong style='color:#2D2D44;'>{passed}</strong> ·
                Supplementary: <strong style='color:#FF8FB1;'>{supp}</strong> ·
                Fails: <strong style='color:#FF6B9D;'>{failed}</strong> ·
                Pass rate: <strong style='color:#6A3DE8;'>{pass_rate:.1f}%</strong>
            </p>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Delete section ----
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-trash3"></i> Remove Mark Record'
        '</h3>',
        unsafe_allow_html=True,
    )

    all_marks = get_all_marks()
    if not all_marks:
        st.info("Nothing to remove.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    options = {
        f"#{m['id']} · {m['student_id']} — {m['course_code']} "
        f"({m['final_mark']}% {m['grade']})": m["id"]
        for m in all_marks
    }
    sel = st.selectbox(
        "Select record to remove",
        list(options.keys()),
        key="marks_del_select",
    )
    confirm = st.checkbox(
        "I understand this action cannot be undone",
        key="marks_del_confirm",
    )
    if st.button(
        "Delete Mark Record",
        disabled=not confirm,
        key="marks_del_btn",
    ):
        ok, msg = delete_marks(options[sel])
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_course_performance():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-bar-chart-line"></i> Course Performance'
        '</h3>',
        unsafe_allow_html=True,
    )

    courses = get_all_courses()
    if not courses:
        st.info("No courses to analyse.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    course_opts = {
        f"{c['course_id']} — {c['course_code']} · {c['course_name']}": c["course_id"]
        for c in courses
    }
    label = st.selectbox("Select course", list(course_opts.keys()))
    course_id = course_opts[label]

    rows = get_marks_for_course(course_id)
    if not rows:
        st.info("No marks captured for this course yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    finals = [r["final_mark"] for r in rows]
    avg = sum(finals) / len(finals)
    highest = max(finals)
    lowest = min(finals)
    passed = sum(1 for r in rows if r["grade"] in ("Pass", "Distinction"))
    pass_rate = (passed / len(rows)) * 100

    st.markdown(
        f"""
        <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:0.5rem;">
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Students</p>
                <p style="color:#2D2D44; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{len(rows)}</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Average</p>
                <p style="color:#6A3DE8; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{avg:.1f}%</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Highest</p>
                <p style="color:#6A3DE8; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{highest:.1f}%</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Lowest</p>
                <p style="color:#FF6B9D; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{lowest:.1f}%</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Pass Rate</p>
                <p style="color:#6A3DE8; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{pass_rate:.1f}%</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(rows)[[
        "student_id", "student_name",
        "assignment1", "assignment2", "exam",
        "final_mark", "grade"
    ]]
    df.columns = ["Student ID", "Student", "Assign 1", "Assign 2", "Exam", "Final %", "Grade"]
    st.markdown("<br/>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)