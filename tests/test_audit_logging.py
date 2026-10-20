# Tests for Service 5 - Security Audit Logging
# Omar Tabsh - 202400798

import sqlite3

import pytest

from common import config
from common.roles import ADMIN, ANALYST, AUDITOR, USER
from services.audit_logging.app import create_app

SERVICE_HEADERS = {config.SERVICE_KEY_HEADER: config.SERVICE_API_KEY}


def event(**overrides):
    body = {"user_id": 7, "action": "LOGIN_SUCCESS", "description": "User 'jdoe' logged in",
            "severity": "Information", "related_service": "Users"}
    body.update(overrides)
    return body


@pytest.fixture
def client(db_path):
    return create_app({"DATABASE_PATH": db_path, "TESTING": True}).test_client()


def store(client, **overrides):
    response = client.post("/logs", json=event(**overrides), headers=SERVICE_HEADERS)
    assert response.status_code == 201, response.json
    return response.json["data"]


def test_service_creates_log_with_server_fields(client):
    log = store(client)
    assert log["log_id"] == 1
    assert log["timestamp"]
    assert log["action"] == "LOGIN_SUCCESS"


def test_failed_login_with_unknown_user(client):
    log = store(client, user_id=None, action="login_failed", severity="warning",
                description="Failed login for unknown username 'ghost'")
    assert log["user_id"] is None
    assert (log["action"], log["severity"]) == ("LOGIN_FAILED", "Warning")


def test_admin_can_create_log_but_others_cannot(client, auth):
    assert client.post("/logs", json=event(), headers=auth(ADMIN)).status_code == 201
    for role in (ANALYST, AUDITOR, USER):
        assert client.post("/logs", json=event(), headers=auth(role)).status_code == 403
    assert client.post("/logs", json=event()).status_code == 401
    wrong_key = {config.SERVICE_KEY_HEADER: "guess"}
    assert client.post("/logs", json=event(), headers=wrong_key).status_code == 401


def test_create_log_validation(client):
    def post(body):
        return client.post("/logs", json=body, headers=SERVICE_HEADERS)

    assert post(event(severity="Panic")).status_code == 400
    assert post(event(related_service="Coffee Machine")).status_code == 400
    assert post(event(action="logged in!")).status_code == 400
    assert post(event(description="")).status_code == 400
    assert post(event(user_id="7")).status_code == 400
    assert post(event(user_id=True)).status_code == 400
    assert post(event(timestamp="2020-01-01 00:00:00")).json["errors"]["timestamp"]
    body = event()
    del body["user_id"]
    assert post(body).status_code == 400
    assert client.post("/logs", data="x", headers=SERVICE_HEADERS).status_code == 400


def test_permission_violations_are_logged_locally(client, auth):
    client.get("/logs", headers=auth(USER))
    client.delete("/logs/1", headers=auth(ANALYST))
    logs = client.get("/logs", headers=auth(ADMIN)).json["data"]
    violations = [log for log in logs if log["action"] == "UNAUTHORIZED_ACCESS"]
    assert len(violations) == 2
    assert {log["user_id"] for log in violations} == {2, 3}
    assert all(log["related_service"] == "Audit Logging" for log in violations)


def test_get_all_permissions(client, auth):
    store(client)
    assert client.get("/logs", headers=auth(ADMIN)).status_code == 200
    assert client.get("/logs", headers=auth(AUDITOR)).status_code == 200
    assert client.get("/logs", headers=auth(ANALYST)).status_code == 403
    assert client.get("/logs", headers=auth(USER)).status_code == 403


def test_get_specific_log(client, auth):
    log_id = store(client)["log_id"]
    for role in (ADMIN, AUDITOR, ANALYST):
        response = client.get(f"/logs/{log_id}", headers=auth(role))
        assert response.status_code == 200
        assert response.json["data"]["log_id"] == log_id
    assert client.get(f"/logs/{log_id}", headers=auth(USER)).status_code == 403
    assert client.get("/logs/999", headers=auth(ADMIN)).status_code == 404
    assert client.get("/logs/abc", headers=auth(ADMIN)).status_code == 400


