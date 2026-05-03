"""
app.py
APEX UNIVERSITY — main entry point.

Run with:    streamlit run app.py
"""

from pathlib import Path
import streamlit as st

# --- Streamlit page config MUST be the first Streamlit call ---
st.set_page_config(
    page_title="APEX UNIVERSITY",
    layout="wide",
    initial_sidebar_state="auto",   # auto = collapsed on login, expanded after
)


def load_global_styles():
    """Inject Google Fonts, Bootstrap Icons, and our stylesheet into the app."""
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
        """,
        unsafe_allow_html=True,
    )
    css_path = Path("assets/styles.css")
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def init_session():
    """Initialise session state keys we rely on across the app."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def route_to_page(page_label: str):
    """Route the sidebar selection to the right page renderer."""
    if page_label == "Dashboard":
        from views.dashboard import render_dashboard
        render_dashboard()
        return

    if page_label == "Students":
        from views.students_page import render_students_page
        render_students_page()
        return

    if page_label == "Courses":
        from views.courses_page import render as render_courses
        render_courses()
        return

    if page_label in ("Enrolment", "Enrollment"):
        from views.enrollment_page import render as render_enrollment
        render_enrollment()
        return
    if page_label == "Fees":
        from views.fees_page import render as render_fees
        render_fees()
        return
    if page_label == "Marks":
        from views.marks_page import render as render_marks
        render_marks()
        return
    if page_label == "Risk Detection":
        from views.risk_page import render as render_risk
        render_risk()
        return
    if page_label == "Reports":
        from views.reports_page import render as render_reports
        render_reports()
        return
    if page_label == "Warning Letters":
        from views.warnings_page import render as render_warnings
        render_warnings()
        return
    if page_label == "Backup & Restore":
        from views.backup_page import render as render_backup
        render_backup()
        return
    # Placeholder for pages not yet built
    st.markdown(
        f"""
        <div class="content-card">
            <h3 class="content-card-title">
                <i class="bi bi-tools"></i> {page_label}
            </h3>
            <p style="color:#8A8AA8; margin:0; font-size:0.92rem;">
                This module is being built. It will be available shortly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    init_session()
    load_global_styles()

    if not st.session_state.authenticated:
        # Show the login screen
        from views.login import render_login
        render_login()
    else:
        # Authenticated: draw the shell, then route to the selected page
        from views.shell import render_shell
        page = render_shell()
        route_to_page(page)


if __name__ == "__main__":
    main()