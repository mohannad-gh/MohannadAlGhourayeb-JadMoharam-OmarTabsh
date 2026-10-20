# Service 5 - Security Audit Logging: log data rules and input validation
# Omar Tabsh - 202400798

import re
from datetime import datetime

from common.audit_events import LOG_SEVERITIES, RELATED_SERVICES

ACTION_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
CREATE_FIELDS = ("user_id", "action", "description", "severity", "related_service")
SERVER_FIELDS = ("log_id", "timestamp")
SEARCH_FILTERS = ("user_id", "date", "date_from", "date_to", "action", "severity", "related_service")
MAX_DESCRIPTION = 2000


class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


def _match_choice(raw, choices, field):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field} is required")
    for choice in choices:
        if raw.strip().lower() == choice.lower():
            return choice
    raise ValueError(f"{field} must be one of: {', '.join(choices)}")


def _parse_date(raw, field):
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field} must be a date in the format YYYY-MM-DD")


class LogValidator:
    """Checks audit events before they are stored."""

    @staticmethod
    def normalize_action(raw):
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("action is required")
        action = raw.strip().upper()
        if not ACTION_RE.match(action):
            raise ValueError("action must be UPPER_SNAKE_CASE, e.g. LOGIN_FAILED (2-64 characters)")
        return action

    @staticmethod
    def normalize_user_id(raw):
        if raw is None:
            return None
        if isinstance(raw, bool) or not isinstance(raw, int) or raw <= 0:
            raise ValueError("user_id must be a positive integer, or null when the user is unknown")
        return raw

    @classmethod
    def validate_new(cls, payload):
        errors = {}
        for field in payload:
            if field in SERVER_FIELDS:
                errors[field] = f"{field} is assigned by the server and cannot be provided"
            elif field not in CREATE_FIELDS:
                errors[field] = f"Unknown field. Allowed fields: {', '.join(CREATE_FIELDS)}"

        cleaned = {}
        if "user_id" not in payload:
            errors["user_id"] = ("user_id is required (send null when the user is unknown, "
                                 "for example a failed login with a non-existing username)")
        else:
            try:
                cleaned["user_id"] = cls.normalize_user_id(payload["user_id"])
            except ValueError as exc:
                errors["user_id"] = str(exc)

        try:
            cleaned["action"] = cls.normalize_action(payload.get("action"))
        except ValueError as exc:
            errors["action"] = str(exc)

        description = payload.get("description")
        if not isinstance(description, str) or not description.strip():
            errors["description"] = "description is required and must be a non-empty string"
        elif len(description.strip()) > MAX_DESCRIPTION:
            errors["description"] = f"description must be at most {MAX_DESCRIPTION} characters"
        else:
            cleaned["description"] = description.strip()

        for field, choices in (("severity", LOG_SEVERITIES), ("related_service", RELATED_SERVICES)):
            try:
                cleaned[field] = _match_choice(payload.get(field), choices, field)
            except ValueError as exc:
                errors[field] = str(exc)

        if errors:
            raise ValidationError(errors)
        return cleaned

    @classmethod
    def validate_search(cls, args):
        """Turn query parameters into clean search filters."""
        errors = {}
        unknown = [name for name in args if name not in SEARCH_FILTERS]
        if unknown:
            errors["filters"] = (f"Unknown search filter(s): {', '.join(unknown)}. "
                                 f"Supported filters: {', '.join(SEARCH_FILTERS)}")

        raw = {name: args.get(name, "").strip() for name in SEARCH_FILTERS if args.get(name, "").strip()}
        if not raw and not unknown:
            errors["filters"] = f"Provide at least one search filter: {', '.join(SEARCH_FILTERS)}"

        filters = {}
        if "user_id" in raw:
            if raw["user_id"].isdigit() and int(raw["user_id"]) > 0:
                filters["user_id"] = int(raw["user_id"])
            else:
                errors["user_id"] = "user_id must be a positive integer"
        for field in ("date", "date_from", "date_to"):
            if field in raw:
                try:
                    filters[field] = _parse_date(raw[field], field)
                except ValueError as exc:
                    errors[field] = str(exc)
        if "date" in raw and ("date_from" in raw or "date_to" in raw):
            errors["date"] = "Use either date, or date_from/date_to, not both"
        if "date_from" in filters and "date_to" in filters and filters["date_from"] > filters["date_to"]:
            errors["date_from"] = "date_from must be on or before date_to"
        if "action" in raw:
            try:
                filters["action"] = cls.normalize_action(raw["action"])
            except ValueError as exc:
                errors["action"] = str(exc)
        for field, choices in (("severity", LOG_SEVERITIES), ("related_service", RELATED_SERVICES)):
            if field in raw:
                try:
                    filters[field] = _match_choice(raw[field], choices, field)
                except ValueError as exc:
                    errors[field] = str(exc)

        if errors:
            raise ValidationError(errors)
        return filters
