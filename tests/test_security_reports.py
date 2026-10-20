# Tests for Service 6 - Security Reports (report calculations and access control)
# Omar Tabsh - 202400798
#
# The source services are replaced by FakeSource objects here so the arithmetic can
# be checked exactly. tests/test_integration.py runs the real services over HTTP.

import pytest

from common.roles import ADMIN, ANALYST, AUDITOR, USER
from services.security_reports.app import create_app
from services.security_reports.data_sources import DataSourceError, extract_records

USERS = [{"user_id": i} for i in range(1, 6)]
ASSETS = [
    {"asset_id": 1, "asset_name": "Web Server", "asset_type": "Server", "criticality_level": "Critical"},
    {"asset_id": 2, "asset_name": "HR Laptop", "asset_type": "Workstation", "criticality_level": "Low"},
    {"asset_id": 3, "asset_name": "Payroll DB", "asset_type": "Database", "criticality_level": "critical"},
    {"asset_id": 4, "asset_name": "Mail Server", "asset_type": "Server", "criticality_level": "High"},
]
INCIDENTS = [
    {"incident_id": 1, "severity": "High", "status": "Open"},
    {"incident_id": 2, "severity": "Critical", "status": "Under Investigation"},
    {"incident_id": 3, "severity": "Low", "status": "Closed"},
    {"incident_id": 4, "severity": "High", "status": "Mitigated"},
    {"incident_id": 5, "severity": "Medium", "status": "Resolved"},
]
THREATS = [
    {"threat_id": 1, "threat_type": "IP Address", "threat_value": "1.2.3.4", "severity": "Critical",
     "source": "A", "date_added": "2026-10-01 10:00:00"},
    {"threat_id": 2, "threat_type": "Domain", "threat_value": "evil.com", "severity": "High",
     "source": "B", "date_added": "2026-10-03 10:00:00"},
    {"threat_id": 3, "threat_type": "Domain", "threat_value": "bad.org", "severity": "Critical",
     "source": "C", "date_added": "2026-10-02 10:00:00"},
]
VULNERABILITIES = [
    {"vulnerability_id": 1, "title": "Log4Shell", "cve_id": "CVE-2021-44228", "severity_level": "Critical",
     "status": "Open"},
    {"vulnerability_id": 2, "title": "Weak TLS", "cve_id": "CVE-2014-3566", "severity_level": "Medium",
     "status": "In Progress"},
    {"vulnerability_id": 3, "title": "Old SMB", "cve_id": "CVE-2017-0144", "severity_level": "Critical",
     "status": "Resolved"},
]
LOGS = [
    {"action": "LOGIN_SUCCESS", "severity": "Information"},
    {"action": "LOGIN_SUCCESS", "severity": "Information"},
    {"action": "LOGIN_FAILED", "severity": "Warning"},
    {"action": "LOGIN_FAILED", "severity": "Warning"},
    {"action": "LOGIN_FAILED", "severity": "Warning"},
    {"action": "THREAT_CREATED", "severity": "Information"},
    {"action": "UNAUTHORIZED_ACCESS", "severity": "Warning"},
]


class FakeSource:
    def __init__(self, name, records=None, failure=None):
        self.name = name
        self.records = records
        self.failure = failure
        self.received_authorization = None

    def describe(self):
        return f"{self.name} service (test data)"

    def fetch_all(self, authorization):
        self.received_authorization = authorization
        if self.failure:
            raise self.failure
        return self.records


@pytest.fixture
def app(audit):
    app = create_app({"AUDIT_HOOK": audit, "TESTING": True})
    app.extensions["report_sources"] = {
        "users": FakeSource("Users", USERS), "assets": FakeSource("Assets", ASSETS),
        "incidents": FakeSource("Incidents", INCIDENTS), "threats": FakeSource("Threats", THREATS),
        "vulnerabilities": FakeSource("Vulnerabilities", VULNERABILITIES), "logs": FakeSource("Logs", LOGS),
    }
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def report(client, auth, name, role=ADMIN):
    response = client.get(f"/reports/{name}", headers=auth(role))
    assert response.status_code == 200, response.json
    return response.json["data"]


