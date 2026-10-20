
import os
import ipaddress

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from sqlalchemy.exc import IntegrityError

if __package__:
    from .models import db, Asset
else:
    from models import db, Asset


# ==========================================
# 1. FLASK APPLICATION SETUP
# ==========================================

load_dotenv()

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY must be configured")

jwt = JWTManager(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("TEAM_DATABASE_URI", "sqlite:///assets.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ==========================================
# 2. SHARED HELPERS AND VALIDATION
# ==========================================

ALLOWED_CRITICALITY = [
    "Low", "Medium", "High", "Critical"
]

ALLOWED_STATUSES = [
    "Active", "Inactive", "Under Maintenance"
]

ASSET_FIELDS = {
    "asset_name",
    "asset_type",
    "ip_address",
    "department",
    "owner_id",
    "criticality",
    "status"
}


def asset_to_dict(asset):
    return {
        "asset_id": asset.id,
        "asset_name": asset.asset_name,
        "asset_type": asset.asset_type,
        "ip_address": asset.ip_address,
        "department": asset.department,
        "owner_id": asset.owner_id,
        "criticality": asset.criticality,
        "status": asset.status,
        "created_date": (
            asset.created_date.isoformat()
            if asset.created_date else None
        )
    }


def validate_asset_fields(data, partial=False):

    if not isinstance(data, dict):
        return "A JSON object is required"

    if not data:
        return "At least one asset field is required"

    if any(field not in ASSET_FIELDS for field in data):
        return "One or more asset fields are not allowed"

    required_fields = [
        "asset_name",
        "asset_type",
        "department",
        "owner_id",
        "criticality"
    ]

    if not partial:
        for field in required_fields:
            if field not in data or data[field] is None:
                return f"{field} is required"

    for field in ["asset_name", "asset_type", "department"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return f"{field} must be a non-empty string"

            max_length = {
                "asset_name": 150,
                "asset_type": 80,
                "department": 100
            }[field]

            if len(data[field].strip()) > max_length:
                return f"{field} is too long"

    if "owner_id" in data:
        if type(data["owner_id"]) is not int or data["owner_id"] <= 0:
            return "owner_id must be a positive integer"

    if "criticality" in data:
        if not isinstance(data["criticality"], str):
            return "Invalid criticality level"

        if data["criticality"] not in ALLOWED_CRITICALITY:
            return "Invalid criticality level"

    if "status" in data:
        if not isinstance(data["status"], str):
            return "Invalid asset status"

        if data["status"] not in ALLOWED_STATUSES:
            return "Invalid asset status"

    if "ip_address" in data and data["ip_address"] is not None:
        value = data["ip_address"]

        if not isinstance(value, str):
            return "Invalid IP address format"

        if value.strip():
            try:
                ipaddress.ip_address(value.strip())
            except ValueError:
                return "Invalid IP address format"

    return None


def role_can_view_assets():
    return get_jwt().get("role") in [
        "Security Administrator",
        "Security Analyst",
        "Auditor"
    ]


def role_can_manage_assets():
    return get_jwt().get("role") == "Security Administrator"


# ==========================================
# 3. HEALTH CHECK
# GET /health
# ==========================================

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "success",
        "service": "Asset Management",
        "message": "Asset Management Service is running"
    }), 200


# ==========================================
# 4. REGISTER ASSET
# POST /assets
# ==========================================

@app.route("/assets", methods=["POST"])
@jwt_required()
def register_asset():

    if not role_can_manage_assets():
        return jsonify({
            "message": "You do not have permission to register assets"
        }), 403

    data = request.get_json(silent=True)
    error = validate_asset_fields(data)

    if error:
        return jsonify({"message": error}), 400

    asset_name = data["asset_name"].strip()

    if Asset.query.filter_by(asset_name=asset_name).first():
        return jsonify({
            "message": "Asset name already exists"
        }), 409

    ip_value = data.get("ip_address")

    if isinstance(ip_value, str):
        ip_value = ip_value.strip() or None

    new_asset = Asset(
        asset_name=asset_name,
        asset_type=data["asset_type"].strip(),
        ip_address=ip_value,
        department=data["department"].strip(),
        owner_id=data["owner_id"],
        criticality=data["criticality"],
        status=data.get("status", "Active")
    )

    try:
        db.session.add(new_asset)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Asset could not be saved due to a database constraint"
        }), 409

    return jsonify({
        "message": "Asset registered successfully",
        "asset": asset_to_dict(new_asset)
    }), 201


# ==========================================
# 5. RETRIEVE ALL ASSETS
# GET /assets
# ==========================================

@app.route("/assets", methods=["GET"])
@jwt_required()
def get_all_assets():

    if not role_can_view_assets():
        return jsonify({
            "message": "You do not have permission to view assets"
        }), 403

    assets = Asset.query.order_by(Asset.id).all()

    return jsonify({
        "message": "Assets retrieved successfully",
        "total_assets": len(assets),
        "assets": [
            asset_to_dict(asset) for asset in assets
        ]
    }), 200


# ==========================================
# 6. SEARCH ASSETS
# GET /assets/search
# ==========================================

