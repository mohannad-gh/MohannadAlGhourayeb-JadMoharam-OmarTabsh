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
