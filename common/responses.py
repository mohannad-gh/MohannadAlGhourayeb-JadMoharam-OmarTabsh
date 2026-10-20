# Common JSON response format shared by all services
# Omar Tabsh - 202400798
#
# Success: {"status": "success", "message": "...", "data": ...}
# Error:   {"status": "error",   "message": "...", "errors": {...}}   (format from the project document)

from flask import jsonify


def success(data=None, message=None, status_code=200, **extra):
    body = {"status": "success"}
    if message:
        body["message"] = message
    body.update(extra)
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def error(message, status_code, errors=None):
    body = {"status": "error", "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def parse_positive_int(raw_value):
    """Return raw_value as an int if it is a positive whole number, otherwise None."""
    if raw_value is None or not str(raw_value).isdigit():
        return None
    value = int(raw_value)
    return value if value > 0 else None
