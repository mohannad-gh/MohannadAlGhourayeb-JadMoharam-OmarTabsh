# The four system roles, exactly as they must appear in the "role" claim of a token
# Omar Tabsh - 202400798

ADMIN = "admin"        # Security Administrator
ANALYST = "analyst"    # Security Analyst
USER = "user"          # Regular Employee/User
AUDITOR = "auditor"    # Auditor

ALL_ROLES = (ADMIN, ANALYST, USER, AUDITOR)

ROLE_TITLES = {
    ADMIN: "Security Administrator",
    ANALYST: "Security Analyst",
    USER: "Regular Employee/User",
    AUDITOR: "Auditor",
}

# Full role titles stored by the Users service (e.g. "Security Administrator") -> role code
_ROLE_ALIASES = {
    "security administrator": ADMIN,
    "administrator": ADMIN,
    "security analyst": ANALYST,
    "analyst": ANALYST,
    "regular user": USER,
    "regular employee": USER,
    "regular employee/user": USER,
    "employee": USER,
    "auditor": AUDITOR,
}


def normalize_role(value):
    """Return the role code for a code or a full role title, or None if unknown."""
    if not isinstance(value, str):
        return None
    key = " ".join(value.split()).lower()
    if key in ALL_ROLES:
        return key
    return _ROLE_ALIASES.get(key)
