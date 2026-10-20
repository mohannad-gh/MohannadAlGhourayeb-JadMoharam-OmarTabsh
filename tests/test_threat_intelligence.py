# Tests for Service 4 - Threat Intelligence
# Omar Tabsh - 202400798

import sqlite3

import pytest

from common.auth import create_token
from common.roles import ADMIN, ANALYST, AUDITOR, USER
from services.threat_intelligence.app import create_app

IP_THREAT = {"threat_type": "IP Address", "threat_value": "185.220.101.45",
             "description": "Tor exit node used in brute-force attempts", "severity": "High",
             "source": "AbuseIPDB"}
DOMAIN_THREAT = {"threat_type": "Domain", "threat_value": "Secure-Login-Paypa1.com",
                 "description": "Phishing domain imitating PayPal", "severity": "Critical",
                 "source": "PhishTank"}
HASH_THREAT = {"threat_type": "File Hash", "threat_value": "44d88612fea8a8f36de82e1278abb02f",
               "description": "EICAR test file MD5", "severity": "Medium", "source": "VirusTotal"}


@pytest.fixture
def client(db_path, audit):
    return create_app({"DATABASE_PATH": db_path, "AUDIT_HOOK": audit, "TESTING": True}).test_client()


def add(client, auth, body):
    return client.post("/threats", json=body, headers=auth(ADMIN))


def test_admin_adds_each_threat_type(client, auth, audit):
    bodies = [IP_THREAT, DOMAIN_THREAT, HASH_THREAT,
              {"threat_type": "Malware Signature", "threat_value": "Trojan.GenericKD.4652",
               "description": "Emotet loader signature", "severity": "High", "source": "Internal SOC"},
              {"threat_type": "other indicators", "threat_value": "User-Agent: sqlmap/1.7",
               "description": "Automated SQL injection scanner", "severity": "low", "source": "WAF"}]
    for body in bodies:
        response = add(client, auth, body)
        assert response.status_code == 201, response.json
        assert response.json["data"]["date_added"]
    assert response.json["data"]["threat_type"] == "Other"
    assert response.json["data"]["severity"] == "Low"
    assert audit.actions().count("THREAT_CREATED") == 5
    assert audit.events[0]["user_id"] == 1
    assert audit.events[0]["related_service"] == "Threat Intelligence"


def test_values_are_normalised(client, auth):
    data = add(client, auth, DOMAIN_THREAT).json["data"]
    assert data["threat_value"] == "secure-login-paypa1.com"
    data = add(client, auth, {**HASH_THREAT, "threat_value": HASH_THREAT["threat_value"].upper()}).json
    assert data["data"]["threat_value"] == HASH_THREAT["threat_value"]


@pytest.mark.parametrize("threat_type, value", [
    ("IP Address", "192.168.1"),
    ("IP Address", "300.1.1.1"),
    ("IP Address", "not-an-ip"),
    ("Domain", "http://evil.com/login"),
    ("Domain", "evil"),
    ("Domain", "-bad-.com"),
    ("File Hash", "12345"),
    ("File Hash", "z" * 32),
    ("Malware Signature", "ab"),
])
def test_invalid_values_are_rejected(client, auth, threat_type, value):
    response = add(client, auth, {**IP_THREAT, "threat_type": threat_type, "threat_value": value})
    assert response.status_code == 400
    assert response.json["status"] == "error"
    assert "threat_value" in response.json["errors"]


def test_valid_ipv6_and_sha256_accepted(client, auth):
    assert add(client, auth, {**IP_THREAT, "threat_value": "2001:db8::1"}).status_code == 201
    assert add(client, auth, {**HASH_THREAT, "threat_value": "a" * 64}).status_code == 201


def test_missing_fields_and_bad_choices(client, auth):
    response = add(client, auth, {"threat_type": "Planet", "severity": "Extreme"})
    assert response.status_code == 400
    errors = response.json["errors"]
    assert {"threat_type", "threat_value", "severity", "description", "source"} <= set(errors)
    assert client.post("/threats", data="not json", headers=auth(ADMIN)).status_code == 400
    assert add(client, auth, {**IP_THREAT, "risk": 9}).status_code == 400


def test_duplicate_indicator_rejected(client, auth):
    first = add(client, auth, DOMAIN_THREAT).json["data"]
    response = add(client, auth, {**DOMAIN_THREAT, "threat_value": "SECURE-login-paypa1.com.",
                                  "description": "same domain again"})
    assert response.status_code == 409
    assert response.json["errors"]["existing_threat_id"] == first["threat_id"]
    # Same value but a different type is a different indicator
    assert add(client, auth, {**DOMAIN_THREAT, "threat_type": "Other"}).status_code == 201


def test_database_unique_constraint(client, auth, db_path):
    add(client, auth, IP_THREAT)
    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(db_path) as conn:
            conn.execute("INSERT INTO threats (threat_type, threat_value, description, severity, source, "
                         "date_added) VALUES ('IP Address', '185.220.101.45', 'x', 'Low', 'x', 'now')")


