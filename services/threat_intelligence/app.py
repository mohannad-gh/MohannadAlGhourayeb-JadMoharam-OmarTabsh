# Service 4 - Threat Intelligence Service (port 5004)
# Omar Tabsh - 202400798
#
# Run from the project root:   python -m services.threat_intelligence.app

from flask import Flask

from common import config
from common.app_setup import configure_app
from common.audit_events import THREATS_SERVICE
from services.threat_intelligence.repository import ThreatRepository
from services.threat_intelligence.routes import threats_bp

DEVELOPER = "Omar Tabsh"


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(
        SERVICE_NAME=THREATS_SERVICE,
        DATABASE_PATH=config.DATABASE_PATH,
        AUDIT_HOOK=None,          # None -> send events to the Audit Logging service over HTTP
        LOGS_SERVICE_URL=None,    # None -> config.service_url("logs")
    )
    app.config.update(overrides or {})

    repository = ThreatRepository(app.config["DATABASE_PATH"])
    repository.create_table()
    app.extensions["threat_repository"] = repository

    app.register_blueprint(threats_bp, url_prefix=config.TABSH_ROUTE_PREFIX or None)
    configure_app(app, DEVELOPER)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=config.SERVICE_PORTS["threats"])
