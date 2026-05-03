"""
Q5 — Fee Payment Management page
Tabs: Record Payment | Student Account | All Accounts | Payments Ledger
Backend logic in modules/fees.py.
"""
import streamlit as st
import pandas as pd

from modules.fees import (
    setup_fee_account,
    make_payment,
    get_fee_account,
    get_payment_history,
    get_all_fee_accounts,
    has_met_minimum_payment,
)
from modules.students import get_all_students
from database import get_connection
from config import (
    PAYMENT_METHODS,
    MINIMUM_INITIAL_PAYMENT,
    DEFAULT_COURSE_FEE,
    format_currency,
)


def _get_all_payments():
    """Pull every payment from DB joined with student names (used in ledger)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.receipt_number, p.payment_date, p.student_id,
                   s.name || ' ' || s.surname AS student_name,
                   p.amount, p.payment_method, p.reference
            FROM payments p
            LEFT JOIN students s ON s.student_id = p.student_id
            ORDER BY p.payment_date DESC
        """).fetchall()
    return [dict(r) for r in rows]


def render():
    st.markdown(
        '<h2 class="page-title">'
        '<i class="bi bi-cash-coin"></i> Fee Payment Management'
        '</h2>',
        unsafe_allow_html=True,
    )

    _render_summary_strip()

    tab_pay, tab_setup, tab_account, tab_all, tab_ledger = st.tabs([
        "  Record Payment  ",
        "  Setup Account  ",
        "  Student Account  ",
        "  All Accounts  ",
        "  Payments Ledger  ",
    ])

    with tab_pay:
        _render_payment_form()
    with tab_setup:
        _render_setup_form()
    with tab_account:
        _render_student_account()
    with tab_all:
        _render_all_accounts()
    with tab_ledger:
        _render_ledger()