def test_get_all_and_by_id(client, auth):
    first = add(client, auth, IP_THREAT).json["data"]
    add(client, auth, DOMAIN_THREAT)
    for role in (ADMIN, ANALYST, AUDITOR):
        response = client.get("/threats", headers=auth(role))
        assert response.status_code == 200
        assert response.json["count"] == 2
    response = client.get(f"/threats/{first['threat_id']}", headers=auth(AUDITOR))
    assert response.status_code == 200
    assert response.json["data"]["threat_value"] == "185.220.101.45"
    assert client.get("/threats/999", headers=auth(ADMIN)).status_code == 404
    assert client.get("/threats/abc", headers=auth(ADMIN)).status_code == 400
    assert client.get("/threats/0", headers=auth(ADMIN)).status_code == 400


def test_search_filters(client, auth):
    for body in (IP_THREAT, DOMAIN_THREAT, HASH_THREAT,
                 {**IP_THREAT, "threat_value": "45.155.205.233", "severity": "Critical"}):
        add(client, auth, body)

    def search(query, role=ADMIN):
        return client.get(f"/threats/search?{query}", headers=auth(role))

    assert search("threat_type=ip address").json["count"] == 2
    assert search("severity=Critical").json["count"] == 2
    assert search("threat_type=IP Address&severity=Critical").json["count"] == 1
    assert search("threat_value=paypa1").json["count"] == 1
    assert search("source=virus").json["count"] == 1
    assert search("source=nothing-matches").json["count"] == 0
    assert search("threat_value=%25").json["count"] == 0          # "%" is matched literally
    assert search("severity=Extreme").status_code == 400
    assert search("").status_code == 400
    assert search("colour=red").status_code == 400
    assert search("severity=High", ANALYST).status_code == 200


def test_update_threat(client, auth, audit):
    threat = add(client, auth, IP_THREAT).json["data"]
    response = client.put(f"/threats/{threat['threat_id']}", headers=auth(ADMIN),
                          json={"severity": "Critical", "source": "CrowdStrike Falcon",
                                "description": "Confirmed C2 server"})
    assert response.status_code == 200
    data = response.json["data"]
    assert (data["severity"], data["source"], data["description"]) == \
        ("Critical", "CrowdStrike Falcon", "Confirmed C2 server")
    assert data["last_updated"]
    assert response.json["previous_values"]["severity"] == "High"
    assert "severity: 'High' -> 'Critical'" in audit.events[-1]["description"]


def test_update_validation(client, auth):
    threat_id = add(client, auth, IP_THREAT).json["data"]["threat_id"]
    url = f"/threats/{threat_id}"
    assert client.put(url, headers=auth(ADMIN), json={"severity": "Huge"}).status_code == 400
    assert client.put(url, headers=auth(ADMIN), json={"threat_value": "1.1.1.1"}).status_code == 400
    assert client.put(url, headers=auth(ADMIN), json={}).status_code == 400
    assert client.put(url, headers=auth(ADMIN), json={"description": "  "}).status_code == 400
    assert client.put("/threats/999", headers=auth(ADMIN), json={"severity": "Low"}).status_code == 404


def test_delete_threat(client, auth, audit):
    threat_id = add(client, auth, IP_THREAT).json["data"]["threat_id"]
    response = client.delete(f"/threats/{threat_id}", headers=auth(ADMIN))
    assert response.status_code == 200
    assert audit.actions()[-1] == "THREAT_DELETED"
    assert client.get(f"/threats/{threat_id}", headers=auth(ADMIN)).status_code == 404
    assert client.delete(f"/threats/{threat_id}", headers=auth(ADMIN)).status_code == 404


@pytest.mark.parametrize("role", [ANALYST, AUDITOR, USER])
def test_non_admins_cannot_modify(client, auth, audit, role):
    threat_id = add(client, auth, IP_THREAT).json["data"]["threat_id"]
    for response in (client.post("/threats", json=DOMAIN_THREAT, headers=auth(role)),
                     client.put(f"/threats/{threat_id}", json={"severity": "Low"}, headers=auth(role)),
                     client.delete(f"/threats/{threat_id}", headers=auth(role))):
        assert response.status_code == 403
        assert response.json["message"] == "User does not have permission to perform this operation"
    assert audit.actions().count("UNAUTHORIZED_ACCESS") == 3
    assert client.get(f"/threats/{threat_id}", headers=auth(ADMIN)).status_code == 200


def test_role_read_permissions(client, auth, audit):
    add(client, auth, IP_THREAT)
    assert client.get("/threats", headers=auth(USER)).status_code == 403
    assert client.get("/threats/1", headers=auth(USER)).status_code == 403
    assert client.get("/threats/search?severity=High", headers=auth(USER)).status_code == 403
    # Service 4 table: the Auditor may view but not search
    assert client.get("/threats/search?severity=High", headers=auth(AUDITOR)).status_code == 403
    assert audit.events[-1]["user_id"] == 4


def test_authentication_errors(client, audit):
    assert client.get("/threats").status_code == 401
    assert client.get("/threats", headers={"Authorization": "Bearer not.a.token"}).status_code == 401
    assert client.get("/threats", headers={"Authorization": "Basic abc"}).status_code == 401
    expired = create_token(1, "admin_account", ADMIN, expires_minutes=-1)
    response = client.get("/threats", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert "expired" in response.json["message"]
    assert audit.actions() == ["UNAUTHORIZED_ACCESS"] * 4


def test_developer_header_and_json_404(client, auth):
    response = client.get("/nothing-here", headers=auth(ADMIN))
    assert response.status_code == 404
    assert response.json["status"] == "error"
    assert response.headers["X-Developed-By"] == "Omar Tabsh"
