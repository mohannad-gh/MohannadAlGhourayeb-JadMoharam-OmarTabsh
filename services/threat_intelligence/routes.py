# Service 4 - Threat Intelligence: REST API routes
# Omar Tabsh - 202400798

from flask import Blueprint, current_app, request

from common.app_setup import read_json_object
from common.audit_client import audit_event
from common.audit_events import INFORMATION, THREAT_CREATED, THREAT_DELETED, THREAT_UPDATED, WARNING
from common.auth import current_user_id, require_roles
from common.responses import error, parse_positive_int, success
from common.roles import ADMIN, ANALYST, AUDITOR
from services.threat_intelligence.models import ThreatValidator, ValidationError
from services.threat_intelligence.repository import DuplicateThreatError

threats_bp = Blueprint("threats", __name__)

# Permissions, taken from the Service 4 "Authorization Requirements" table
CAN_MODIFY = (ADMIN,)
CAN_VIEW = (ADMIN, ANALYST, AUDITOR)
# The Service 4 table does not give the Auditor GET /threats/search, while the general
# Auditor role list does. We follow the Service 4 table; if the instructor says the
# Auditor may search, add AUDITOR to this tuple.
CAN_SEARCH = (ADMIN, ANALYST)

SEARCH_FILTERS = ("threat_type", "threat_value", "severity", "source")


def _repository():
    return current_app.extensions["threat_repository"]


def _invalid_id():
    return error("Threat ID must be a positive integer", 400)


def _not_found(threat_id):
    return error(f"Threat with ID {threat_id} not found", 404)


# Add Threat Indicator - route developed by Omar Tabsh
@threats_bp.post("/threats")
@require_roles(*CAN_MODIFY)
def add_threat():
    payload = read_json_object()
    if payload is None:
        return error("Request body must be a JSON object", 400)
    try:
        threat = ThreatValidator.validate_new(payload)
    except ValidationError as exc:
        return error("Invalid threat indicator", 400, exc.errors)

    try:
        created = _repository().add(threat)
    except DuplicateThreatError as exc:
        return error(f"A '{threat['threat_type']}' indicator with value '{threat['threat_value']}' "
                     "already exists", 409, {"existing_threat_id": exc.existing_id})

    audit_event(THREAT_CREATED,
                f"Threat #{created['threat_id']} added: {created['threat_type']} "
                f"'{created['threat_value']}' (severity {created['severity']}, source {created['source']})",
                INFORMATION, user_id=current_user_id())
    return success(created, "Threat indicator added successfully", 201)


# Retrieve All Threat Indicators - route developed by Omar Tabsh
@threats_bp.get("/threats")
@require_roles(*CAN_VIEW)
def get_all_threats():
    threats = _repository().get_all()
    return success(threats, count=len(threats))


# Search Threat Indicators - route developed by Omar Tabsh
@threats_bp.get("/threats/search")
@require_roles(*CAN_SEARCH)
def search_threats():
    unknown = [name for name in request.args if name not in SEARCH_FILTERS]
    if unknown:
        return error(f"Unknown search filter(s): {', '.join(unknown)}. "
                     f"Supported filters: {', '.join(SEARCH_FILTERS)}", 400)

    filters = {}
    for name in SEARCH_FILTERS:
        value = request.args.get(name, "").strip()
        if value:
            filters[name] = value
    if not filters:
        return error(f"Provide at least one search filter: {', '.join(SEARCH_FILTERS)}", 400)

    errors = {}
    if "threat_type" in filters:
        try:
            filters["threat_type"] = ThreatValidator.normalize_type(filters["threat_type"])
        except ValueError as exc:
            errors["threat_type"] = str(exc)
    if "severity" in filters:
        try:
            filters["severity"] = ThreatValidator.normalize_severity(filters["severity"])
        except ValueError as exc:
            errors["severity"] = str(exc)
    if errors:
        return error("Invalid search filter value", 400, errors)

    results = _repository().search(**filters)
    return success(results, f"{len(results)} threat indicator(s) matched the search",
                   count=len(results), filters=filters)


# Retrieve Specific Threat Indicator - route developed by Omar Tabsh
@threats_bp.get("/threats/<threat_id>")
@require_roles(*CAN_VIEW)
def get_threat(threat_id):
    threat_id = parse_positive_int(threat_id)
    if threat_id is None:
        return _invalid_id()
    threat = _repository().get_by_id(threat_id)
    if threat is None:
        return _not_found(threat_id)
    return success(threat)


# Update Threat Information - route developed by Omar Tabsh
@threats_bp.put("/threats/<threat_id>")
@require_roles(*CAN_MODIFY)
def update_threat(threat_id):
    threat_id = parse_positive_int(threat_id)
    if threat_id is None:
        return _invalid_id()
    before = _repository().get_by_id(threat_id)
    if before is None:
        return _not_found(threat_id)

    payload = read_json_object()
    if payload is None:
        return error("Request body must be a JSON object", 400)
    try:
        changes = ThreatValidator.validate_update(payload)
    except ValidationError as exc:
        return error("Invalid threat update", 400, exc.errors)

    updated = _repository().update(threat_id, changes)
    previous = {field: before[field] for field in changes}
    changed_text = "; ".join(f"{field}: '{before[field]}' -> '{updated[field]}'"
                             for field in changes if before[field] != updated[field])
    audit_event(THREAT_UPDATED,
                f"Threat #{threat_id} ({updated['threat_type']} '{updated['threat_value']}') updated: "
                f"{changed_text or 'no values changed'}",
                INFORMATION, user_id=current_user_id())
    return success(updated, "Threat information updated successfully", previous_values=previous)


# Delete Threat Indicator - route developed by Omar Tabsh
@threats_bp.delete("/threats/<threat_id>")
@require_roles(*CAN_MODIFY)
def delete_threat(threat_id):
    threat_id = parse_positive_int(threat_id)
    if threat_id is None:
        return _invalid_id()
    threat = _repository().get_by_id(threat_id)
    if threat is None:
        return _not_found(threat_id)

    _repository().delete(threat_id)
    audit_event(THREAT_DELETED,
                f"Threat #{threat_id} deleted: {threat['threat_type']} '{threat['threat_value']}' "
                f"(severity {threat['severity']}, source {threat['source']})",
                WARNING, user_id=current_user_id())
    return success(threat, f"Threat indicator {threat_id} deleted successfully")