def test_summary(client, auth, app, tokens):
    data = report(client, auth, "summary")
    assert (data["users"], data["assets"], data["open_incidents"], data["critical_threats"]) == (5, 4, 3, 2)
    assert len(data["data_sources"]) == 4
    # The caller's token is forwarded to the source services
    assert app.extensions["report_sources"]["users"].received_authorization == f"Bearer {tokens[ADMIN]}"


def test_incident_report(client, auth):
    data = report(client, auth, "incidents", AUDITOR)
    assert data["total_incidents"] == 5
    assert data["incidents_by_severity"] == {"Low": 1, "Medium": 1, "High": 2, "Critical": 1}
    assert data["incidents_by_status"] == {"Open": 1, "Under Investigation": 1, "Mitigated": 1,
                                           "Resolved": 1, "Closed": 1}


def test_asset_report(client, auth):
    data = report(client, auth, "assets")
    assert data["total_assets"] == 4
    assert data["critical_assets"] == 2
    assert [asset["asset_name"] for asset in data["critical_asset_list"]] == ["Web Server", "Payroll DB"]
    assert data["assets_by_type"] == {"Server": 2, "Workstation": 1, "Database": 1}


def test_threat_report(client, auth):
    data = report(client, auth, "threats")
    assert data["total_threats"] == 3
    assert data["threats_by_severity"] == {"Low": 0, "Medium": 0, "High": 1, "Critical": 2}
    assert data["threats_by_type"]["Domain"] == 2
    assert data["threats_by_type"]["IP Address"] == 1
    assert [t["threat_id"] for t in data["recently_added_threats"]] == [2, 3, 1]


def test_vulnerability_report(client, auth):
    data = report(client, auth, "vulnerabilities")
    assert data["total_vulnerabilities"] == 3
    assert data["vulnerabilities_by_severity"] == {"Low": 0, "Medium": 1, "High": 0, "Critical": 2}
    assert data["vulnerabilities_by_status"]["In Progress"] == 1
    assert data["critical_vulnerabilities"] == 2
    assert data["critical_vulnerability_list"][0]["cve_id"] == "CVE-2021-44228"


def test_activity_report(client, auth):
    data = report(client, auth, "activity", AUDITOR)
    assert data["total_user_activities"] == 7
    assert data["login_attempts"] == 5
    assert data["failed_login_attempts"] == 3
    assert data["unauthorized_access_attempts"] == 1
    assert data["most_performed_actions"][0] == {"action": "LOGIN_FAILED", "count": 3}


def test_empty_data_gives_zero_counts(client, auth, app):
    app.extensions["report_sources"]["incidents"].records = []
    data = report(client, auth, "incidents")
    assert data["total_incidents"] == 0
    assert set(data["incidents_by_severity"].values()) == {0}


@pytest.mark.parametrize("role", [ANALYST, USER])
@pytest.mark.parametrize("name", ["summary", "incidents", "assets", "threats", "vulnerabilities", "activity"])
def test_reports_denied_for_analyst_and_user(client, auth, audit, role, name):
    response = client.get(f"/reports/{name}", headers=auth(role))
    assert response.status_code == 403
    assert audit.actions() == ["UNAUTHORIZED_ACCESS"]


def test_report_requires_login(client):
    assert client.get("/reports/summary").status_code == 401


def test_unreachable_source_returns_503(client, auth, app):
    app.extensions["report_sources"]["assets"].failure = DataSourceError(
        "Asset Management", "The Asset Management service is not reachable", 503)
    response = client.get("/reports/summary", headers=auth(ADMIN))
    assert response.status_code == 503
    assert response.json["errors"]["source"] == "Asset Management"


def test_extract_records_formats():
    assert extract_records([{"a": 1}]) == [{"a": 1}]
    assert extract_records({"status": "success", "data": [{"a": 1}]}) == [{"a": 1}]
    assert extract_records({"data": {"users": [{"a": 1}]}}) == [{"a": 1}]
    assert extract_records({"users": [{"a": 1}]}) == [{"a": 1}]
    assert extract_records({"message": "hi"}) is None
