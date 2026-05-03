"""
APEX UNIVERSITY - Configuration Constants
==========================================
Centralized business rules and settings.
Other modules import from here so values stay consistent.

Owned by: Sinqobile (shared, but coordinated)
"""

# === BRAND ===
APP_NAME = "APEX UNIVERSITY"
APP_TAGLINE = "Excellence Defined."

# === CURRENCY ===
CURRENCY_SYMBOL = "R"
CURRENCY_CODE = "ZAR"


def format_currency(amount: float) -> str:
    """
    Format a number as South African Rand.
    Example: format_currency(1850.5) -> 'R 1,850.50'
    """
    if amount is None:
        return "R 0.00"
    return f"R {amount:,.2f}"


# === FEE RULES ===
# Minimum amount a student must pay before they are considered fully enrolled.
# Used by the fee module to flag students who haven't met the threshold.
MINIMUM_INITIAL_PAYMENT = 4500.00

# Default fee per course (used when adding a new course without specifying a fee).
DEFAULT_COURSE_FEE = 1850.00

# Maximum number of courses a student can register for in a single semester.
MAX_COURSES_PER_SEMESTER = 6


# === PAYMENT METHODS ===
# Comprehensive list catering to students from all backgrounds:
#   - NSFAS for government-sponsored students
#   - Bursary for employer/NGO sponsorships
#   - EFT, Card, PayU for banked students
#   - Retail for unbanked students (pay cash at supermarkets)
#   - Cash for in-person campus payments
PAYMENT_METHODS = [
    "NSFAS Bursary",
    "Other Bursary / Sponsor",
    "EFT (Electronic Funds Transfer)",
    "Debit / Credit Card",
    "PayU (Online Gateway)",
    "Retail (Pick n Pay / Checkers / Shoprite / PEP)",
    "Cash (Campus Office)",
]


# === ACADEMIC RULES (for teammates' reference) ===
PASS_MARK = 50.0
DISTINCTION_MARK = 75.0
SUPPLEMENTARY_MIN = 40.0