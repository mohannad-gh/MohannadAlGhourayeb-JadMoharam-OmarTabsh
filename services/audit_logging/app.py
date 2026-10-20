# Service 5 - Security Audit Logging Service (port 5005)
# Omar Tabsh - 202400798
#
# Run from the project root:   python -m services.audit_logging.app
# Start this service FIRST: every other service sends its audit events here.

from flask import Flask

from common import config
from common.app_setup import configure_app
from common.audit_events import LOGS_SERVICE
from services.audit_logging.repository import AuditLogRepository
from services.audit_logging.routes import logs_bp

DEVELOPER = "Omar Tabsh"


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(SERVICE_NAME=LOGS_SERVICE, DATABASE_PATH=config.DATABASE_PATH)
    app.config.update(overrides or {})

    repository = AuditLogRepository(app.config["DATABASE_PATH"])
    repository.create_table()
    app.extensions["log_repository"] = repository

    # This service stores its own events (e.g. permission violations) directly,
    # instead of sending an HTTP request to itself.
    def store_locally(user_id, action, description, severity, related_service):
        repository.add({"user_id": user_id, "action": action, "description": description,
                        "severity": severity, "related_service": related_service})
        return True

    app.config["AUDIT_HOOK"] = store_locally

    app.register_blueprint(logs_bp, url_prefix=config.TABSH_ROUTE_PREFIX or None)
    configure_app(app, DEVELOPER)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=config.SERVICE_PORTS["logs"])
