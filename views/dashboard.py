"""
views/dashboard.py
The home page — live KPIs, payments chart, recent activity.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from modules.analytics import (
    get_dashboard_kpis,
    get_payments_timeseries,
    get_recent_payments,
)
from config import format_currency


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _kpi_card(label: str, value: str, sub: str, icon: str, colour: str) -> str:
    """Returns the HTML for one glassmorphic KPI card."""
    return f"""
    <div class="kpi-card">
        <div class="kpi-card-header">
            <p class="kpi-label">{label}</p>
            <div class="kpi-icon {colour}">
                <i class="bi {icon}"></i>
            </div>
        </div>
        <p class="kpi-value">{value}</p>
        <p class="kpi-sub">{sub}</p>
    </div>
    """


def _render_kpi_row():
    """Top row: 4 KPI cards pulling live data from the database."""
    kpis = get_dashboard_kpis()

    cards = [
        ("Students",    f"{kpis['students']:,}",          "Registered in system",  "bi-people-fill",  "purple"),
        ("Courses",     f"{kpis['courses']:,}",           "In course catalogue",   "bi-book-fill",    "pink"),
        ("Revenue",     format_currency(kpis['revenue']), "Total collected",       "bi-cash-coin",    "teal"),
        ("Outstanding", format_currency(kpis['outstanding']), "Total still owed",  "bi-wallet2",      "amber"),
    ]

    cols = st.columns(4, gap="medium")
    for col, card_args in zip(cols, cards):
        with col:
            st.markdown(_kpi_card(*card_args), unsafe_allow_html=True)


def _render_payments_chart():
    """Smooth area chart of daily payments over the last 30 days."""
    series = get_payments_timeseries(days=30)
    df = pd.DataFrame(series)
    df["date"] = pd.to_datetime(df["date"])
    has_data = df["total"].sum() > 0

    # Card title (its own card block)
    st.markdown(
        """
        <div class="content-card">
            <h3 class="content-card-title">
                <i class="bi bi-graph-up-arrow"></i> Payments — Last 30 Days
            </h3>
        """,
        unsafe_allow_html=True,
    )

    if not has_data:
        st.markdown(
            """
            <p style="color:#8A8AA8; text-align:center; padding: 30px 0; margin: 0;">
                No payment data in the system yet. Once payments are recorded,
                the trend will appear here.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Build the Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["total"],
        mode="lines",
        line=dict(color="#6A3DE8", width=3, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(139, 95, 191, 0.18)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>R %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            color="#8A8AA8",
            showline=False,
            tickformat="%d %b",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(139, 95, 191, 0.10)",
            color="#8A8AA8",
            tickprefix="R ",
        ),
        hoverlabel=dict(bgcolor="white", bordercolor="#6A3DE8", font_size=12),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Close the card
    st.markdown("</div>", unsafe_allow_html=True)


def _render_recent_activity():
    """Right-hand panel: last 5 payments with student names and amounts."""
    payments = get_recent_payments(limit=5)

    # Open card
    st.markdown(
        """
        <div class="content-card">
            <h3 class="content-card-title">
                <i class="bi bi-clock-history"></i> Recent Payments
            </h3>
        """,
        unsafe_allow_html=True,
    )

    if not payments:
        st.markdown(
            """
            <p style="color:#8A8AA8; text-align:center; padding: 30px 0; margin: 0;">
                No recent payments.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Build the activity rows
    rows_html = ""
    for p in payments:
        date_short = (p["date"] or "")[:10]
        rows_html += f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding: 11px 0; border-bottom: 1px solid rgba(139,95,191,0.08);">
            <div style="min-width:0; flex: 1;">
                <div style="font-weight:600; color:#2D2D44; font-size:0.9rem;
                            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {p['student_name']}
                </div>
                <div style="font-size:0.74rem; color:#8A8AA8; margin-top: 2px;">
                    {p['student_id']} &middot; {p['method']} &middot; {date_short}
                </div>
            </div>
            <div style="font-weight:700; color:#6A3DE8; font-size:0.92rem; padding-left: 8px;">
                {format_currency(p['amount'])}
            </div>
        </div>
        """

    st.markdown(rows_html + "</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------

def render_dashboard():
    user = st.session_state.user
    first_name = (user.get("name") or "there").split()[0]

    # Compact welcome strip
    st.markdown(
        f"""
        <div class="content-card" style="padding: 16px 22px; margin-bottom: 18px;">
            <h2 style="margin:0; font-size:1.1rem; color:#2D2D44; font-weight:600;">
                <i class="bi bi-stars" style="color:#6A3DE8;"></i> Welcome back, {first_name}
            </h2>
            <p style="color:#8A8AA8; margin: 4px 0 0 0; font-size:0.86rem;">
                Signed in as <strong>{user['role']}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPI row (4 cards)
    _render_kpi_row()

    # Spacer
    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

    # Chart (2/3 width) + recent activity (1/3 width)
    chart_col, activity_col = st.columns([2, 1], gap="medium")
    with chart_col:
        _render_payments_chart()
    with activity_col:
        _render_recent_activity()