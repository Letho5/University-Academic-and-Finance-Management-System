"""
Q6 — Academic Risk Detection page
Tabs: Risk Overview | Student Profile
"""
import streamlit as st
import pandas as pd

from modules.risk import (
    get_all_risk_profiles,
    get_student_risk,
    get_risk_summary,
)
from modules.students import get_all_students
from config import format_currency


def _risk_pill_class(level):
    return {
        "HIGH": "unpaid",
        "MEDIUM": "partial",
        "LOW": "partial",
        "NONE": "settled",
    }.get(level, "partial")


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-shield-exclamation"></i> Academic Risk Detection'
        '</h2>',
        unsafe_allow_html=True,
    )

    _render_summary_strip()

    tab_overview, tab_profile = st.tabs([
        "  Risk Overview  ",
        "  Student Profile  ",
    ])

    with tab_overview:
        _render_overview()
    with tab_profile:
        _render_profile()


# ------------------------------------------------------------------ #
def _render_summary_strip():
    s = get_risk_summary()
    st.markdown(
        f"""
        <div class="content-card" style="margin-bottom:1rem;">
            <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
                <div style="flex:1; min-width:160px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Total Students</p>
                    <p style="color:#2D2D44; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{s['total']}</p>
                </div>
                <div style="flex:1; min-width:160px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">High Risk</p>
                    <p style="color:#FF6B9D; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{s['high']}</p>
                </div>
                <div style="flex:1; min-width:160px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Medium Risk</p>
                    <p style="color:#FF8FB1; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{s['medium']}</p>
                </div>
                <div style="flex:1; min-width:160px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Low Risk</p>
                    <p style="color:#8B5FBF; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{s['low']}</p>
                </div>
                <div style="flex:1; min-width:160px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Good Standing</p>
                    <p style="color:#6A3DE8; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{s['none']}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ #
def _render_overview():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-list-check"></i> Risk Register'
        '</h3>',
        unsafe_allow_html=True,
    )

    profiles = get_all_risk_profiles()
    if not profiles:
        st.info("No students yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    levels = st.multiselect(
        "Filter by risk level",
        ["HIGH", "MEDIUM", "LOW", "NONE"],
        default=["HIGH", "MEDIUM"],
    )

    filtered = [p for p in profiles if p["risk_level"] in levels] if levels else profiles

    if not filtered:
        st.info("No students match the selected filters.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(filtered)
    df["full_name"] = df["name"] + " " + df["surname"]
    df["average_disp"] = df["average"].apply(
        lambda v: f"{v:.1f}%" if v is not None else "—"
    )
    df["balance_disp"] = df["balance"].apply(format_currency)
    df["reasons_disp"] = df["reasons"].apply(lambda r: " · ".join(r))

    df_display = df[[
        "student_id", "full_name", "qualification", "year_of_study",
        "courses_assessed", "average_disp", "fails", "supplementary",
        "balance_disp", "risk_level", "reasons_disp",
    ]]
    df_display.columns = [
        "Student ID", "Name", "Qualification", "Year",
        "Assessed", "Average", "Fails", "Supp.",
        "Balance", "Risk", "Reasons",
    ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Showing <strong style='color:#6A3DE8;'>{len(filtered)}</strong> of {len(profiles)} students."
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_profile():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-person-badge"></i> Individual Risk Profile'
        '</h3>',
        unsafe_allow_html=True,
    )

    students = get_all_students()
    if not students:
        st.info("No students yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    student_opts = {
        f"{s['student_id']} — {s['name']} {s['surname']}": s["student_id"]
        for s in students
    }
    label = st.selectbox("Select student", list(student_opts.keys()))
    profile = get_student_risk(student_opts[label])

    if not profile:
        st.error("Profile not available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    pill_cls = _risk_pill_class(profile["risk_level"])
    avg_disp = f"{profile['average']:.1f}%" if profile["average"] is not None else "—"

    st.markdown(
        f"""
        <div style="margin-top:0.5rem; padding:1.25rem;
                    background:rgba(255,255,255,0.6); border-radius:18px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
                <div>
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Student</p>
                    <p style="color:#2D2D44; font-size:1.3rem; font-weight:600; margin:0.15rem 0 0 0;">
                        {profile['name']} {profile['surname']}
                    </p>
                    <p style="color:#8A8AA8; font-size:0.85rem; margin:0;">
                        {profile['student_id']} · {profile['qualification'] or '—'} · Year {profile['year_of_study'] or '—'}
                    </p>
                </div>
                <span class="status-pill {pill_cls}" style="font-size:0.95rem; padding:0.4rem 1rem;">
                    {profile['risk_level']} RISK
                </span>
            </div>
        </div>

        <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:1rem;">
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Average</p>
                <p style="color:#6A3DE8; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{avg_disp}</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Courses Assessed</p>
                <p style="color:#2D2D44; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{profile['courses_assessed']}</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Fails</p>
                <p style="color:#FF6B9D; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{profile['fails']}</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Supplementary</p>
                <p style="color:#FF8FB1; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{profile['supplementary']}</p>
            </div>
            <div style="flex:1; min-width:140px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Balance</p>
                <p style="color:#FF6B9D; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(profile['balance'])}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Reasons list
    reasons_html = "".join(
        f"<li style='margin-bottom:0.4rem;'>{r}</li>" for r in profile["reasons"]
    )
    st.markdown(
        f"""
        <div style="margin-top:1rem; padding:1rem 1.25rem;
                    background:rgba(255,255,255,0.55); border-radius:14px;">
            <p style="color:#8A8AA8; font-size:0.78rem; margin:0 0 0.5rem 0; text-transform:uppercase; letter-spacing:0.05em;">
                Risk Indicators
            </p>
            <ul style="color:#2D2D44; margin:0; padding-left:1.2rem;">
                {reasons_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)