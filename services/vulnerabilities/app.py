
import os
import re
import math
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

if __package__:
    from .models import db, Vulnerability
else:
    from models import db, Vulnerability


# ==========================================
# 1. FLASK APPLICATION SETUP
# ==========================================

load_dotenv()

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY must be configured")

jwt = JWTManager(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("TEAM_DATABASE_URI", "sqlite:///vulnerabilities.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ==========================================
# 2. VALIDATION AND HELPER FUNCTIONS
# ==========================================

ALLOWED_SEVERITIES = ["Low", "Medium", "High", "Critical"]
ALLOWED_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$")

ALLOWED_FIELDS = {
    "title",
    "description",
    "cve_id",
    "asset_id",
    "severity",
    "cvss_score",
    "status",
    "remediation"
}


def role_can_view_vulnerabilities():
    return get_jwt().get("role") in [
        "Security Administrator",
        "Security Analyst",
        "Auditor"
    ]


def role_can_manage_vulnerabilities():
    return get_jwt().get("role") in [
        "Security Administrator",
        "Security Analyst"
    ]


def role_can_delete_vulnerabilities():
    return get_jwt().get("role") == "Security Administrator"


def vulnerability_to_dict(v):
    return {
        "vulnerability_id": v.id,
        "title": v.title,
        "description": v.description,
        "cve_id": v.cve_id,
        "asset_id": v.asset_id,
        "severity": v.severity,
        "cvss_score": v.cvss_score,
        "status": v.status,
        "remediation": v.remediation,
        "discovered_date": (
            v.discovered_date.isoformat()
            if v.discovered_date else None
        ),
        "updated_date": (
            v.updated_date.isoformat()
            if v.updated_date else None
        )
    }


def validate_vulnerability_data(data, partial=False):

    if not isinstance(data, dict):
        return "A JSON object is required"

    if not data:
        return "At least one vulnerability field is required"

    if any(field not in ALLOWED_FIELDS for field in data):
        return "One or more vulnerability fields are not allowed"

    required_fields = [
        "title",
        "description",
        "asset_id",
        "severity"
    ]

    if not partial:
        for field in required_fields:
            if field not in data or data[field] is None:
                return f"{field} is required"

    for field in ["title", "description", "severity"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return f"{field} must be a non-empty string"

    if "title" in data and len(data["title"].strip()) > 200:
        return "title is too long"

    if "asset_id" in data:
        if type(data["asset_id"]) is not int or data["asset_id"] <= 0:
            return "asset_id must be a positive integer"

    if "severity" in data:
        if data["severity"].strip() not in ALLOWED_SEVERITIES:
            return "Invalid severity level"

    if "status" in data:
        if (
            not isinstance(data["status"], str)
            or data["status"] not in ALLOWED_STATUSES
        ):
            return "Invalid vulnerability status"

    if "cve_id" in data and data["cve_id"] is not None:
        if not isinstance(data["cve_id"], str):
            return "Invalid CVE ID format"

        cve_id = data["cve_id"].strip().upper()

        if cve_id and not CVE_PATTERN.fullmatch(cve_id):
            return "Invalid CVE ID format"

        if len(cve_id) > 30:
            return "Invalid CVE ID format"

    if "cvss_score" in data and data["cvss_score"] is not None:
        score = data["cvss_score"]

        if (
            type(score) not in (int, float)
            or not math.isfinite(score)
            or not 0 <= score <= 10
        ):
            return "CVSS score must be between 0 and 10"

    if "remediation" in data and data["remediation"] is not None:
        if not isinstance(data["remediation"], str):
            return "remediation must be text"

    return None


def duplicate_cve_exists(asset_id, cve_id, exclude_id=None):

    if not cve_id:
        return False

    existing = Vulnerability.query.filter_by(
        asset_id=asset_id,
        cve_id=cve_id
    ).first()

    return existing is not None and existing.id != exclude_id


# ==========================================
# 3. HEALTH CHECK
# GET /health
# ==========================================

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "success",
        "service": "Vulnerability Management",
        "message": "Vulnerability Management Service is running"
    }), 200


# ==========================================
# 4. REGISTER VULNERABILITY
# POST /vulnerabilities
# ==========================================

@app.route("/vulnerabilities", methods=["POST"])
@jwt_required()
def register_vulnerability():

    if not role_can_manage_vulnerabilities():
        return jsonify({
            "message": "You do not have permission to register vulnerabilities"
        }), 403

    data = request.get_json(silent=True)
    error = validate_vulnerability_data(data)

    if error:
        return jsonify({"message": error}), 400

    cve_id = data.get("cve_id")

    if isinstance(cve_id, str):
        cve_id = cve_id.strip().upper() or None

    if duplicate_cve_exists(data["asset_id"], cve_id):
        return jsonify({
            "message": "Vulnerability already exists for this asset"
        }), 409

    remediation = data.get("remediation")

    if isinstance(remediation, str):
        remediation = remediation.strip() or None

    now = datetime.now(timezone.utc)

    new_vulnerability = Vulnerability(
        title=data["title"].strip(),
        description=data["description"].strip(),
        cve_id=cve_id,
        asset_id=data["asset_id"],
        severity=data["severity"].strip(),
        cvss_score=data.get("cvss_score"),
        status=data.get("status", "Open"),
        remediation=remediation,
        discovered_date=now,
        updated_date=now
    )

    try:
        db.session.add(new_vulnerability)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Vulnerability could not be saved"
        }), 409

    return jsonify({
        "message": "Vulnerability registered successfully",
        "vulnerability": vulnerability_to_dict(new_vulnerability)
    }), 201


