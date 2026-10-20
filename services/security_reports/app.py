# Service 6 - Security Reports Service (port 5006)
# Omar Tabsh - 202400798
#
# Run from the project root:   python -m services.security_reports.app
# This service has no table of its own: every report is computed on request
# from the live data of the other services.

from flask import Flask

from common import config
from common.app_setup import configure_app
from common.audit_events import REPORTS_SERVICE
from services.security_reports.data_sources import build_clients
from services.security_reports.routes import reports_bp

DEVELOPER = "Omar Tabsh"


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(
        SERVICE_NAME=REPORTS_SERVICE,
        AUDIT_HOOK=None,
        LOGS_SERVICE_URL=None,
        SERVICE_URLS={},          # e.g. {"users": "http://127.0.0.1:5001"} to override a source URL
    )
    app.config.update(overrides or {})

    app.extensions["report_sources"] = build_clients(app.config["SERVICE_URLS"])

    app.register_blueprint(reports_bp, url_prefix=config.TABSH_ROUTE_PREFIX or None)
    configure_app(app, DEVELOPER)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=config.SERVICE_PORTS["reports"])