# ------------------------------------------------------------------ #
def _render_summary_strip():
    accounts = get_all_fee_accounts()
    total_billed = sum(a["total_billed"] for a in accounts)
    total_paid = sum(a["total_paid"] for a in accounts)
    total_outstanding = sum(a["balance"] for a in accounts)
    settled = sum(1 for a in accounts if a["status"] == "Settled")

    st.markdown(
        f"""
        <div class="content-card" style="margin-bottom:1rem;">
            <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
                <div style="flex:1; min-width:180px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Total Billed</p>
                    <p style="color:#2D2D44; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(total_billed)}</p>
                </div>
                <div style="flex:1; min-width:180px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Total Collected</p>
                    <p style="color:#6A3DE8; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(total_paid)}</p>
                </div>
                <div style="flex:1; min-width:180px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Outstanding</p>
                    <p style="color:#FF6B9D; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(total_outstanding)}</p>
                </div>
                <div style="flex:1; min-width:180px;">
                    <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Settled Accounts</p>
                    <p style="color:#2D2D44; font-size:1.5rem; font-weight:600; margin:0.25rem 0 0 0;">{settled}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ #
def _render_setup_form():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-folder-plus"></i> Open / Update Fee Account'
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

    with st.form("setup_account_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            student_label = st.selectbox("Student *", list(student_opts.keys()))
        with c2:
            total_fee = st.number_input(
                "Total Billed (R) *",
                min_value=0.0,
                value=float(DEFAULT_COURSE_FEE * 5),  # rough default: 5 modules
                step=100.0,
                format="%.2f",
            )

        st.markdown(
            "<p style='color:#8A8AA8; font-size:0.85rem; margin:0.25rem 0 0.75rem 0;'>"
            "Use this to open a fee account for a new student or update the billed total "
            "if courses change. Existing payments are preserved."
            "</p>",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("Save Account", use_container_width=True)
        if submitted:
            ok, msg = setup_fee_account(student_opts[student_label], total_fee)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_payment_form():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-receipt"></i> Record New Payment'
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

    with st.form("payment_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            student_label = st.selectbox("Student *", list(student_opts.keys()))
            amount = st.number_input(
                "Amount (R) *",
                min_value=0.01,
                value=float(MINIMUM_INITIAL_PAYMENT),
                step=100.0,
                format="%.2f",
            )
        with c2:
            method = st.selectbox("Payment Method *", PAYMENT_METHODS)
            reference = st.text_input(
                "Reference / Transaction ID",
                placeholder="e.g. NSFAS-2026-0145 or EFT ref",
            )

        # Live balance preview
        sel_id = student_opts[student_label]
        acc = get_fee_account(sel_id)
        if acc:
            st.markdown(
                f"<p style='color:#8A8AA8; font-size:0.85rem; margin:0.25rem 0 0.75rem 0;'>"
                f"Outstanding balance: "
                f"<strong style='color:#FF6B9D;'>{format_currency(acc['balance'])}</strong> · "
                f"Paid to date: <strong style='color:#6A3DE8;'>{format_currency(acc['total_paid'])}</strong>"
                f"</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='color:#FF6B9D; font-size:0.85rem; margin:0.25rem 0 0.75rem 0;'>"
                "⚠ No fee account exists. Open one in the <strong>Setup Account</strong> tab first."
                "</p>",
                unsafe_allow_html=True,
            )

        submitted = st.form_submit_button("Record Payment", use_container_width=True)
        if submitted:
            ok, msg, receipt = make_payment(sel_id, amount, method, reference)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_student_account():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-person-vcard"></i> Student Account Statement'
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
    student_id = student_opts[label]

    account = get_fee_account(student_id)
    if not account:
        st.info("No fee account yet for this student. Open one in the 'Setup Account' tab.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    billed = account["total_billed"]
    paid = account["total_paid"]
    balance = account["balance"]
    last = account["last_payment_date"] or "—"

    if balance <= 0 and paid > 0:
        status_text, status_class = "SETTLED", "settled"
    elif paid > 0:
        status_text, status_class = "PARTIAL", "partial"
    else:
        status_text, status_class = "UNPAID", "unpaid"

    met, met_msg = has_met_minimum_payment(student_id)
    min_color = "#6A3DE8" if met else "#FF6B9D"

    st.markdown(
        f"""
        <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:0.5rem;">
            <div style="flex:1; min-width:160px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Billed</p>
                <p style="color:#2D2D44; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(billed)}</p>
            </div>
            <div style="flex:1; min-width:160px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Paid</p>
                <p style="color:#6A3DE8; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(paid)}</p>
            </div>
            <div style="flex:1; min-width:160px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Balance</p>
                <p style="color:#FF6B9D; font-size:1.35rem; font-weight:600; margin:0.25rem 0 0 0;">{format_currency(balance)}</p>
            </div>
            <div style="flex:1; min-width:160px; padding:1rem; background:rgba(255,255,255,0.55); border-radius:14px;">
                <p style="color:#8A8AA8; font-size:0.78rem; margin:0; text-transform:uppercase;">Status</p>
                <span class="status-pill {status_class}" style="margin-top:0.4rem; display:inline-block;">{status_text}</span>
            </div>
        </div>
        <p style="color:#8A8AA8; font-size:0.85rem; margin-top:0.75rem;">
            Last payment: <strong style="color:#2D2D44;">{last}</strong> ·
            <span style="color:{min_color};">{met_msg}</span>
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Payment history ----
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-clock-history"></i> Payment History'
        '</h3>',
        unsafe_allow_html=True,
    )

    payments = get_payment_history(student_id)
    if not payments:
        st.info("No payments recorded yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(payments)
    df["amount"] = df["amount"].apply(format_currency)
    df.columns = ["Receipt", "Amount", "Method", "Reference", "Date"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_all_accounts():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-people"></i> All Student Fee Accounts'
        '</h3>',
        unsafe_allow_html=True,
    )

    accounts = get_all_fee_accounts()
    if not accounts:
        st.info("No accounts on record.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(accounts)
    df_display = df.copy()
    df_display["full_name"] = df_display["name"] + " " + df_display["surname"]
    df_display = df_display[[
        "student_id", "full_name", "total_billed",
        "total_paid", "balance", "last_payment_date", "status",
    ]]
    for col in ("total_billed", "total_paid", "balance"):
        df_display[col] = df_display[col].apply(format_currency)
    df_display.columns = [
        "Student ID", "Student", "Billed",
        "Paid", "Balance", "Last Payment", "Status",
    ]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
def _render_ledger():
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown(
        '<h3 class="content-card-title">'
        '<i class="bi bi-journal-text"></i> All Payments Ledger'
        '</h3>',
        unsafe_allow_html=True,
    )

    payments = _get_all_payments()
    if not payments:
        st.info("No payments on record.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(payments)
    df["amount"] = df["amount"].apply(format_currency)
    df = df[[
        "receipt_number", "payment_date", "student_id",
        "student_name", "amount", "payment_method", "reference",
    ]]
    df.columns = ["Receipt", "Date", "Student ID", "Student", "Amount", "Method", "Reference"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(
        f"<p style='color:#8A8AA8; margin-top:0.5rem;'>"
        f"Total transactions: <strong style='color:#6A3DE8;'>{len(payments)}</strong>"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)