# ==========================================
# 5. RETRIEVE ALL VULNERABILITIES
# GET /vulnerabilities
# ==========================================

@app.route("/vulnerabilities", methods=["GET"])
@jwt_required()
def get_all_vulnerabilities():

    if not role_can_view_vulnerabilities():
        return jsonify({
            "message": "You do not have permission to view vulnerabilities"
        }), 403

    vulnerabilities = Vulnerability.query.order_by(
        Vulnerability.id
    ).all()

    return jsonify({
        "message": "Vulnerabilities retrieved successfully",
        "total_vulnerabilities": len(vulnerabilities),
        "vulnerabilities": [
            vulnerability_to_dict(v) for v in vulnerabilities
        ]
    }), 200


# ==========================================
# 6. SEARCH VULNERABILITIES
# GET /vulnerabilities/search
# ==========================================

@app.route("/vulnerabilities/search", methods=["GET"])
@jwt_required()
def search_vulnerabilities():

    if not role_can_view_vulnerabilities():
        return jsonify({
            "message": "You do not have permission to search vulnerabilities"
        }), 403

    allowed_filters = {
        "title",
        "cve_id",
        "asset_id",
        "severity",
        "status"
    }

    if not request.args:
        return jsonify({
            "message": "At least one search filter is required"
        }), 400

    for field in request.args:
        if field not in allowed_filters:
            return jsonify({
                "message": f"Unsupported search filter: {field}"
            }), 400

        if len(request.args.getlist(field)) > 1:
            return jsonify({
                "message": f"Duplicate search filter: {field}"
            }), 400

    query = Vulnerability.query

    # Partial title search
    if "title" in request.args:
        title = request.args["title"].strip()

        if not title:
            return jsonify({
                "message": "title cannot be empty"
            }), 400

        query = query.filter(
            Vulnerability.title.ilike(f"%{title}%")
        )

    # CVE ID search
    if "cve_id" in request.args:
        cve_id = request.args["cve_id"].strip().upper()

        if not cve_id or not CVE_PATTERN.fullmatch(cve_id):
            return jsonify({
                "message": "Invalid CVE ID format"
            }), 400

        query = query.filter_by(cve_id=cve_id)

    # Affected asset search
    if "asset_id" in request.args:
        try:
            asset_id = int(request.args["asset_id"])

            if asset_id <= 0:
                raise ValueError

        except ValueError:
            return jsonify({
                "message": "asset_id must be a positive integer"
            }), 400

        query = query.filter_by(asset_id=asset_id)

    # Severity search
    if "severity" in request.args:
        severity = request.args["severity"].strip()

        if severity not in ALLOWED_SEVERITIES:
            return jsonify({
                "message": "Invalid severity level"
            }), 400

        query = query.filter_by(severity=severity)

    # Remediation status search
    if "status" in request.args:
        status = request.args["status"].strip()

        if status not in ALLOWED_STATUSES:
            return jsonify({
                "message": "Invalid vulnerability status"
            }), 400

        query = query.filter_by(status=status)

    results = query.order_by(Vulnerability.id).all()

    return jsonify({
        "message": "Vulnerability search completed successfully",
        "total_results": len(results),
        "vulnerabilities": [
            vulnerability_to_dict(v) for v in results
        ]
    }), 200


