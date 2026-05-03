"""
Comprehensive test for the fee module — all 7 functions.
Delete this file when you're done testing.
"""
from database import init_database, get_connection, generate_student_id
from modules.fees import (
    setup_fee_account,
    make_payment,
    get_balance,
    get_fee_account,
    get_payment_history,
    has_met_minimum_payment,
    get_all_fee_accounts,
)
from config import format_currency

# Initialize database
init_database()

# Create two test students
student_a = generate_student_id()
student_b = generate_student_id()

with get_connection() as conn:
    conn.execute("""
        INSERT OR IGNORE INTO students 
        (student_id, name, surname, email, password)
        VALUES (?, ?, ?, ?, ?)
    """, (student_a, "Sarah", "Mokoena", f"{student_a}@apex.ac.za", "test123"))
    conn.execute("""
        INSERT OR IGNORE INTO students 
        (student_id, name, surname, email, password)
        VALUES (?, ?, ?, ?, ?)
    """, (student_b, "Thabo", "Khumalo", f"{student_b}@apex.ac.za", "test123"))

print(f"Created test students: {student_a}, {student_b}")

# === SETUP ===
print("\n" + "="*60)
print("SETUP PHASE")
print("="*60)

setup_fee_account(student_a, 9250.00)
setup_fee_account(student_b, 7400.00)
print(f"Fee accounts created for both students.")

# Student A pays R 4,500 (meets minimum)
make_payment(student_a, 4500.00, "EFT (Electronic Funds Transfer)", "EFT-001")

# Student A pays R 2,000 more
make_payment(student_a, 2000.00, "NSFAS Bursary", "NSFAS-001")

# Student B pays R 2,000 (does NOT meet minimum)
make_payment(student_b, 2000.00, "Cash (Campus Office)", "CASH-001")

print("Payments made.")

# === FUNCTION 3: get_balance ===
print("\n" + "="*60)
print("FUNCTION 3: get_balance()")
print("="*60)
print(f"  Student A balance: {format_currency(get_balance(student_a))}")
print(f"  Student B balance: {format_currency(get_balance(student_b))}")
print(f"  Non-existent student: {format_currency(get_balance('STU99999'))}")

# === FUNCTION 4: get_fee_account ===
print("\n" + "="*60)
print("FUNCTION 4: get_fee_account()")
print("="*60)
acc = get_fee_account(student_a)
print(f"  Student A account:")
print(f"    Total Billed: {format_currency(acc['total_billed'])}")
print(f"    Total Paid:   {format_currency(acc['total_paid'])}")
print(f"    Balance:      {format_currency(acc['balance'])}")
print(f"    Last Payment: {acc['last_payment_date']}")

print(f"  Non-existent student: {get_fee_account('STU99999')}")

# === FUNCTION 5: get_payment_history ===
print("\n" + "="*60)
print("FUNCTION 5: get_payment_history()")
print("="*60)
history = get_payment_history(student_a)
print(f"  Student A has {len(history)} payment(s):")
for p in history:
    print(f"    {p['receipt_number']} | {format_currency(p['amount']):>12} | {p['payment_method']}")

# === FUNCTION 6: has_met_minimum_payment ===
print("\n" + "="*60)
print("FUNCTION 6: has_met_minimum_payment()")
print("="*60)
met_a, msg_a = has_met_minimum_payment(student_a)
met_b, msg_b = has_met_minimum_payment(student_b)
print(f"  Student A (paid R 6,500): {met_a}")
print(f"    Message: {msg_a}")
print(f"  Student B (paid R 2,000): {met_b}")
print(f"    Message: {msg_b}")

# === FUNCTION 7: get_all_fee_accounts ===
print("\n" + "="*60)
print("FUNCTION 7: get_all_fee_accounts()")
print("="*60)
all_accounts = get_all_fee_accounts()
print(f"  Total fee accounts in system: {len(all_accounts)}")
for a in all_accounts:
    print(f"    {a['student_id']} | {a['name']} {a['surname']:<15} | "
          f"Bill: {format_currency(a['total_billed']):>12} | "
          f"Bal: {format_currency(a['balance']):>12} | "
          f"Status: {a['status']}")

# === CLEANUP ===
with get_connection() as conn:
    conn.execute("DELETE FROM students WHERE student_id IN (?, ?)", (student_a, student_b))

print("\n" + "="*60)
print("All tests complete. Test students cleaned up.")
print("="*60)