"""
Q7 — Academic Reports page
Generate transcript PDFs and list generated files.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.reports import generate_academic_report, list_generated_reports
from modules.students import get_all_students


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-file-earmark-pdf"></i> Academic Reports'
        '</h2>',
        unsafe_allow_html=True,
    )

    tab_gen, tab_list = st.tabs([
        "  Generate Transcript  ",
        "  Report Archive  ",
    ])

    with tab_gen:
        _render_generator()
    with tab_list:
        _render_archive()


# ------------------------------------------------------------------ #
def _render_generator():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-printer"></i> Generate Academic Transcript'
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

    label = st.selectbox("Select student", list(student_opts.keys()))
    student_id = student_opts[label]

    st.markdown(
        "<p style='color:#8A8AA8; font-size:0.85rem; margin:0.25rem 0 0.75rem 0;'>"
        "Generates a professional PDF transcript with the student's marks, "
        "grades, and fee summary. The file is saved to the <code>reports/</code> folder."
        "</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        generate_clicked = st.button(
            "Generate PDF", use_container_width=True, key="gen_report_btn",
        )

    if generate_clicked:
        with st.spinner("Generating transcript..."):
            ok, msg, path = generate_academic_report(student_id)
        if ok:
            st.success(msg)
            try:
                with open(path, "rb") as f:
                    st.download_button(
                        label="Download Transcript",
                        data=f.read(),
                        file_name=Path(path).name,
                        mime="application/pdf",
                        use_container_width=False,
                        key="dl_just_generated",
                    )
            except Exception as e:
                st.error(f"Could not open file for download: {e}")
        else:
            st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_archive():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-folder2-open"></i> Generated Reports'
        '</h3>',
        unsafe_allow_html=True,
    )

    reports = list_generated_reports()
    if not reports:
        st.info("No reports generated yet. Create one in the 'Generate Transcript' tab.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(reports)[["filename", "created", "size_kb"]]
    df.columns = ["Filename", "Created", "Size (KB)"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Total reports: <strong style='color:#6A3DE8;'>{len(reports)}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Download section ----
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-download"></i> Download Report'
        '</h3>',
        unsafe_allow_html=True,
    )

    options = {r["filename"]: r["path"] for r in reports}
    sel = st.selectbox("Select report", list(options.keys()), key="report_dl_select")

    try:
        with open(options[sel], "rb") as f:
            st.download_button(
                label="Download Selected PDF",
                data=f.read(),
                file_name=sel,
                mime="application/pdf",
                key="dl_archive",
            )
    except FileNotFoundError:
        st.error("File missing on disk — it may have been moved or deleted.")

    st.markdown("</div>", unsafe_allow_html=True)