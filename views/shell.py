"""
views/shell.py
The persistent dashboard shell — sidebar + top header — wrapped around every authenticated page.

Usage from any page:
    from views.shell import render_shell
    page_title = render_shell()      # draws sidebar + header
    if page_title == "Dashboard":
        render_dashboard()
    elif page_title == "Students":
        render_students()
    ...
"""

import streamlit as st


# ---------------------------------------------------------------
# Navigation menu definitions, keyed by role.
# Each item: (label shown in sidebar, Bootstrap Icon class)
# Order in this list = order they appear in the sidebar.
# ---------------------------------------------------------------
MENU_BY_ROLE = {
    "Administrator": [
        ("Dashboard",        "bi-grid-1x2-fill"),
        ("Students",         "bi-people-fill"),
        ("Courses",          "bi-book-fill"),
        ("Enrolment",        "bi-pencil-square"),
        ("Marks",            "bi-clipboard-data-fill"),
        ("Fees",             "bi-cash-coin"),
        ("Risk Detection",   "bi-exclamation-triangle-fill"),
        ("Reports",          "bi-file-earmark-text-fill"),
        ("Warning Letters",  "bi-envelope-exclamation-fill"),
        ("Backup & Restore", "bi-cloud-arrow-up-fill"),
    ],
    "Finance Officer": [
        ("Dashboard",        "bi-grid-1x2-fill"),
        ("Students",         "bi-people-fill"),
        ("Fees",             "bi-cash-coin"),
        ("Reports",          "bi-file-earmark-text-fill"),
    ],
    "Lecturer": [
        ("Dashboard",        "bi-grid-1x2-fill"),
        ("Courses",          "bi-book-fill"),
        ("Marks",            "bi-clipboard-data-fill"),
        ("Risk Detection",   "bi-exclamation-triangle-fill"),
        ("Reports",          "bi-file-earmark-text-fill"),
        ("Warning Letters",  "bi-envelope-exclamation-fill"),
    ],
    "Student": [
        ("Dashboard",        "bi-grid-1x2-fill"),
        ("Enrolment",        "bi-pencil-square"),
        ("Marks",            "bi-clipboard-data-fill"),
        ("Fees",             "bi-cash-coin"),
    ],
}


# Subtitle shown under each page's title in the top header
PAGE_SUBTITLES = {
    "Dashboard":        "System overview at a glance",
    "Students":         "Manage student records and registrations",
    "Courses":          "Course catalogue and management",
    "Enrolment":        "Course enrolment and registration",
    "Marks":            "Capture and manage student marks",
    "Fees":             "Fee accounts, payments, and receipts",
    "Risk Detection":   "Identify academically at-risk students",
    "Reports":          "Generate academic and financial reports",
    "Warning Letters":  "Issue and track warning letters",
    "Backup & Restore": "Export and import system data",
}


def _initials(full_name: str) -> str:
    """Return up to two uppercase initials from a name string."""
    parts = (full_name or "").strip().split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _render_sidebar(user: dict) -> str:
    """
    Draw the sidebar and return the currently selected page label.
    The selected page is stored in st.session_state.current_page.
    """
    menu = MENU_BY_ROLE.get(user["role"], [("Dashboard", "bi-grid-1x2-fill")])

    # Default landing page on first login
    if "current_page" not in st.session_state:
        st.session_state.current_page = menu[0][0]

    # Safety: if role changes (rare), make sure current_page is still valid
    valid_labels = [m[0] for m in menu]
    if st.session_state.current_page not in valid_labels:
        st.session_state.current_page = valid_labels[0]

    with st.sidebar:
        # --- Brand block (logo at the top) ---
        st.markdown(
            """
            <div class="sidebar-brand">
                <h1 class="sidebar-brand-title">APEX</h1>
                <div class="sidebar-brand-tagline">University ERP</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- User card with initials avatar ---
        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-avatar">{_initials(user['name'])}</div>
                <div class="user-info">
                    <div class="user-name">{user['name']}</div>
                    <div class="user-role">{user['role']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- Section label ---
        st.markdown(
            '<div class="nav-section-label">Navigation</div>',
            unsafe_allow_html=True,
        )

        # --- Navigation buttons ---
        # We render each menu item as a Streamlit button, styled in CSS to look like a nav link.
        # The active item uses type="primary" which our CSS picks up via [kind="primary"].
        for label, icon in menu:
            is_active = (label == st.session_state.current_page)
            # The icon HTML goes inside the label using Streamlit's markdown support in buttons (set via :material:/HTML).
            # Streamlit doesn't render HTML in button labels, so we keep the icon out of the button itself
            # and rely on CSS spacing. (Cleaner than fighting Streamlit on this.)
            btn_label = f"   {label}"
            if st.button(
                btn_label,
                key=f"nav_{label}",
                type=("primary" if is_active else "secondary"),
                use_container_width=True,
            ):
                st.session_state.current_page = label
                st.rerun()

        # --- Logout at the bottom ---
        st.markdown('<div class="sidebar-logout-wrap">', unsafe_allow_html=True)
        if st.button("Sign out", key="nav_logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.pop("current_page", None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.current_page


def _render_header(page_title: str, user: dict):
    """Draw the top header strip with page title and role badge."""
    subtitle = PAGE_SUBTITLES.get(page_title, "")
    st.markdown(
        f"""
        <div class="top-header">
            <div class="top-header-left">
                <h1>{page_title}</h1>
                <p>{subtitle}</p>
            </div>
            <div class="top-header-right">
                <span class="role-badge">
                    <i class="bi bi-shield-check"></i> {user['role']}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_shell() -> str:
    """
    Public entry point. Renders sidebar + header, returns the current page label
    so the caller (app.py) can route to the right page renderer.
    """
    user = st.session_state.user
    page_title = _render_sidebar(user)
    _render_header(page_title, user)
    return page_title