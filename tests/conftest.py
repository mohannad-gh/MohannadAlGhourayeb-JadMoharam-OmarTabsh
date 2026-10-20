# Shared pytest fixtures for Omar Tabsh's services
# Omar Tabsh - 202400798

import pytest

from common.auth import create_token
from common.roles import ADMIN, ANALYST, AUDITOR, USER

USER_IDS = {ADMIN: 1, ANALYST: 2, USER: 3, AUDITOR: 4}


class AuditRecorder:
    """Stands in for the logging service in unit tests and remembers every audit event."""

    def __init__(self):
        self.events = []

    def __call__(self, **event):
        self.events.append(event)
        return True

    def actions(self):
        return [event["action"] for event in self.events]


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_security_system.db")


@pytest.fixture
def audit():
    return AuditRecorder()


@pytest.fixture
def tokens():
    return {role: create_token(user_id, f"{role}_account", role) for role, user_id in USER_IDS.items()}


@pytest.fixture
def auth(tokens):
    def headers(role):
        return {"Authorization": f"Bearer {tokens[role]}"}
    return headers
