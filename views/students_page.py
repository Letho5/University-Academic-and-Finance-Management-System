"""
views/students_page.py
Q1: Student Registration Module — UI.
"""

import streamlit as st
import pandas as pd
from modules.students import (
    register_student, get_all_students, delete_student
)


def render_students_page():
    tab_register, tab_list = st.tabs(["Register New Student", "All Students"])

    with tab_register:
        _render_register_form()

    with tab_list:
        _render_student_list()


def _render_register_form():
    st.markdown(
        """
        <div class="content-card">
            <h3 class="content-card-title">
                <i class="bi bi-person-plus-fill"></i> New Student Registration
            </h3>
        """,
        unsafe_allow_html=True,
    )

    with st.form("student_register_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("First name *")
            email = st.text_input("Email address *", placeholder="student@apex.ac.za")
            dob = st.text_input("Date of birth *", placeholder="DD/MM/YYYY")
            gender = st.selectbox(
                "Gender",
                ["", "Male", "Female", "Other", "Prefer not to say"]
            )
            password = st.text_input("Password *", type="password",
                                     help="8+ chars, 1 uppercase, 1 number")
        with c2:
            surname = st.text_input("Surname *")
            phone = st.text_input("Phone")
            qualification = st.text_input("Qualification",
                                          placeholder="e.g. BSc Computer Science")
            year = st.selectbox("Year of study", [1, 2, 3, 4])
            password2 = st.text_input("Confirm password *", type="password")

        submitted = st.form_submit_button("Register Student",
                                          use_container_width=True)
        if submitted:
            ok, msg, sid = register_student(
                name, surname, dob, gender, email, phone,
                qualification, year, password, password2
            )
            if ok:
                st.success(f"{msg}")
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_student_list():
    students = get_all_students()

    st.markdown(
        f"""
        <div class="content-card">
            <h3 class="content-card-title">
                <i class="bi bi-people-fill"></i> Registered Students
                <span style="margin-left:auto; font-size:0.78rem;
                             color:#8A8AA8; font-weight:500;">
                    {len(students)} total
                </span>
            </h3>
        """,
        unsafe_allow_html=True,
    )

    if not students:
        st.markdown(
            """<p style="color:#8A8AA8; text-align:center; padding:30px 0; margin:0;">
                No students registered yet.
            </p></div>""",
            unsafe_allow_html=True,
        )
        return

    # Search
    query = st.text_input("Search by ID, name, surname, or email",
                          placeholder="Type to filter...",
                          label_visibility="collapsed").strip().lower()

    if query:
        students = [s for s in students if (
            query in (s["student_id"] or "").lower() or
            query in (s["name"] or "").lower() or
            query in (s["surname"] or "").lower() or
            query in (s["email"] or "").lower()
        )]

    # Display table
    df = pd.DataFrame(students)
    df = df[["student_id", "name", "surname", "email", "phone",
             "qualification", "year_of_study"]]
    df.columns = ["ID", "First Name", "Surname", "Email", "Phone",
                  "Qualification", "Year"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Delete control
    st.markdown(
        """
        <div class="content-card">
            <h3 class="content-card-title">
                <i class="bi bi-trash3"></i> Delete Student
            </h3>
        """,
        unsafe_allow_html=True,
    )

    sid_options = [s["student_id"] for s in students]
    if sid_options:
        sid_to_delete = st.selectbox("Select student to delete", sid_options)
        if st.button("Delete student", type="primary"):
            ok, msg = delete_student(sid_to_delete)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)