def test_search_logs(client, auth):
    store(client, user_id=7, action="LOGIN_SUCCESS")
    store(client, user_id=7, action="LOGIN_FAILED", severity="Warning")
    store(client, user_id=9, action="THREAT_CREATED", related_service="Threat Intelligence")
    store(client, user_id=9, action="THREAT_DELETED", severity="Warning",
          related_service="Threat Intelligence")
    today = store(client)["timestamp"][:10]

    def search(query, role=ADMIN):
        return client.get(f"/logs/search?{query}", headers=auth(role))

    assert search("user_id=9").json["count"] == 2
    assert search("action=login_failed").json["count"] == 1
    assert search("severity=Warning").json["count"] == 2
    assert search("related_service=threat intelligence").json["count"] == 2
    assert search("user_id=7&severity=Information").json["count"] == 2
    assert search(f"date={today}").json["count"] == 5
    assert search("date=2000-01-01").json["count"] == 0
    assert search(f"date_from=2000-01-01&date_to={today}").json["count"] == 5
    assert search("date=20-10-2026").status_code == 400
    assert search("date_from=2026-12-01&date_to=2026-01-01").status_code == 400
    assert search("").status_code == 400
    assert search("colour=red").status_code == 400
    assert search("user_id=9", AUDITOR).status_code == 200
    assert search("user_id=9", ANALYST).status_code == 200
    assert search("user_id=9", USER).status_code == 403


def test_logs_by_user(client, auth):
    store(client, user_id=7)
    store(client, user_id=7, action="LOGIN_FAILED", severity="Warning")
    store(client, user_id=8)
    response = client.get("/logs/user/7", headers=auth(AUDITOR))
    assert response.status_code == 200
    assert response.json["count"] == 2
    assert {log["user_id"] for log in response.json["data"]} == {7}

    empty = client.get("/logs/user/555", headers=auth(ADMIN))
    assert empty.status_code == 200
    assert empty.json["data"] == []
    assert empty.json["message"] == "No log records found for user 555"
    assert client.get("/logs/user/x", headers=auth(ADMIN)).status_code == 400
    assert client.get("/logs/user/7", headers=auth(ANALYST)).status_code == 403


def test_delete_log_records_the_deletion(client, auth):
    log_id = store(client)["log_id"]
    response = client.delete(f"/logs/{log_id}", headers=auth(ADMIN))
    assert response.status_code == 200
    assert client.get(f"/logs/{log_id}", headers=auth(ADMIN)).status_code == 404
    deletion = client.get("/logs/search?action=LOG_DELETED", headers=auth(ADMIN)).json["data"]
    assert len(deletion) == 1
    assert deletion[0]["user_id"] == 1
    assert f"#{log_id}" in deletion[0]["description"]
    assert client.delete("/logs/999", headers=auth(ADMIN)).status_code == 404


@pytest.mark.parametrize("role", [ANALYST, AUDITOR, USER])
def test_unauthorized_delete(client, auth, role):
    log_id = store(client)["log_id"]
    assert client.delete(f"/logs/{log_id}", headers=auth(role)).status_code == 403
    assert client.get(f"/logs/{log_id}", headers=auth(ADMIN)).status_code == 200


def test_logs_cannot_be_modified(client, auth, db_path):
    original = store(client)
    response = client.put(f"/logs/{original['log_id']}", json={"description": "tampered"},
                          headers=auth(ADMIN))
    assert response.status_code == 405
    assert client.patch(f"/logs/{original['log_id']}", json={}, headers=auth(ADMIN)).status_code == 405

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE logs SET description = 'tampered' WHERE log_id = ?", (original["log_id"],))

    after = client.get(f"/logs/{original['log_id']}", headers=auth(ADMIN)).json["data"]
    assert after == original
    blocked = client.get("/logs/search?action=UNAUTHORIZED_ACCESS", headers=auth(ADMIN)).json["data"]
    assert len(blocked) == 2 and blocked[0]["user_id"] == 1
