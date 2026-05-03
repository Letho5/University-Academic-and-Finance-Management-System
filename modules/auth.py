"""
modules/auth.py
Authentication for APEX UNIVERSITY.

Phase 1: hardcoded demo accounts (4 roles for the demo).
Phase later: extend authenticate() to also query the students table for student logins.
"""

# Demo accounts — keys are emails (lowercased). Passwords are plaintext for the demo only.
DEMO_USERS = {
    "admin@apex.ac.za": {
        "password": "admin123",
        "role": "Administrator",
        "name": "Sinqobile Mthembu",
    },
    "finance@apex.ac.za": {
        "password": "finance123",
        "role": "Finance Officer",
        "name": "Finance Office",
    },
    "lecturer@apex.ac.za": {
        "password": "lecturer123",
        "role": "Lecturer",
        "name": "Dr. Mokoena",
    },
    "student@apex.ac.za": {
        "password": "student123",
        "role": "Student",
        "name": "Test Student",
    },
}


def authenticate(email: str, password: str):
    """
    Validate credentials.

    Returns:
        (success: bool, user: dict | None, message: str)
        user dict shape: {"email", "role", "name"}
    """
    # Defensive trimming — users always paste with stray whitespace
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        return False, None, "Please enter both email and password."

    user = DEMO_USERS.get(email)
    if user is None:
        return False, None, "No account found with that email."

    if user["password"] != password:
        return False, None, "Incorrect password. Please try again."

    return True, {
        "email": email,
        "role": user["role"],
        "name": user["name"],
    }, "Login successful."


def logout(session_state):
    """Clear session state on logout. Called from the dashboard later."""
    session_state.authenticated = False
    session_state.user = None