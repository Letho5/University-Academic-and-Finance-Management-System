"""
Q8 — Warning Letters page
Tabs: Issue Warning | Issued Letters Log
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.warnings import (
    generate_warning_letter,
    get_warning_log,
    list_generated_warnings,
)
from modules.risk import get_at_risk_students, get_student_risk
from modules.students import get_all_students


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-envelope-exclamation"></i> Warning Letters'
        '</h2>',
        unsafe_allow_html=True,
    )

    tab_issue, tab_log = st.tabs([
        "  Issue Warning  ",
        "  Issued Letters  ",
    ])

    with tab_issue:
        _render_issue()
    with tab_log:
        _render_log()


# ------------------------------------------------------------------ #
def _render_issue():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-file-earmark-text"></i> Issue Academic Warning'
        '</h3>',
        unsafe_allow_html=True,
    )

    students = get_all_students()
    if not students:
        st.warning("No students registered.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    only_at_risk = st.checkbox(
        "Only show MEDIUM/HIGH risk students",
        value=True,
        key="warn_only_at_risk",
    )

    if only_at_risk:
        candidates = get_at_risk_students(min_level="MEDIUM")
        if not candidates:
            st.success("No at-risk students at the moment. ✓ All accounts in good standing.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        student_opts = {
            f"{p['student_id']} — {p['name']} {p['surname']}  ·  {p['risk_level']}":
            p["student_id"] for p in candidates
        }
    else:
        student_opts = {
            f"{s['student_id']} — {s['name']} {s['surname']}": s["student_id"]
            for s in students
        }

    label = st.selectbox("Select student", list(student_opts.keys()))
    student_id = student_opts[label]

    profile = get_student_risk(student_id)
    if profile:
        risk = profile["risk_level"]
        color = "#FF6B9D" if risk == "HIGH" else (
            "#FF8FB1" if risk == "MEDIUM" else
            "#8B5FBF" if risk == "LOW" else "#6A3DE8"
        )
        reasons_html = "".join(f"<li>{r}</li>" for r in profile["reasons"])
        st.markdown(
            f"""
            <div style="margin-top:0.5rem; padding:1rem 1.25rem;
                        background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="margin:0 0 0.4rem 0; color:#8A8AA8; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.05em;">
                    Risk Snapshot
                </p>
                <p style="margin:0 0 0.5rem 0; color:#2D2D44;">
                    <strong style="color:{color};">{risk} RISK</strong>
                </p>
                <ul style="margin:0; padding-left:1.2rem; color:#2D2D44; font-size:0.92rem;">
                    {reasons_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    custom_reason = st.text_area(
        "Custom reason (optional)",
        placeholder="e.g. Failure to submit Assignment 2 by the second deadline.",
        height=90,
        key="warn_reason",
    )

    if st.button(
        "Generate Warning Letter",
        use_container_width=True,
        key="warn_generate_btn",
    ):
        with st.spinner("Generating letter..."):
            ok, msg, path = generate_warning_letter(student_id, custom_reason)
        if ok:
            st.session_state["last_warning_path"] = path
            st.session_state["last_warning_msg"] = msg
        else:
            st.session_state["last_warning_path"] = None
            st.session_state["last_warning_msg"] = msg
            st.error(msg)

    # Show success + download button OUTSIDE the form
    last_path = st.session_state.get("last_warning_path")
    last_msg = st.session_state.get("last_warning_msg")
    if last_path:
        st.success(last_msg)
        try:
            with open(last_path, "rb") as f:
                st.download_button(
                    label="Download Warning Letter",
                    data=f.read(),
                    file_name=Path(last_path).name,
                    mime="application/pdf",
                    key="dl_just_warned",
                )
        except FileNotFoundError:
            st.warning("Letter file no longer on disk.")

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
def _render_log():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-archive"></i> Issued Warning Letters'
        '</h3>',
        unsafe_allow_html=True,
    )

    log = get_warning_log()
    if not log:
        st.info("No warning letters issued yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(log)
    df_display = df[["id", "issued_on", "student_id", "student_name",
                     "reason", "file_path"]].copy()
    df_display["file_path"] = df_display["file_path"].apply(
        lambda p: Path(p).name if p else "—"
    )
    df_display["reason"] = df_display["reason"].fillna("Academic risk warning")
    df_display.columns = ["#", "Issued", "Student ID", "Student",
                          "Reason", "File"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Total letters issued: <strong style='color:#6A3DE8;'>{len(log)}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Download section ----
    files = list_generated_warnings()
    if not files:
        return

    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-download"></i> Download Letter'
        '</h3>',
        unsafe_allow_html=True,
    )

    options = {f["filename"]: f["path"] for f in files}
    sel = st.selectbox("Select letter", list(options.keys()), key="warn_dl_select")

    try:
        with open(options[sel], "rb") as f:
            st.download_button(
                label="Download Selected PDF",
                data=f.read(),
                file_name=sel,
                mime="application/pdf",
                key="dl_warn_archive",
            )
    except FileNotFoundError:
        st.error("File missing on disk.")

    st.markdown("</div>", unsafe_allow_html=True)