# Settings applied to every Flask app: JSON error pages and a developer header
# Omar Tabsh - 202400798

from flask import request
from werkzeug.exceptions import HTTPException

from common.responses import error


def configure_app(app, developer):
    """Make every error a JSON response and tag every response with the developer's name."""
    app.json.sort_keys = False

    @app.after_request
    def add_developer_header(response):
        response.headers["X-Developed-By"] = developer
        return response

    @app.errorhandler(404)
    def not_found(_exc):
        return error(f"Endpoint {request.method} {request.path} does not exist", 404)

    @app.errorhandler(405)
    def method_not_allowed(_exc):
        return error(f"Method {request.method} is not allowed on {request.path}", 405)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return error(exc.description, exc.code)

    @app.errorhandler(Exception)
    def unexpected_error(exc):
        app.logger.exception("Unexpected error: %s", exc)
        return error("Internal server error", 500)


def read_json_object():
    """Return the request body as a dict, or None if it is missing or not a JSON object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None
