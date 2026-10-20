
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from models import db, User


# ==========================================
# 1. FLASK APPLICATION SETUP
# ==========================================

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY must be configured")

jwt = JWTManager(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ==========================================
# 2. HEALTH CHECK API
# ==========================================

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "success",
        "service": "Users and Identity Management",
        "message": "Service is running"
    }), 200


# ==========================================
# 3. USER REGISTRATION
# POST /users/register
# ==========================================

@app.route("/users/register", methods=["POST"])
def register_user():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "A JSON object is required"
        }), 400

    required_fields = [
        "full_name",
        "username",
        "email",
        "password",
        "department"
    ]

    for field in required_fields:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return jsonify({
                "message": f"{field} is required"
            }), 400

    username = data["username"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({
            "message": "Invalid email format"
        }), 400

    if len(password) < 8:
        return jsonify({
            "message": "Password must contain at least 8 characters"
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            "message": "Username already exists"
        }), 409

    if User.query.filter_by(email=email).first():
        return jsonify({
            "message": "Email already exists"
        }), 409

    hashed_password = bcrypt.generate_password_hash(
        password
    ).decode("utf-8")

    new_user = User(
        full_name=data["full_name"].strip(),
        username=username,
        email=email,
        password_hash=hashed_password,
        department=data["department"].strip(),
        role="Regular User",
        account_status="Active"
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Username or email already exists"
        }), 409

    return jsonify({
        "message": "User registered successfully",
        "user_id": new_user.id,
        "username": new_user.username,
        "role": new_user.role
    }), 201


# ==========================================
# 4. USER LOGIN
# POST /users/login
# ==========================================

@app.route("/users/login", methods=["POST"])
def login_user():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "A JSON object is required"
        }), 400

    identifier = data.get("username") or data.get("email")
    password = data.get("password")

    if not isinstance(identifier, str) or not identifier.strip():
        return jsonify({
            "message": "Username or email is required"
        }), 400

    if not isinstance(password, str) or not password:
        return jsonify({
            "message": "Password is required"
        }), 400

    user = User.query.filter(
        or_(
            User.username == identifier.strip(),
            User.email == identifier.strip().lower()
        )
    ).first()

    if not user or not bcrypt.check_password_hash(
        user.password_hash, password
    ):
        return jsonify({
            "message": "Invalid username or password"
        }), 401

    if user.account_status != "Active":
        return jsonify({
            "message": "Account is inactive or suspended"
        }), 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    user.last_login_date = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }), 200


# ==========================================
# 5. UPDATE USER
# PUT /users/<id>
# ==========================================

@app.route("/users/<int:id>", methods=["PUT"])
@jwt_required()
def update_user(id):

    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)

    if not current_user or current_user.account_status != "Active":
        return jsonify({
            "message": "Account is not active"
        }), 403

    if current_user.role != "Security Administrator":
        if current_user.role != "Regular User" or current_user_id != id:
            return jsonify({
                "message": "You do not have permission to update this user"
            }), 403

    user = db.session.get(User, id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "A JSON object is required"
        }), 400

    allowed_fields = {"full_name", "email", "department"}

    if not data or any(field not in allowed_fields for field in data):
        return jsonify({
            "message": "Only full_name, email and department can be updated"
        }), 400

    for field, value in data.items():
        if not isinstance(value, str) or not value.strip():
            return jsonify({
                "message": f"{field} must be a non-empty string"
            }), 400

    if "full_name" in data:
        user.full_name = data["full_name"].strip()

    if "email" in data:
        new_email = data["email"].strip().lower()

        if "@" not in new_email or "." not in new_email.split("@")[-1]:
            return jsonify({
                "message": "Invalid email format"
            }), 400

        existing_user = User.query.filter_by(email=new_email).first()

        if existing_user and existing_user.id != id:
            return jsonify({
                "message": "Email already exists"
            }), 409

        user.email = new_email

    if "department" in data:
        user.department = data["department"].strip()

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Email already exists"
        }), 409

    return jsonify({
        "message": "User updated successfully",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "department": user.department
    }), 200


# ==========================================
# 6. DELETE USER
# DELETE /users/<id>
# ==========================================

@app.route("/users/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):

    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)

    if not current_user or current_user.account_status != "Active":
        return jsonify({
            "message": "Account is not active"
        }), 403

    if current_user.role != "Security Administrator":
        return jsonify({
            "message": "You do not have permission to delete users"
        }), 403

    if current_user_id == id:
        return jsonify({
            "message": "Administrators cannot delete their own account"
        }), 403

    user = db.session.get(User, id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    deleted_username = user.username
    deleted_user_id = user.id

    db.session.delete(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "User cannot be deleted because related records exist"
        }), 409

    return jsonify({
        "message": "User deleted successfully",
        "user_id": deleted_user_id,
        "username": deleted_username
    }), 200


# ==========================================
# 7. RETRIEVE ALL USERS
# GET /users
# ==========================================

@app.route("/users", methods=["GET"])
@jwt_required()
def get_all_users():

    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)

    if not current_user or current_user.account_status != "Active":
        return jsonify({
            "message": "Account is not active"
        }), 403

    allowed_roles = [
        "Security Administrator",
        "Auditor"
    ]

    if current_user.role not in allowed_roles:
        return jsonify({
            "message": "You do not have permission to view all users"
        }), 403

    users = User.query.order_by(User.id).all()
    users_list = []

    for user in users:
        users_list.append({
            "user_id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "department": user.department,
            "role": user.role,
            "account_status": user.account_status,
            "created_date": (
                user.created_date.isoformat()
                if user.created_date else None
            ),
            "last_login_date": (
                user.last_login_date.isoformat()
                if user.last_login_date else None
            )
        })

    return jsonify({
        "message": "Users retrieved successfully",
        "total_users": len(users_list),
        "users": users_list
    }), 200


# ==========================================
# 8. RETRIEVE USER BY USERNAME
# GET /users/<username>
# ==========================================

@app.route("/users/<string:username>", methods=["GET"])
@jwt_required()
def get_user_by_username(username):

    # Identify the authenticated user
    current_user_id = int(get_jwt_identity())
    current_user = db.session.get(User, current_user_id)

    if not current_user or current_user.account_status != "Active":
        return jsonify({
            "message": "Account is not active"
        }), 403

    # Check permissions before looking up the target
    if current_user.role not in ["Security Administrator", "Auditor"]:
        if current_user.role != "Regular User" or current_user.username != username:
            return jsonify({
                "message": "You do not have permission to view this user"
            }), 403

    # Search for user by username
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    # Never expose passwords or password hashes
    return jsonify({
        "message": "User retrieved successfully",
        "user": {
            "user_id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "email": user.email,
            "department": user.department,
            "role": user.role,
            "account_status": user.account_status,
            "created_date": (
                user.created_date.isoformat()
                if user.created_date else None
            ),
            "last_login_date": (
                user.last_login_date.isoformat()
                if user.last_login_date else None
            )
        }
    }), 200


# ==========================================
# 9. RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
