# Shared authentication and role-based authorization
# Omar Tabsh - 202400798
#
# Tokens: the Users and Identity Management service calls create_token() after a
# successful login. Every other service checks the token locally with
# require_roles(), using the same JWT_SECRET_KEY, so no extra call is needed.
#
# Token claims: {"sub": "7", "user_id": 7, "username": "jdoe", "role": "analyst", "iat": ..., "exp": ...}
#
#   401 -> token missing, malformed, expired or signed with another key
#   403 -> valid token, but the role is not allowed for this endpoint
# Both cases are recorded in the audit log as UNAUTHORIZED_ACCESS.

import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, request

from common import config
from common.audit_client import audit_event
from common.audit_events import UNAUTHORIZED_ACCESS, WARNING
from common.responses import error
from common.roles import ALL_ROLES, ROLE_TITLES

PERMISSION_DENIED_MESSAGE = "User does not have permission to perform this operation"


class AuthenticationError(Exception):
    pass


def create_token(user_id, username, role, expires_minutes=None):
    """Create a signed login token (called by the Users service at login)."""
    if role not in ALL_ROLES:
        raise ValueError(f"Unknown role '{role}'. Expected one of {ALL_ROLES}")
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "user_id": int(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes or config.JWT_EXPIRES_MINUTES),
    }
    return jwt.encode(claims, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token):
    """Verify a token and return {"user_id", "username", "role"}. Raises AuthenticationError."""
    try:
        claims = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM],
                            options={"require": ["exp", "user_id", "role"]})
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Authentication token has expired. Please log in again")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid authentication token")

    user_id = claims.get("user_id")
    if claims.get("role") not in ALL_ROLES or not isinstance(user_id, int) or isinstance(user_id, bool):
        raise AuthenticationError("Invalid authentication token")
    return {"user_id": user_id, "username": claims.get("username"), "role": claims["role"]}


def get_bearer_token():
    header = request.headers.get("Authorization", "").strip()
    if not header:
        raise AuthenticationError(
            "Missing authentication token. Send the header 'Authorization: Bearer <token>'")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthenticationError("Authorization header must have the format 'Bearer <token>'")
    return token.strip()


def has_service_key():
    return config.SERVICE_KEY_HEADER in request.headers


def is_trusted_service():
    """True if the request carries the correct inter-service key."""
    key = request.headers.get(config.SERVICE_KEY_HEADER, "")
    return bool(key) and hmac.compare_digest(key, config.SERVICE_API_KEY)


def require_roles(*allowed_roles, allow_service=False):
    """Protect a route so that only the given roles (and optionally trusted services) can call it.

    Inside the route, g.current_user holds {"user_id", "username", "role"} for a user,
    or None when the caller is a trusted service (g.is_service is then True).
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = None
            g.is_service = False

            if allow_service and has_service_key():
                if is_trusted_service():
                    g.is_service = True
                    return view(*args, **kwargs)
                _record_violation(None, f"Rejected request to {request.method} {request.path}: "
                                        f"invalid {config.SERVICE_KEY_HEADER}")
                return error("Invalid service key", 401)

            try:
                user = decode_token(get_bearer_token())
            except AuthenticationError as exc:
                _record_violation(None, f"Rejected unauthenticated request to "
                                        f"{request.method} {request.path}: {exc}")
                return error(str(exc), 401)

            if user["role"] not in allowed_roles:
                _record_violation(user["user_id"], (
                    f"User '{user['username']}' (id {user['user_id']}, role {ROLE_TITLES[user['role']]}) "
                    f"was denied access to {request.method} {request.path}"))
                return error(PERMISSION_DENIED_MESSAGE, 403)

            g.current_user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator


def current_user_id():
    user = g.get("current_user")
    return user["user_id"] if user else None


def _record_violation(user_id, description):
    audit_event(UNAUTHORIZED_ACCESS, description, WARNING, user_id=user_id)
