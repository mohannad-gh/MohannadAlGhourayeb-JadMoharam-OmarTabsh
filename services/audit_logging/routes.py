# Service 5 - Security Audit Logging: REST API routes
# Omar Tabsh - 202400798

from flask import Blueprint, current_app, request

from common.app_setup import read_json_object
from common.audit_client import audit_event
from common.audit_events import LOG_DELETED, LOGS_SERVICE, UNAUTHORIZED_ACCESS, WARNING
from common.auth import AuthenticationError, current_user_id, decode_token, get_bearer_token, require_roles
from common.responses import error, parse_positive_int, success
from common.roles import ADMIN, ANALYST, AUDITOR
from services.audit_logging.models import LogValidator, ValidationError

logs_bp = Blueprint("logs", __name__)

# Permissions, taken from the Service 5 "Authorization Requirements" table.
# POST /logs is also open to other services that send the shared X-Service-Key header.
CAN_CREATE = (ADMIN,)
CAN_VIEW_ALL = (ADMIN, AUDITOR)
CAN_VIEW_ONE = (ADMIN, AUDITOR, ANALYST)
CAN_SEARCH = (ADMIN, AUDITOR, ANALYST)
CAN_VIEW_BY_USER = (ADMIN, AUDITOR)
CAN_DELETE = (ADMIN,)


def _repository():
    return current_app.extensions["log_repository"]


def _invalid_id():
    return error("Log ID must be a positive integer", 400)


# Create Log Record - route developed by Omar Tabsh
@logs_bp.post("/logs")
@require_roles(*CAN_CREATE, allow_service=True)
def create_log():
    payload = read_json_object()
    if payload is None:
        return error("Request body must be a JSON object", 400)
    try:
        entry = LogValidator.validate_new(payload)
    except ValidationError as exc:
        return error("Invalid log record", 400, exc.errors)

    created = _repository().add(entry)
    return success(created, "Log record created successfully", 201)


# Retrieve All Logs - route developed by Omar Tabsh
@logs_bp.get("/logs")
@require_roles(*CAN_VIEW_ALL)
def get_all_logs():
    logs = _repository().get_all()
    return success(logs, count=len(logs))


# Search Logs - route developed by Omar Tabsh
@logs_bp.get("/logs/search")
@require_roles(*CAN_SEARCH)
def search_logs():
    try:
        filters = LogValidator.validate_search(request.args)
    except ValidationError as exc:
        return error("Invalid search filters", 400, exc.errors)
    logs = _repository().search(**filters)
    return success(logs, f"{len(logs)} log record(s) matched the search",
                   count=len(logs), filters=filters)


# Retrieve Logs By User - route developed by Omar Tabsh
@logs_bp.get("/logs/user/<user_id>")
@require_roles(*CAN_VIEW_BY_USER)
def get_logs_by_user(user_id):
    user_id = parse_positive_int(user_id)
    if user_id is None:
        return error("User ID must be a positive integer", 400)
    logs = _repository().get_by_user(user_id)
    message = (f"{len(logs)} log record(s) found for user {user_id}" if logs
               else f"No log records found for user {user_id}")
    return success(logs, message, count=len(logs), user_id=user_id)


# Retrieve Specific Log - route developed by Omar Tabsh
@logs_bp.get("/logs/<log_id>")
@require_roles(*CAN_VIEW_ONE)
def get_log(log_id):
    log_id = parse_positive_int(log_id)
    if log_id is None:
        return _invalid_id()
    log = _repository().get_by_id(log_id)
    if log is None:
        return error(f"Log with ID {log_id} not found", 404)
    return success(log)


# Delete Logs - route developed by Omar Tabsh
@logs_bp.delete("/logs/<log_id>")
@require_roles(*CAN_DELETE)
def delete_log(log_id):
    log_id = parse_positive_int(log_id)
    if log_id is None:
        return _invalid_id()
    log = _repository().get_by_id(log_id)
    if log is None:
        return error(f"Log with ID {log_id} not found", 404)

    _repository().delete(log_id)
    # The deletion itself is recorded, so removing a log never goes unnoticed
    _repository().add({
        "user_id": current_user_id(),
        "action": LOG_DELETED,
        "description": (f"Audit log #{log_id} was deleted. Original record: action={log['action']}, "
                        f"user_id={log['user_id']}, timestamp={log['timestamp']}, "
                        f"service={log['related_service']}, description={log['description'][:200]}"),
        "severity": WARNING,
        "related_service": LOGS_SERVICE,
    })
    return success(log, f"Log record {log_id} deleted successfully")


# Logs can never be edited: PUT/PATCH are rejected and the attempt is recorded
# Route developed by Omar Tabsh
@logs_bp.route("/logs/<log_id>", methods=["PUT", "PATCH"])
def reject_log_modification(log_id):
    try:
        user_id = decode_token(get_bearer_token())["user_id"]
    except AuthenticationError:
        user_id = None
    audit_event(UNAUTHORIZED_ACCESS,
                f"Blocked attempt to modify audit log #{log_id} with {request.method} "
                "(audit logs are immutable)", WARNING, user_id=user_id)
    return error("Audit log records are immutable and cannot be modified", 405)
