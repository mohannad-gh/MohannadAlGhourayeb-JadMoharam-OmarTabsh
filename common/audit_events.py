# Agreed vocabulary for audit log records (used by every service)
# Omar Tabsh - 202400798
#
# The Security Reports service counts these exact strings (for example the
# activity report counts LOGIN_FAILED), so always use these constants instead of
# typing the action name by hand.

# Log severity levels (from the project document)
INFORMATION = "Information"
WARNING = "Warning"
ERROR = "Error"
CRITICAL = "Critical"
LOG_SEVERITIES = (INFORMATION, WARNING, ERROR, CRITICAL)

# Values for the "related_service" field
USERS_SERVICE = "Users"
ASSETS_SERVICE = "Assets"
INCIDENTS_SERVICE = "Incidents"
THREATS_SERVICE = "Threat Intelligence"
LOGS_SERVICE = "Audit Logging"
REPORTS_SERVICE = "Security Reports"
VULNERABILITIES_SERVICE = "Vulnerabilities"
NOTIFICATIONS_SERVICE = "Notifications"
PLAYBOOKS_SERVICE = "Playbooks"
RELATED_SERVICES = (
    USERS_SERVICE, ASSETS_SERVICE, INCIDENTS_SERVICE, THREATS_SERVICE,
    LOGS_SERVICE, REPORTS_SERVICE, VULNERABILITIES_SERVICE,
    NOTIFICATIONS_SERVICE, PLAYBOOKS_SERVICE,
)

# Actions. Format: UPPER_SNAKE_CASE. Suggested severity in the comment.
# Users and Identity Management (Mohannad Al Ghourayeb)
LOGIN_SUCCESS = "LOGIN_SUCCESS"            # Information
LOGIN_FAILED = "LOGIN_FAILED"              # Warning
USER_CREATED = "USER_CREATED"              # Information
USER_UPDATED = "USER_UPDATED"              # Information
USER_DELETED = "USER_DELETED"              # Warning
ROLE_CHANGED = "ROLE_CHANGED"              # Warning
# Asset Management (Mohannad Al Ghourayeb)
ASSET_CREATED = "ASSET_CREATED"            # Information
ASSET_UPDATED = "ASSET_UPDATED"            # Information
ASSET_DELETED = "ASSET_DELETED"            # Warning
# Incident Management (Jad Moharam)
INCIDENT_CREATED = "INCIDENT_CREATED"                  # Information
INCIDENT_ASSIGNED = "INCIDENT_ASSIGNED"                # Information
INCIDENT_STATUS_CHANGED = "INCIDENT_STATUS_CHANGED"    # Information
INCIDENT_NOTE_ADDED = "INCIDENT_NOTE_ADDED"            # Information
# Threat Intelligence (Omar Tabsh)
THREAT_CREATED = "THREAT_CREATED"          # Information
THREAT_UPDATED = "THREAT_UPDATED"          # Information
THREAT_DELETED = "THREAT_DELETED"          # Warning
# Security Audit Logging (Omar Tabsh)
LOG_DELETED = "LOG_DELETED"                # Warning
# Vulnerability Management (Mohannad Al Ghourayeb)
VULNERABILITY_CREATED = "VULNERABILITY_CREATED"        # Information
VULNERABILITY_UPDATED = "VULNERABILITY_UPDATED"        # Information
VULNERABILITY_DELETED = "VULNERABILITY_DELETED"        # Warning
# Notification and Alert Management (Jad Moharam)
NOTIFICATION_CREATED = "NOTIFICATION_CREATED"          # Information
NOTIFICATION_READ = "NOTIFICATION_READ"                # Information
NOTIFICATION_DELETED = "NOTIFICATION_DELETED"          # Warning
# Security Playbook and Response Automation (Jad Moharam)
PLAYBOOK_CREATED = "PLAYBOOK_CREATED"                  # Information
PLAYBOOK_DELETED = "PLAYBOOK_DELETED"                  # Warning
RESPONSE_ACTION_ADDED = "RESPONSE_ACTION_ADDED"        # Information
RESPONSE_ACTION_UPDATED = "RESPONSE_ACTION_UPDATED"    # Information
# Any service
UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"            # Warning
