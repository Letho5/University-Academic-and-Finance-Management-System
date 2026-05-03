"""
Q2 — Course Management page (Streamlit UI)
Tabs: Add Course | Course Catalogue (with search + delete).
"""
import streamlit as st
import pandas as pd

from modules.courses import (
    add_course,
    get_all_courses,
    search_courses,
    delete_course,
)
from config import DEFAULT_COURSE_FEE, format_currency


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-journal-bookmark-fill"></i> Course Management'
        '</h2>',
        unsafe_allow_html=True,
    )

    tab_add, tab_list = st.tabs(["  Add Course  ", "  Course Catalogue  "])

    with tab_add:
        _render_add_form()

    with tab_list:
        _render_catalogue()


# ------------------------------------------------------------------ #
def _render_add_form():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-plus-circle"></i> Register New Course'
        '</h3>',
        unsafe_allow_html=True,
    )

    with st.form("add_course_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            course_name = st.text_input(
                "Course Name *", placeholder="e.g. Database Systems"
            )
            course_code = st.text_input(
                "Course Code *", placeholder="e.g. COS221"
            )
            duration = st.text_input(
                "Duration *", placeholder="e.g. 1 semester / 1 year"
            )
            credits = st.number_input(
                "Credits *", min_value=1, max_value=60, value=12, step=1
            )
        with c2:
            semester = st.selectbox(
                "Semester *", ["Semester 1", "Semester 2", "Year-long"]
            )
            fee = st.number_input(
                "Course Fee (R) *",
                min_value=0.0,
                value=float(DEFAULT_COURSE_FEE),
                step=50.0,
                format="%.2f",
            )
            lecturer = st.text_input(
                "Lecturer *", placeholder="e.g. Dr. T. Nkosi"
            )

        submitted = st.form_submit_button(
            "Add Course", use_container_width=True
        )

        if submitted:
            ok, msg, course_id = add_course(
                course_name, course_code, duration,
                credits, semester, fee, lecturer,
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_catalogue():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-collection"></i> Course Catalogue'
        '</h3>',
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search",
        placeholder="Search by ID, code, name, or lecturer…",
        key="course_search",
        label_visibility="collapsed",
    )

    courses = search_courses(query) if query else get_all_courses()

    if not courses:
        st.info("No courses found. Add your first course in the 'Add Course' tab.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(courses)
    df_display = df.copy()
    df_display["fee"] = df_display["fee"].apply(format_currency)
    df_display.columns = [
        "Course ID", "Code", "Course Name", "Duration",
        "Credits", "Semester", "Fee", "Lecturer",
    ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Total courses: <strong style='color:#6A3DE8;'>{len(courses)}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Delete section ----
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-trash3"></i> Remove Course'
        '</h3>',
        unsafe_allow_html=True,
    )

    options = {
        f"{c['course_id']} — {c['course_code']} · {c['course_name']}": c["course_id"]
        for c in courses
    }
    label = st.selectbox(
        "Select course to remove",
        list(options.keys()),
        key="course_delete_select",
    )
    confirm = st.checkbox(
        "I understand this action cannot be undone",
        key="course_delete_confirm",
    )

    if st.button(
        "Delete Course",
        disabled=not confirm,
        key="course_delete_btn",
        use_container_width=False,
    ):
        ok, msg = delete_course(options[label])
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)