# ==========================================
# 7. RETRIEVE VULNERABILITY BY ID
# GET /vulnerabilities/<id>
# ==========================================

@app.route("/vulnerabilities/<int:id>", methods=["GET"])
@jwt_required()
def get_vulnerability_by_id(id):

    if not role_can_view_vulnerabilities():
        return jsonify({
            "message": "You do not have permission to view vulnerabilities"
        }), 403

    vulnerability = db.session.get(Vulnerability, id)

    if not vulnerability:
        return jsonify({
            "message": "Vulnerability not found"
        }), 404

    return jsonify({
        "message": "Vulnerability retrieved successfully",
        "vulnerability": vulnerability_to_dict(vulnerability)
    }), 200


# ==========================================
# 8. UPDATE VULNERABILITY
# PUT /vulnerabilities/<id>
# ==========================================

@app.route("/vulnerabilities/<int:id>", methods=["PUT"])
@jwt_required()
def update_vulnerability(id):

    if not role_can_manage_vulnerabilities():
        return jsonify({
            "message": "You do not have permission to update vulnerabilities"
        }), 403

    vulnerability = db.session.get(Vulnerability, id)

    if not vulnerability:
        return jsonify({
            "message": "Vulnerability not found"
        }), 404

    data = request.get_json(silent=True)
    error = validate_vulnerability_data(data, partial=True)

    if error:
        return jsonify({"message": error}), 400

    new_asset_id = data.get("asset_id", vulnerability.asset_id)
    new_cve_id = data.get("cve_id", vulnerability.cve_id)

    if isinstance(new_cve_id, str):
        new_cve_id = new_cve_id.strip().upper() or None

    if duplicate_cve_exists(
        new_asset_id,
        new_cve_id,
        exclude_id=id
    ):
        return jsonify({
            "message": "Vulnerability already exists for this asset"
        }), 409

    if "title" in data:
        vulnerability.title = data["title"].strip()

    if "description" in data:
        vulnerability.description = data["description"].strip()

    if "cve_id" in data:
        vulnerability.cve_id = new_cve_id

    if "asset_id" in data:
        vulnerability.asset_id = new_asset_id

    if "severity" in data:
        vulnerability.severity = data["severity"].strip()

    if "cvss_score" in data:
        vulnerability.cvss_score = data["cvss_score"]

    if "status" in data:
        vulnerability.status = data["status"]

    if "remediation" in data:
        remediation = data["remediation"]
        vulnerability.remediation = (
            remediation.strip() or None
            if isinstance(remediation, str)
            else None
        )

    vulnerability.updated_date = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Vulnerability update conflicts with database constraints"
        }), 409

    return jsonify({
        "message": "Vulnerability updated successfully",
        "vulnerability": vulnerability_to_dict(vulnerability)
    }), 200


# ==========================================
# 9. DELETE VULNERABILITY
# DELETE /vulnerabilities/<id>
# ==========================================

@app.route("/vulnerabilities/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_vulnerability(id):

    if not role_can_delete_vulnerabilities():
        return jsonify({
            "message": "You do not have permission to delete vulnerabilities"
        }), 403

    vulnerability = db.session.get(Vulnerability, id)

    if not vulnerability:
        return jsonify({
            "message": "Vulnerability not found"
        }), 404

    deleted_id = vulnerability.id
    deleted_title = vulnerability.title
    deleted_asset_id = vulnerability.asset_id

    db.session.delete(vulnerability)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Vulnerability could not be deleted"
        }), 409

    return jsonify({
        "message": "Vulnerability deleted successfully",
        "vulnerability_id": deleted_id,
        "title": deleted_title,
        "asset_id": deleted_asset_id
    }), 200


# ==========================================
# 10. RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True, port=5003)
