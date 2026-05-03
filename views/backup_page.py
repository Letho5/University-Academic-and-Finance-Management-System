"""
Q9 — Backup & Restore page
Tabs: Export Backup | Restore Backup | Backup Archive
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from modules.backup import (
    export_database,
    import_database,
    list_backups,
    get_backup_summary,
)


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-cloud-arrow-up"></i> Backup &amp; Restore'
        '</h2>',
        unsafe_allow_html=True,
    )

    _render_summary_strip()

    tab_export, tab_restore, tab_archive = st.tabs([
        "  Export Backup  ",
        "  Restore Backup  ",
        "  Backup Archive  ",
    ])

    with tab_export:
        _render_export()
    with tab_restore:
        _render_restore()
    with tab_archive:
        _render_archive()


# ------------------------------------------------------------------ #
def _render_summary_strip():
    s = get_backup_summary()
    total = sum(s.values())

    cells = "".join(
        f'<div style="flex:1; min-width:120px;">'
        f'<p style="color:#8A8AA8; font-size:0.72rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">{k.replace("_"," ").title()}</p>'
        f'<p style="color:#2D2D44; font-size:1.25rem; font-weight:600; margin:0.2rem 0 0 0;">{v}</p>'
        f'</div>'
        for k, v in s.items()
    )

    html = (
        '<div class="content-card" style="margin-bottom:1rem;">'
        '<div style="display:flex; gap:1rem; flex-wrap:wrap; align-items:center;">'
        '<div style="min-width:160px;">'
        '<p style="color:#8A8AA8; font-size:0.72rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Total Records</p>'
        f'<p style="color:#6A3DE8; font-size:1.7rem; font-weight:600; margin:0.2rem 0 0 0;">{total}</p>'
        '</div>'
        '<div style="flex:1; display:flex; gap:1rem; flex-wrap:wrap;">'
        f'{cells}'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
# ------------------------------------------------------------------ #
def _render_export():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-download"></i> Export Database to JSON'
        '</h3>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='color:#8A8AA8; font-size:0.9rem; margin:0.25rem 0 0.75rem 0;'>"
        "Creates a complete snapshot of every table — students, courses, enrolments, "
        "marks, fee accounts, payments, and warning letters — saved as a single "
        "timestamped JSON file in the <code>exports/</code> folder."
        "</p>",
        unsafe_allow_html=True,
    )

    if st.button("Generate Backup", use_container_width=False, key="exp_btn"):
        with st.spinner("Exporting database..."):
            ok, msg, path = export_database()
        if ok:
            st.session_state["last_backup_path"] = path
            st.session_state["last_backup_msg"] = msg
        else:
            st.error(msg)

    last_path = st.session_state.get("last_backup_path")
    last_msg = st.session_state.get("last_backup_msg")
    if last_path:
        st.success(last_msg)
        try:
            with open(last_path, "rb") as f:
                st.download_button(
                    label="Download Backup File",
                    data=f.read(),
                    file_name=Path(last_path).name,
                    mime="application/json",
                    key="dl_backup",
                )
        except FileNotFoundError:
            st.warning("File no longer on disk.")

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_restore():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-upload"></i> Restore from Backup File'
        '</h3>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='color:#FF6B9D; font-size:0.88rem; margin:0.25rem 0 0.75rem 0;'>"
        "<strong>⚠ Warning:</strong> Restoring will overwrite the current database. "
        "Always export a backup first."
        "</p>",
        unsafe_allow_html=True,
    )

    upload = st.file_uploader(
        "Select an APEX backup JSON file",
        type=["json"],
        key="restore_uploader",
    )

    if upload is None:
        st.info("Upload a backup file to begin.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown(
        f"<p style='color:#8A8AA8; font-size:0.88rem; margin-top:0.5rem;'>"
        f"File: <strong style='color:#2D2D44;'>{upload.name}</strong> · "
        f"Size: <strong style='color:#2D2D44;'>{round(len(upload.getvalue())/1024, 1)} KB</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )

    confirm = st.checkbox(
        "I confirm that I want to OVERWRITE the current database with this file.",
        key="restore_confirm",
    )

    if st.button(
        "Restore Database",
        disabled=not confirm,
        key="restore_btn",
    ):
        file_bytes = upload.getvalue()
        with st.spinner("Restoring database..."):
            ok, msg, stats = import_database(file_bytes, replace=True)
        if ok:
            st.success(msg)
            if stats:
                df = pd.DataFrame(
                    [{"Table": k, "Rows imported": v} for k, v in stats.items()]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            st.info("Refresh other pages to see the restored data.")
        else:
            st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_archive():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-folder2-open"></i> Backup Archive'
        '</h3>',
        unsafe_allow_html=True,
    )

    backups = list_backups()
    if not backups:
        st.info("No backups generated yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(backups)[["filename", "created", "size_kb"]]
    df.columns = ["Filename", "Created", "Size (KB)"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Total backups: <strong style='color:#6A3DE8;'>{len(backups)}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Download from archive
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-download"></i> Download a Backup'
        '</h3>',
        unsafe_allow_html=True,
    )
    options = {b["filename"]: b["path"] for b in backups}
    sel = st.selectbox("Select backup", list(options.keys()), key="bk_arch_sel")
    try:
        with open(options[sel], "rb") as f:
            st.download_button(
                label="Download Selected JSON",
                data=f.read(),
                file_name=sel,
                mime="application/json",
                key="dl_bk_archive",
            )
    except FileNotFoundError:
        st.error("File missing on disk.")
    st.markdown("</div>", unsafe_allow_html=True)