# End-to-end test: the real Threat, Logging and Reports services talking over HTTP
# Omar Tabsh - 202400798
#
# Each service runs in a background thread on a free port with a temporary database.
# The teammates' services (users, assets, incidents, vulnerabilities) are not part
# of this branch, so the reports that need them are expected to answer 503.

import threading

import pytest
import requests
from werkzeug.serving import make_server

from common.auth import create_token
from common.roles import ADMIN, ANALYST, AUDITOR
from services.audit_logging.app import create_app as create_logs_app
from services.security_reports.app import create_app as create_reports_app
from services.threat_intelligence.app import create_app as create_threats_app


class LiveServer:
    def __init__(self, app):
        self.server = make_server("127.0.0.1", 0, app, threaded=True)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()


@pytest.fixture
def system(tmp_path):
    db_path = str(tmp_path / "integration.db")
    logs = LiveServer(create_logs_app({"DATABASE_PATH": db_path}))
    threats = LiveServer(create_threats_app({"DATABASE_PATH": db_path, "LOGS_SERVICE_URL": logs.url}))
    unused = "http://127.0.0.1:9"   # nothing listens here
    reports = LiveServer(create_reports_app({
        "LOGS_SERVICE_URL": logs.url,
        "SERVICE_URLS": {"threats": threats.url, "logs": logs.url, "users": unused,
                         "assets": unused, "incidents": unused, "vulnerabilities": unused},
    }))
    yield {"logs": logs.url, "threats": threats.url, "reports": reports.url}
    for server in (reports, threats, logs):
        server.stop()


def bearer(role, user_id):
    return {"Authorization": f"Bearer {create_token(user_id, f'{role}_account', role)}"}


ADMIN_H = bearer(ADMIN, 1)
ANALYST_H = bearer(ANALYST, 2)
AUDITOR_H = bearer(AUDITOR, 4)


def test_threat_changes_are_logged_automatically(system):
    created = requests.post(f"{system['threats']}/threats", headers=ADMIN_H, json={
        "threat_type": "IP Address", "threat_value": "45.155.205.233", "description": "Scanner",
        "severity": "High", "source": "AbuseIPDB"}).json()["data"]
    requests.put(f"{system['threats']}/threats/{created['threat_id']}", headers=ADMIN_H,
                 json={"severity": "Critical"})
    denied = requests.delete(f"{system['threats']}/threats/{created['threat_id']}", headers=ANALYST_H)
    assert denied.status_code == 403

    logs = requests.get(f"{system['logs']}/logs/search?related_service=Threat Intelligence",
                        headers=AUDITOR_H).json()["data"]
    actions = sorted(log["action"] for log in logs)
    assert actions == ["THREAT_CREATED", "THREAT_UPDATED", "UNAUTHORIZED_ACCESS"]
    assert {log["user_id"] for log in logs} == {1, 2}


def test_reports_use_live_threat_and_log_data(system):
    for value, severity in (("evil.com", "Critical"), ("bad.org", "Low"), ("phish.net", "Critical")):
        requests.post(f"{system['threats']}/threats", headers=ADMIN_H, json={
            "threat_type": "Domain", "threat_value": value, "description": "test", "severity": severity,
            "source": "PhishTank"})

    threat_report = requests.get(f"{system['reports']}/reports/threats", headers=AUDITOR_H).json()["data"]
    assert threat_report["total_threats"] == 3
    assert threat_report["threats_by_severity"]["Critical"] == 2

    # The report changes when the underlying data changes
    requests.delete(f"{system['threats']}/threats/1", headers=ADMIN_H)
    threat_report = requests.get(f"{system['reports']}/reports/threats", headers=AUDITOR_H).json()["data"]
    assert threat_report["total_threats"] == 2

    activity = requests.get(f"{system['reports']}/reports/activity", headers=ADMIN_H).json()["data"]
    all_logs = requests.get(f"{system['logs']}/logs", headers=ADMIN_H).json()["data"]
    assert activity["total_user_activities"] == len(all_logs)
    top = {item["action"]: item["count"] for item in activity["most_performed_actions"]}
    assert top["THREAT_CREATED"] == 3


def test_report_denied_and_missing_sources(system):
    denied = requests.get(f"{system['reports']}/reports/summary", headers=ANALYST_H)
    assert denied.status_code == 403
    violation = requests.get(f"{system['logs']}/logs/search?related_service=Security Reports",
                             headers=ADMIN_H).json()["data"]
    assert violation[0]["action"] == "UNAUTHORIZED_ACCESS"

    unavailable = requests.get(f"{system['reports']}/reports/assets", headers=ADMIN_H)
    assert unavailable.status_code == 503
    assert "Asset Management" in unavailable.json()["message"]


def test_logging_down_does_not_break_threat_service(tmp_path):
    db_path = str(tmp_path / "alone.db")
    threats = LiveServer(create_threats_app({"DATABASE_PATH": db_path,
                                             "LOGS_SERVICE_URL": "http://127.0.0.1:9"}))
    try:
        response = requests.post(f"{threats.url}/threats", headers=ADMIN_H, json={
            "threat_type": "Domain", "threat_value": "evil.com", "description": "x", "severity": "Low",
            "source": "y"})
        assert response.status_code == 201
    finally:
        threats.stop()
