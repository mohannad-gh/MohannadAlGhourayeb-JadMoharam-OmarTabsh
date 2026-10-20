# Tokens issued by the Users service with flask_jwt_extended must work on Omar Tabsh's services
# Omar Tabsh - 202400798

import jwt
import pytest
from flask import Flask

from common import config
from common.auth import AuthenticationError, decode_token
from services.threat_intelligence.app import create_app

flask_jwt_extended = pytest.importorskip("flask_jwt_extended")


def users_service_token(user_id, role, refresh=False):
    """A token made exactly like POST /users/login does (identity=str(id), role as a full title)."""
    app = Flask("users-service")
    app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
    flask_jwt_extended.JWTManager(app)
    create = flask_jwt_extended.create_refresh_token if refresh else flask_jwt_extended.create_access_token
    with app.app_context():
        return create(identity=str(user_id), additional_claims={"role": role})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db_path, audit):
    return create_app({"DATABASE_PATH": db_path, "AUDIT_HOOK": audit, "TESTING": True}).test_client()


@pytest.mark.parametrize("title, code", [
    ("Security Administrator", "admin"),
    ("Security Analyst", "analyst"),
    ("Regular User", "user"),
    ("Auditor", "auditor"),
])
def test_role_titles_are_mapped(title, code):
    user = decode_token(users_service_token(12, title))
    assert user["role"] == code
    assert user["user_id"] == 12


def test_users_service_tokens_follow_the_permission_table(client, audit):
    threat = {"threat_type": "Domain", "threat_value": "evil.com", "description": "Phishing",
              "severity": "High", "source": "PhishTank"}
    admin = bearer(users_service_token(1, "Security Administrator"))
    created = client.post("/threats", json=threat, headers=admin)
    assert created.status_code == 201
    assert audit.events[-1]["user_id"] == 1

    assert client.get("/threats", headers=bearer(users_service_token(4, "Auditor"))).status_code == 200
    assert client.get("/threats", headers=bearer(users_service_token(3, "Regular User"))).status_code == 403

    analyst = bearer(users_service_token(2, "Security Analyst"))
    assert client.delete(f"/threats/{created.json['data']['threat_id']}", headers=analyst).status_code == 403
    assert audit.events[-1]["action"] == "UNAUTHORIZED_ACCESS"
    assert audit.events[-1]["user_id"] == 2
    assert "user 2" in audit.events[-1]["description"]


def test_refresh_tokens_are_rejected():
    with pytest.raises(AuthenticationError):
        decode_token(users_service_token(1, "Security Administrator", refresh=True))


def test_unknown_role_or_bad_identity_rejected():
    with pytest.raises(AuthenticationError):
        decode_token(users_service_token(1, "Superuser"))
    with pytest.raises(AuthenticationError):
        decode_token(users_service_token("abc", "Auditor"))


def test_token_signed_with_another_key_rejected():
    forged = jwt.encode({"sub": "1", "role": "Security Administrator", "exp": 4102444800},
                        "not-the-shared-secret", algorithm="HS256")
    with pytest.raises(AuthenticationError):
        decode_token(forged)
