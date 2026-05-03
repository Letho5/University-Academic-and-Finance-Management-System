"""
views/login.py
Renders the login screen for APEX UNIVERSITY.
"""

import streamlit as st
from modules.auth import authenticate


def render_login():
    """Draw the login screen. Sets st.session_state on successful login."""

    # Three-column trick: empty | form | empty  →  centers the card horizontally
    left, center, right = st.columns([1, 1.2, 1])

    with center:
        # Brand wordmark and welcome copy (HTML so the gradient text effect works)
        st.markdown(
            """
            <h1 class="brand-title">APEX</h1>
            <p class="brand-tagline">University &middot; Excellence Defined</p>
            <h2 class="login-heading">Welcome back</h2>
            <p class="login-sub">Sign in to continue to your dashboard</p>
            """,
            unsafe_allow_html=True,
        )

        # The Streamlit form is styled in styles.css to look like a white card
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email address",
                placeholder="you@apex.ac.za",
                key="login_email",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                ok, user, msg = authenticate(email, password)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()  # immediately re-route to the dashboard placeholder
                else:
                    st.error(msg)

        # Demo credentials panel — helps during the demo, removed for production
        st.markdown(
            """
            <div class="demo-box">
                <p class="demo-title">Demo Accounts</p>
                <div class="demo-grid">
                    <div><strong>Administrator</strong>
                        <span>admin@apex.ac.za / admin123</span></div>
                    <div><strong>Finance Officer</strong>
                        <span>finance@apex.ac.za / finance123</span></div>
                    <div><strong>Lecturer</strong>
                        <span>lecturer@apex.ac.za / lecturer123</span></div>
                    <div><strong>Student</strong>
                        <span>student@apex.ac.za / student123</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )