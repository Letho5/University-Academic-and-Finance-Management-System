"""
APEX UNIVERSITY - Fee Payment Management Module


Responsibilities:
  - Track all student payments
  - Prevent overpayment (cannot pay more than owed)
  - Show balances for any student
  - Maintain a complete payment history
  - Verify minimum payment for enrollment eligibility

Tables used:
  - fee_accounts  (one row per student, summary of charges/payments)
  - payments      (one row per transaction, full audit trail)
  - students      (read-only - to verify student exists)

"""

from database import get_connection, generate_receipt_number
from config import MINIMUM_INITIAL_PAYMENT, PAYMENT_METHODS, format_currency
from datetime import datetime


# =====================================================================
# FUNCTION 1: SETUP FEE ACCOUNT
# =====================================================================
def setup_fee_account(student_id: str, total_fee: float) -> tuple[bool, str]:
    """
    Create or update a student's fee account.

    This is called when:
      - A student first enrolls (creates account)
      - A student adds more courses (updates total_fee)

    Args:
        student_id: The student's unique ID (e.g., "STU00001")
        total_fee: Total amount the student owes (e.g., 9250.00)

    Returns:
        (success, message) tuple
    """
    # Step 1: Validate the input
    if total_fee < 0:
        return False, "Total fee cannot be negative."

    # Step 2: Check that the student actually exists
    with get_connection() as conn:
        student = conn.execute(
            "SELECT student_id FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if not student:
            return False, f"Student {student_id} does not exist."

        # Step 3: Check if the student already has a fee account
        existing = conn.execute(
            "SELECT total_paid FROM fee_accounts WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if existing:
            # Update existing account
            already_paid = existing["total_paid"]
            new_balance = total_fee - already_paid

            conn.execute("""
                UPDATE fee_accounts 
                SET total_billed = ?, balance = ?
                WHERE student_id = ?
            """, (total_fee, new_balance, student_id))

            return True, f"Fee account updated. New balance: {format_currency(new_balance)}"
        else:
            # Create new account
            conn.execute("""
                INSERT INTO fee_accounts 
                (student_id, total_billed, total_paid, balance)
                VALUES (?, ?, 0, ?)
            """, (student_id, total_fee, total_fee))

            return True, f"Fee account created. Total owed: {format_currency(total_fee)}"


# =====================================================================
# FUNCTION 2: MAKE PAYMENT
# =====================================================================
def make_payment(
    student_id: str,
    amount: float,
    payment_method: str,
    reference: str = ""
) -> tuple[bool, str, str]:
    """
    Record a payment for a student.

    Args:
        student_id: The student paying (e.g., "STU00001")
        amount: How much they are paying (e.g., 4500.00)
        payment_method: How they paid (must be from PAYMENT_METHODS list)
        reference: Optional transaction reference (e.g., bank ref number)

    Returns:
        (success, message, receipt_number) tuple

    Business rules enforced:
        1. Amount must be positive
        2. Payment method must be valid
        3. Student must exist
        4. Student must have a fee account
        5. Cannot pay more than the outstanding balance (overpayment prevention)
    """
    # Rule 1: Amount must be positive
    if amount <= 0:
        return False, "Payment amount must be greater than zero.", ""

    # Rule 2: Payment method must be valid
    if payment_method not in PAYMENT_METHODS:
        valid_methods = ", ".join(PAYMENT_METHODS)
        return False, f"Invalid payment method. Choose from: {valid_methods}", ""

    # Rules 3 & 4: Verify student and fee account exist
    with get_connection() as conn:
        # Check student exists
        student = conn.execute(
            "SELECT student_id FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()
        if not student:
            return False, f"Student {student_id} does not exist.", ""

        # Check fee account exists
        account = conn.execute(
            "SELECT total_billed, total_paid, balance FROM fee_accounts WHERE student_id = ?",
            (student_id,)
        ).fetchone()
        if not account:
            return False, (
                f"Student {student_id} has no fee account yet. "
                f"Set up a fee account first using setup_fee_account()."
            ), ""

        # Rule 5: Prevent overpayment
        current_balance = account["balance"]
        if amount > current_balance:
            return False, (
                f"Overpayment blocked. "
                f"Outstanding balance is {format_currency(current_balance)}, "
                f"but you tried to pay {format_currency(amount)}."
            ), ""

        # All checks passed - record the payment
        receipt_number = generate_receipt_number()
        new_total_paid = account["total_paid"] + amount
        new_balance = account["total_billed"] - new_total_paid
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert into payments table (audit trail)
        conn.execute("""
            INSERT INTO payments 
            (receipt_number, student_id, amount, payment_method, reference, payment_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (receipt_number, student_id, amount, payment_method, reference, now))

        # Update fee_accounts table (current balance)
        conn.execute("""
            UPDATE fee_accounts
            SET total_paid = ?, balance = ?, last_payment_date = ?
            WHERE student_id = ?
        """, (new_total_paid, new_balance, now, student_id))

    success_msg = (
        f"Payment of {format_currency(amount)} recorded successfully. "
        f"New balance: {format_currency(new_balance)}. "
        f"Receipt: {receipt_number}"
    )
    return True, success_msg, receipt_number
# =====================================================================
# FUNCTION 3: GET BALANCE
# =====================================================================
def get_balance(student_id: str) -> float:
    """
    Get a student's current outstanding balance.

    Args:
        student_id: The student's ID (e.g., "STU00001")

    Returns:
        The balance as a float (e.g., 2750.00).
        Returns 0.0 if student has no fee account.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT balance FROM fee_accounts WHERE student_id = ?",
            (student_id,)
        ).fetchone()

    if row is None:
        return 0.0
    return float(row["balance"])
# =====================================================================
# FUNCTION 4: GET FEE ACCOUNT (FULL DETAILS)
# =====================================================================
def get_fee_account(student_id: str) -> dict | None:
    """
    Get full fee account details for a student.

    Args:
        student_id: The student's ID

    Returns:
        Dictionary with keys:
          - student_id
          - total_billed
          - total_paid
          - balance
          - last_payment_date
        Returns None if student has no fee account.
    """
    with get_connection() as conn:
        row = conn.execute("""
            SELECT student_id, total_billed, total_paid, balance, last_payment_date
            FROM fee_accounts
            WHERE student_id = ?
        """, (student_id,)).fetchone()

    if row is None:
        return None

    return {
        "student_id":          row["student_id"],
        "total_billed":        float(row["total_billed"]),
        "total_paid":          float(row["total_paid"]),
        "balance":             float(row["balance"]),
        "last_payment_date":   row["last_payment_date"],
    }
# =====================================================================
# FUNCTION 5: GET PAYMENT HISTORY
# =====================================================================
def get_payment_history(student_id: str) -> list[dict]:
    """
    Get all payments made by a specific student.

    Args:
        student_id: The student's ID

    Returns:
        List of dictionaries, each representing one payment.
        Most recent payment appears first.
        Returns empty list [] if student has no payments.
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT receipt_number, amount, payment_method, reference, payment_date
            FROM payments
            WHERE student_id = ?
            ORDER BY payment_date DESC
        """, (student_id,)).fetchall()

    return [
        {
            "receipt_number":  row["receipt_number"],
            "amount":          float(row["amount"]),
            "payment_method":  row["payment_method"],
            "reference":       row["reference"],
            "payment_date":    row["payment_date"],
        }
        for row in rows
    ]
# =====================================================================
# FUNCTION 6: CHECK MINIMUM PAYMENT
# =====================================================================
def has_met_minimum_payment(student_id: str) -> tuple[bool, str]:
    """
    Check if a student has paid at least the minimum required amount.

    The minimum is set in config.py as MINIMUM_INITIAL_PAYMENT (R 4,500).
    Q3 (Enrollment) can call this before confirming a student's registration.

    Args:
        student_id: The student's ID

    Returns:
        (met, message) tuple
        - met: True if total_paid >= minimum, False otherwise
        - message: Human-readable explanation
    """
    account = get_fee_account(student_id)

    if account is None:
        return False, f"Student {student_id} has no fee account."

    total_paid = account["total_paid"]

    if total_paid >= MINIMUM_INITIAL_PAYMENT:
        return True, (
            f"Minimum payment met. "
            f"Paid {format_currency(total_paid)} "
            f"(required: {format_currency(MINIMUM_INITIAL_PAYMENT)})"
        )
    else:
        shortfall = MINIMUM_INITIAL_PAYMENT - total_paid
        return False, (
            f"Minimum payment not yet met. "
            f"Paid {format_currency(total_paid)}, "
            f"needs {format_currency(shortfall)} more "
            f"(minimum: {format_currency(MINIMUM_INITIAL_PAYMENT)})"
        )
    # =====================================================================
# FUNCTION 7: GET ALL FEE ACCOUNTS (DASHBOARD VIEW)
# =====================================================================
def get_all_fee_accounts() -> list[dict]:
    """
    Get fee account summary for ALL students.
    Joins with the students table to include names for easy display.

    Returns:
        List of dictionaries, each containing:
          - student_id
          - name
          - surname
          - total_billed
          - total_paid
          - balance
          - last_payment_date
          - status: 'Settled', 'Partial', or 'Unpaid'

    Used by:
        - Finance dashboard (overview of all accounts)
        - Reports module (Q7)
        - Risk detection if it needs financial info
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT 
                s.student_id, s.name, s.surname,
                COALESCE(f.total_billed, 0)        AS total_billed,
                COALESCE(f.total_paid, 0)          AS total_paid,
                COALESCE(f.balance, 0)             AS balance,
                f.last_payment_date
            FROM students s
            LEFT JOIN fee_accounts f ON s.student_id = f.student_id
            ORDER BY s.surname, s.name
        """).fetchall()

    result = []
    for row in rows:
        # Determine status based on balance and amount paid
        balance = float(row["balance"])
        total_paid = float(row["total_paid"])
        total_billed = float(row["total_billed"])

        if total_billed == 0:
            status = "No Account"
        elif balance <= 0:
            status = "Settled"
        elif total_paid > 0:
            status = "Partial"
        else:
            status = "Unpaid"

        result.append({
            "student_id":         row["student_id"],
            "name":               row["name"],
            "surname":            row["surname"],
            "total_billed":       total_billed,
            "total_paid":         total_paid,
            "balance":            balance,
            "last_payment_date":  row["last_payment_date"],
            "status":             status,
        })

    return result