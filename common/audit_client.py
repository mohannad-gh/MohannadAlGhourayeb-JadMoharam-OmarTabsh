# Client used by every service to send audit events to the Security Audit Logging service
# Omar Tabsh - 202400798
#
# Usage inside any Flask route (after a successful change):
#
#     from common.audit_client import audit_event
#     from common import audit_events as events
#     audit_event(events.ASSET_CREATED, f"Asset #{asset_id} '{name}' created",
#                 events.INFORMATION, user_id=g.current_user["user_id"])
#
# The service name comes from app.config["SERVICE_NAME"].
# Logging is "best effort": if the logging service is down the original request
# still succeeds and a warning is printed in the terminal.

import logging

import requests
from flask import current_app, has_app_context

from common import config
from common.audit_events import INFORMATION

logger = logging.getLogger(__name__)


def send_audit_log(user_id, action, description, severity=INFORMATION,
                   related_service=None, timeout=3):
    """Send one audit event to POST /logs. Returns True if it was stored. Never raises."""
    url = _logs_base_url() + "/logs"
    payload = {
        "user_id": user_id,
        "action": action,
        "description": description,
        "severity": severity,
        "related_service": related_service,
    }
    headers = {config.SERVICE_KEY_HEADER: config.SERVICE_API_KEY}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning("Audit event %s NOT recorded, logging service unreachable at %s: %s",
                       action, url, exc)
        return False
    if response.status_code != 201:
        logger.warning("Audit event %s rejected by logging service (%s): %s",
                       action, response.status_code, response.text[:300])
        return False
    return True


def audit_event(action, description, severity=INFORMATION, user_id=None):
    """Record an audit event on behalf of the service handling the current request."""
    hook = current_app.config.get("AUDIT_HOOK") or send_audit_log
    try:
        return hook(user_id=user_id, action=action, description=description,
                    severity=severity, related_service=current_app.config["SERVICE_NAME"])
    except Exception:  # an audit failure must never break the main operation
        logger.exception("Audit hook failed for action %s", action)
        return False


def _logs_base_url():
    if has_app_context() and current_app.config.get("LOGS_SERVICE_URL"):
        return current_app.config["LOGS_SERVICE_URL"].rstrip("/")
    return config.service_url("logs")
