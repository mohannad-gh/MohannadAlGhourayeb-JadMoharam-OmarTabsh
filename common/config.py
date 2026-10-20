# Shared configuration used by every service
# Omar Tabsh - 202400798
#
# Values come from the .env file in the project root (copy .env.example to .env).
# All three teammates must use the SAME JWT_SECRET_KEY and SERVICE_API_KEY,
# otherwise tokens issued by the Users service will be rejected by the others.

import os
import logging

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

_DEV_JWT_SECRET = "dev-only-jwt-secret-change-me"
_DEV_SERVICE_KEY = "dev-only-service-key-change-me"

# One SQLite database file shared by all services. Each service only creates,
# reads and writes ITS OWN tables; data owned by another service is always
# obtained through that service's API.
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH", os.path.join(BASE_DIR, "database", "security_system.db"))

# Authentication (tokens are issued by the Users and Identity Management service)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", _DEV_JWT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.environ.get("JWT_EXPIRES_MINUTES", "60"))

# Secret shared only between services. A service sends it in the X-Service-Key
# header when it records an audit event, so normal users cannot forge logs.
SERVICE_API_KEY = os.environ.get("SERVICE_API_KEY", _DEV_SERVICE_KEY)
SERVICE_KEY_HEADER = "X-Service-Key"

if JWT_SECRET_KEY == _DEV_JWT_SECRET or SERVICE_API_KEY == _DEV_SERVICE_KEY:
    logging.getLogger(__name__).warning(
        "Using development secrets. Create a .env file (see .env.example).")

# Optional URL prefix for Omar Tabsh's services, e.g. "/omar-tabsh", in case the
# student name has to appear inside the URL. Empty by default.
TABSH_ROUTE_PREFIX = os.environ.get("TABSH_ROUTE_PREFIX", "")

# Port of every service: port 500N belongs to Service N of the project document
SERVICE_PORTS = {
    "users": 5001,
    "assets": 5002,
    "incidents": 5003,
    "threats": 5004,
    "logs": 5005,
    "reports": 5006,
    "vulnerabilities": 5007,
    "notifications": 5008,
    "playbooks": 5009,
}

_TABSH_SERVICES = ("threats", "logs", "reports")


def service_url(name):
    """Base URL of a service, e.g. service_url("logs") -> http://127.0.0.1:5005

    Can be overridden with an environment variable such as LOGS_SERVICE_URL.
    """
    override = os.environ.get(f"{name.upper()}_SERVICE_URL")
    if override:
        return override.rstrip("/")
    prefix = TABSH_ROUTE_PREFIX if name in _TABSH_SERVICES else ""
    return f"http://127.0.0.1:{SERVICE_PORTS[name]}{prefix}"
