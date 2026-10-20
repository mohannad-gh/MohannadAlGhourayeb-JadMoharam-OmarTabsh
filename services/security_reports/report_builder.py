# Service 6 - Security Reports: the calculations behind each report
# Omar Tabsh - 202400798
#
# Every number is computed from the records returned by the source services.
# Nothing is stored or hard-coded. Several field names are accepted for the
# teammates' records (e.g. "criticality_level" or "criticality") so that a small
# naming difference does not silently break a report.

from collections import Counter

from common.audit_events import LOGIN_FAILED, LOGIN_SUCCESS, UNAUTHORIZED_ACCESS

SEVERITY_LEVELS = ("Low", "Medium", "High", "Critical")
INCIDENT_STATUSES = ("Open", "Under Investigation", "Mitigated", "Resolved", "Closed")
# "Open incidents" = incidents that are not resolved yet
UNRESOLVED_INCIDENT_STATUSES = ("Open", "Under Investigation", "Mitigated")
VULNERABILITY_STATUSES = ("Open", "Under Investigation", "In Progress", "Resolved", "Closed")
THREAT_TYPES = ("IP Address", "Domain", "File Hash", "Malware Signature", "Other")
RECENT_THREATS_LIMIT = 5
TOP_ACTIONS_LIMIT = 5


def field(record, *names):
    """Return the first non-empty value among the given field names."""
    for name in names:
        value = record.get(name)
        if value not in (None, ""):
            return value
    return None


def count_by(records, names, known_values=()):
    """Count records per value of a field. Known values always appear (with 0 if absent)."""
    counts = {value: 0 for value in known_values}
    canonical = {value.lower(): value for value in known_values}
    for record in records:
        raw = field(record, *names)
        if raw is None:
            key = "Unknown"
        else:
            text = str(raw).strip()
            key = canonical.get(text.lower(), text)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _is(value, expected):
    return value is not None and str(value).strip().lower() == expected.lower()


INCIDENT_SEVERITY = ("severity", "severity_level")
INCIDENT_STATUS = ("status",)
ASSET_TYPE = ("asset_type", "type")
ASSET_CRITICALITY = ("criticality_level", "criticality")
VULN_SEVERITY = ("severity_level", "severity")
VULN_STATUS = ("status",)


class ReportGenerator:

    @staticmethod
    def summary(users, assets, incidents, threats):
        open_incidents = [incident for incident in incidents
                          if any(_is(field(incident, *INCIDENT_STATUS), status)
                                 for status in UNRESOLVED_INCIDENT_STATUSES)]
        critical_threats = [threat for threat in threats if _is(threat.get("severity"), "Critical")]
        return {
            "users": len(users),
            "assets": len(assets),
            "open_incidents": len(open_incidents),
            "critical_threats": len(critical_threats),
            "definitions": {
                "open_incidents": f"incidents with status {', '.join(UNRESOLVED_INCIDENT_STATUSES)}",
                "critical_threats": "threat indicators with severity Critical",
            },
        }

    @staticmethod
    def incidents(incidents):
        return {
            "total_incidents": len(incidents),
            "incidents_by_severity": count_by(incidents, INCIDENT_SEVERITY, SEVERITY_LEVELS),
            "incidents_by_status": count_by(incidents, INCIDENT_STATUS, INCIDENT_STATUSES),
        }

    @staticmethod
    def assets(assets):
        critical = [asset for asset in assets if _is(field(asset, *ASSET_CRITICALITY), "Critical")]
        return {
            "total_assets": len(assets),
            "critical_assets": len(critical),
            "critical_asset_list": [
                {"asset_id": field(asset, "asset_id", "id"), "asset_name": field(asset, "asset_name", "name")}
                for asset in critical],
            "assets_by_type": count_by(assets, ASSET_TYPE),
            "assets_by_criticality": count_by(assets, ASSET_CRITICALITY, SEVERITY_LEVELS),
        }

    @staticmethod
    def threats(threats):
        newest_first = sorted(threats, key=lambda t: (t.get("date_added") or "", t.get("threat_id") or 0),
                              reverse=True)
        return {
            "total_threats": len(threats),
            "threats_by_severity": count_by(threats, ("severity",), SEVERITY_LEVELS),
            "threats_by_type": count_by(threats, ("threat_type",), THREAT_TYPES),
            "recently_added_threats": [
                {key: threat.get(key) for key in
                 ("threat_id", "threat_type", "threat_value", "severity", "source", "date_added")}
                for threat in newest_first[:RECENT_THREATS_LIMIT]],
        }

    @staticmethod
    def vulnerabilities(vulnerabilities):
        critical = [vuln for vuln in vulnerabilities if _is(field(vuln, *VULN_SEVERITY), "Critical")]
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities_by_severity": count_by(vulnerabilities, VULN_SEVERITY, SEVERITY_LEVELS),
            "vulnerabilities_by_status": count_by(vulnerabilities, VULN_STATUS, VULNERABILITY_STATUSES),
            "critical_vulnerabilities": len(critical),
            "critical_vulnerability_list": [
                {"vulnerability_id": field(vuln, "vulnerability_id", "id"),
                 "title": field(vuln, "title", "vulnerability_title"),
                 "cve_id": field(vuln, "cve_id", "cve_identifier", "cve"),
                 "status": field(vuln, *VULN_STATUS)}
                for vuln in critical],
        }

    @staticmethod
    def activity(logs):
        actions = Counter(str(log.get("action")) for log in logs if log.get("action"))
        successful = actions.get(LOGIN_SUCCESS, 0)
        failed = actions.get(LOGIN_FAILED, 0)
        top = sorted(actions.items(), key=lambda item: (-item[1], item[0]))[:TOP_ACTIONS_LIMIT]
        return {
            "total_user_activities": len(logs),
            "login_attempts": successful + failed,
            "successful_logins": successful,
            "failed_login_attempts": failed,
            "unauthorized_access_attempts": actions.get(UNAUTHORIZED_ACCESS, 0),
            "most_performed_actions": [{"action": action, "count": count} for action, count in top],
            "activities_by_severity": count_by(logs, ("severity",),
                                               ("Information", "Warning", "Error", "Critical")),
        }
