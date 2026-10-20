# Service 6 - Security Reports: REST API routes
# Omar Tabsh - 202400798

from datetime import datetime, timezone

from flask import Blueprint, current_app, request

from common.auth import require_roles
from common.responses import error, success
from common.roles import ADMIN, AUDITOR
from services.security_reports.data_sources import DataSourceError
from services.security_reports.report_builder import ReportGenerator

reports_bp = Blueprint("reports", __name__)

# Service 6 table: Administrator and Auditor can generate all six reports.
# Analysts ("unless explicitly authorized") and Regular Users are denied.
CAN_GENERATE = (ADMIN, AUDITOR)


def _generate(title, source_keys, builder):
    """Fetch the records from every source, then compute the report."""
    clients = current_app.extensions["report_sources"]
    authorization = request.headers.get("Authorization", "")
    records = {}
    try:
        for key in source_keys:
            records[key] = clients[key].fetch_all(authorization)
    except DataSourceError as exc:
        return error(f"Could not generate the {title}: {exc}", exc.status_code,
                     {"source": exc.source_name})

    report = builder(**records)
    report["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report["data_sources"] = [clients[key].describe() for key in source_keys]
    return success(report, f"{title} generated successfully")


# Generate Security Summary Report - route developed by Omar Tabsh
@reports_bp.get("/reports/summary")
@require_roles(*CAN_GENERATE)
def summary_report():
    return _generate("Security Summary Report", ("users", "assets", "incidents", "threats"),
                     ReportGenerator.summary)


# Generate Incident Report - route developed by Omar Tabsh
@reports_bp.get("/reports/incidents")
@require_roles(*CAN_GENERATE)
def incident_report():
    return _generate("Incident Report", ("incidents",), ReportGenerator.incidents)


# Generate Asset Report - route developed by Omar Tabsh
@reports_bp.get("/reports/assets")
@require_roles(*CAN_GENERATE)
def asset_report():
    return _generate("Asset Report", ("assets",), ReportGenerator.assets)


# Generate Threat Report - route developed by Omar Tabsh
@reports_bp.get("/reports/threats")
@require_roles(*CAN_GENERATE)
def threat_report():
    return _generate("Threat Report", ("threats",), ReportGenerator.threats)


# Generate Vulnerability Report - route developed by Omar Tabsh
@reports_bp.get("/reports/vulnerabilities")
@require_roles(*CAN_GENERATE)
def vulnerability_report():
    return _generate("Vulnerability Report", ("vulnerabilities",), ReportGenerator.vulnerabilities)


# Generate Activity Report - route developed by Omar Tabsh
@reports_bp.get("/reports/activity")
@require_roles(*CAN_GENERATE)
def activity_report():
    return _generate("Activity Report", ("logs",), ReportGenerator.activity)