@app.route("/assets/search", methods=["GET"])
@jwt_required()
def search_assets():

    if not role_can_view_assets():
        return jsonify({
            "message": "You do not have permission to search assets"
        }), 403

    allowed_filters = {
        "asset_name",
        "asset_type",
        "department",
        "criticality",
        "status",
        "owner_id"
    }

    # Check for unsupported search parameters
    for key in request.args:
        if key not in allowed_filters:
            return jsonify({
                "message": f"Unsupported search filter: {key}"
            }), 400

    if not request.args:
        return jsonify({
            "message": "At least one search filter is required"
        }), 400

    query = Asset.query

    # Partial, case-insensitive asset name search
    if "asset_name" in request.args:
        name = request.args.get("asset_name", "").strip()

        if not name:
            return jsonify({
                "message": "asset_name cannot be empty"
            }), 400

        query = query.filter(
            Asset.asset_name.ilike(f"%{name}%")
        )

    # Filter by asset type
    if "asset_type" in request.args:
        asset_type = request.args["asset_type"].strip()

        if not asset_type:
            return jsonify({
                "message": "asset_type cannot be empty"
            }), 400

        query = query.filter(
            Asset.asset_type.ilike(asset_type)
        )

    # Filter by department
    if "department" in request.args:
        department = request.args["department"].strip()

        if not department:
            return jsonify({
                "message": "department cannot be empty"
            }), 400

        query = query.filter(
            Asset.department.ilike(department)
        )

    # Filter by criticality
    if "criticality" in request.args:
        criticality = request.args["criticality"]

        if criticality not in ALLOWED_CRITICALITY:
            return jsonify({
                "message": "Invalid criticality level"
            }), 400

        query = query.filter_by(criticality=criticality)

    # Filter by status
    if "status" in request.args:
        status = request.args["status"]

        if status not in ALLOWED_STATUSES:
            return jsonify({
                "message": "Invalid asset status"
            }), 400

        query = query.filter_by(status=status)

    # Filter by owner
    if "owner_id" in request.args:
        raw_id = request.args["owner_id"]

        try:
            owner_id = int(raw_id)

            if owner_id <= 0:
                raise ValueError

        except ValueError:
            return jsonify({
                "message": "owner_id must be a positive integer"
            }), 400

        query = query.filter_by(owner_id=owner_id)

    # Execute search
    assets = query.order_by(Asset.id).all()

    return jsonify({
        "message": "Asset search completed successfully",
        "total_results": len(assets),
        "assets": [
            asset_to_dict(asset) for asset in assets
        ]
    }), 200


# ==========================================
# 7. RETRIEVE ASSET BY ID
# GET /assets/<id>
# ==========================================

@app.route("/assets/<int:id>", methods=["GET"])
@jwt_required()
def get_asset_by_id(id):

    if not role_can_view_assets():
        return jsonify({
            "message": "You do not have permission to view assets"
        }), 403

    asset = db.session.get(Asset, id)

    if not asset:
        return jsonify({
            "message": "Asset not found"
        }), 404

    return jsonify({
        "message": "Asset retrieved successfully",
        "asset": asset_to_dict(asset)
    }), 200


# ==========================================
# 8. UPDATE ASSET
# PUT /assets/<id>
# ==========================================

@app.route("/assets/<int:id>", methods=["PUT"])
@jwt_required()
def update_asset(id):

    if not role_can_manage_assets():
        return jsonify({
            "message": "You do not have permission to update assets"
        }), 403

    asset = db.session.get(Asset, id)

    if not asset:
        return jsonify({
            "message": "Asset not found"
        }), 404

    data = request.get_json(silent=True)
    error = validate_asset_fields(data, partial=True)

    if error:
        return jsonify({"message": error}), 400

    if "asset_name" in data:
        new_name = data["asset_name"].strip()

        existing = Asset.query.filter_by(
            asset_name=new_name
        ).first()

        if existing and existing.id != id:
            return jsonify({
                "message": "Asset name already exists"
            }), 409

        asset.asset_name = new_name

    if "asset_type" in data:
        asset.asset_type = data["asset_type"].strip()

    if "department" in data:
        asset.department = data["department"].strip()

    if "owner_id" in data:
        asset.owner_id = data["owner_id"]

    if "criticality" in data:
        asset.criticality = data["criticality"]

    if "status" in data:
        asset.status = data["status"]

    if "ip_address" in data:
        ip_value = data["ip_address"]

        asset.ip_address = (
            ip_value.strip() or None
            if isinstance(ip_value, str)
            else None
        )

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Asset update conflicts with database constraints"
        }), 409

    return jsonify({
        "message": "Asset updated successfully",
        "asset": asset_to_dict(asset)
    }), 200


# ==========================================
# 9. DELETE ASSET
# DELETE /assets/<id>
# ==========================================

@app.route("/assets/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_asset(id):

    if not role_can_manage_assets():
        return jsonify({
            "message": "You do not have permission to delete assets"
        }), 403

    asset = db.session.get(Asset, id)

    if not asset:
        return jsonify({
            "message": "Asset not found"
        }), 404

    deleted_asset_id = asset.id
    deleted_asset_name = asset.asset_name

    db.session.delete(asset)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Asset cannot be deleted because related records exist"
        }), 409

    return jsonify({
        "message": "Asset deleted successfully",
        "asset_id": deleted_asset_id,
        "asset_name": deleted_asset_name
    }), 200


# ==========================================
# 10. RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True, port=5002)
