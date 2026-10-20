"""Jad Moharam: persistence, validation and integration for services 3/8/9."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import requests
from flask import current_app, g, request

from common import config
from common.audit_client import audit_event, send_audit_log
from common.auth import require_roles
from common.responses import error, success

SEVERITIES = ('Low', 'Medium', 'High', 'Critical')
CATEGORIES = ('Malware', 'Phishing', 'Unauthorized Access', 'Account Compromise',
              'Data Leakage', 'Denial of Service', 'Other')
INCIDENT_STATUSES = ('Open', 'Under Investigation', 'Mitigated', 'Resolved', 'Closed')
TYPES = ('Incident Assignment', 'Security Alert', 'System Notification', 'Threat Alert', 'Vulnerability Alert')
ACTION_STATUSES = ('Pending', 'In Progress', 'Completed')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


class JadRepository:
    def __init__(self, path):
        self.path = path
        Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)
        schema = Path(__file__).resolve().parents[1] / 'database/schema_jad_moharam.sql'
        with self.connect() as conn:
            # Mohannad's SQLAlchemy models use id; earlier shared fixtures use user_id/asset_id.
            self.user_key = self.primary_key(conn, 'users', 'user_id')
            self.asset_key = self.primary_key(conn, 'assets', 'asset_id')
            sql = schema.read_text(encoding='utf-8')
            sql = sql.replace('REFERENCES users(user_id)', f'REFERENCES users({self.user_key})')
            sql = sql.replace('REFERENCES assets(asset_id)', f'REFERENCES assets({self.asset_key})')
            conn.executescript(sql)

    @staticmethod
    def primary_key(conn, table, legacy):
        columns = {row['name'] for row in conn.execute(f'PRAGMA table_info({table})')}
        return 'id' if 'id' in columns and legacy not in columns else legacy

    def asset(self, asset_id):
        return self.one(f'SELECT {self.asset_key} AS asset_id FROM assets WHERE {self.asset_key}=?',
                        (asset_id,), 'Asset not found')

    @contextmanager
    def connect(self, write=False):
        conn = sqlite3.connect(self.path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            if write:
                conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def all(self, sql, params=()):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def one(self, sql, params=(), missing='Resource not found'):
        rows = self.all(sql, params)
        if not rows:
            raise ApiError(missing, 404)
        return rows[0]


def repo():
    return current_app.extensions['jad_repository']


def integer(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ApiError(f'{field} must be a positive integer')
    return value


def text(value, field, limit=5000):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ApiError(f'{field} must be nonempty text of at most {limit} characters')
    cleaned = value.strip()
    if any(ord(char) < 32 and char not in '\n\r\t' for char in cleaned):
        raise ApiError(f'{field} contains invalid control characters')
    return cleaned


def enum(value, field, choices):
    value = text(value, field, 100)
    for option in choices:
        if option.casefold() == value.casefold():
            return option
    raise ApiError(f'{field} must be one of: {", ".join(choices)}')


def body(required, optional=()):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        raise ApiError('A nonempty JSON object is required')
    missing = set(required) - data.keys()
    unknown = data.keys() - set(required) - set(optional)
    if missing:
        raise ApiError('Missing fields: ' + ', '.join(sorted(missing)))
    if unknown:
        raise ApiError('Unknown fields: ' + ', '.join(sorted(unknown)))
    return data


def user(user_id, active=True):
    integer(user_id, 'user_id')
    key = repo().user_key
    row = repo().one(f'SELECT {key} AS user_id,username,role,account_status FROM users WHERE {key}=?',
                     (user_id,), 'User not found')
    role_names = {'Security Administrator': 'admin', 'Security Analyst': 'analyst',
                  'Regular Employee/User': 'user', 'Regular User': 'user', 'Auditor': 'auditor'}
    row['role'] = role_names.get(row['role'], row['role'])
    if active and row['account_status'].lower() != 'active':
        raise ApiError('User account is not active', 403)
    return row


def protect(*roles, allow_service=False):
    def decorator(view):
        @wraps(view)
        def checked(*args, **kwargs):
            if not g.is_service:
                try:
                    stored = user(g.current_user['user_id'])
                except ApiError:
                    audit_event('UNAUTHORIZED_ACCESS', 'Authenticated account missing or inactive', 'Warning',
                                user_id=g.current_user['user_id'])
                    raise ApiError('Authenticated account is missing or inactive', 401)
                if stored['role'] != g.current_user['role']:
                    audit_event('UNAUTHORIZED_ACCESS', 'Token role no longer matches account', 'Warning',
                                user_id=g.current_user['user_id'])
                    raise ApiError('Account role changed; log in again', 401)
            return view(*args, **kwargs)
        return require_roles(*roles, allow_service=allow_service)(checked)
    return decorator


def deny(message='User does not have permission to access this record'):
    audit_event('UNAUTHORIZED_ACCESS', message, 'Warning', user_id=g.current_user['user_id'])
    raise ApiError(message, 403)


def incident_access(row):
    actor = g.current_user
    if actor['role'] == 'analyst' and row['assigned_analyst_id'] != actor['user_id']:
        deny('Analysts may access only incidents assigned to them')
    if actor['role'] == 'user' and row['reporter_id'] != actor['user_id']:
        deny('Users may access only their own incident reports')


def personal_access(row):
    if g.current_user['role'] in ('analyst', 'user') and row['user_id'] != g.current_user['user_id']:
        deny('Users may access only their own notifications')


def queue(conn, kind, payload):
    conn.execute('INSERT INTO jad_outbox(owner_service,kind,payload,created_at) VALUES(?,?,?,?)',
                 (current_app.config['SERVICE_NAME'], kind, json.dumps(payload), now()))


def record(conn, action, description):
    actor = g.get('current_user')
    queue(conn, 'audit', dict(user_id=actor['user_id'] if actor else None,
          action=action, description=description, severity='Information',
          related_service=current_app.config['SERVICE_NAME']))


def flush_outbox():
    """Send outside write transactions: Omar's logs use the same SQLite file."""
    pending = repo().all('SELECT * FROM jad_outbox WHERE owner_service=? AND delivered_at IS NULL ORDER BY event_id LIMIT 100',
                         (current_app.config['SERVICE_NAME'],))
    failures = set()
    for event in pending:
        lease = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(timespec='microseconds').replace('+00:00', 'Z')
        with repo().connect(write=True) as conn:
            claimed = conn.execute('UPDATE jad_outbox SET claimed_until=? WHERE event_id=? '
                'AND delivered_at IS NULL AND (claimed_until IS NULL OR claimed_until<?)',
                (lease, event['event_id'], now())).rowcount
        if not claimed:
            continue
        payload = json.loads(event['payload'])
        delivered = False
        try:
            if event['kind'] == 'audit':
                hook = current_app.config.get('AUDIT_HOOK') or send_audit_log
                delivered = hook(**payload)
            else:
                hook = current_app.config.get('NOTIFICATION_HOOK')
                if hook:
                    delivered = hook(payload)
                else:
                    base = current_app.config.get('NOTIFICATIONS_SERVICE_URL') or config.service_url('notifications')
                    response = requests.post(base.rstrip('/') + '/notifications', json=payload,
                        headers={config.SERVICE_KEY_HEADER: config.SERVICE_API_KEY}, timeout=3)
                    delivered = response.status_code == 201
            if delivered:
                with repo().connect(write=True) as conn:
                    conn.execute('UPDATE jad_outbox SET delivered_at=?,claimed_until=NULL WHERE event_id=?', (now(), event['event_id']))
            else:
                failures.add(event['kind'])
        except (requests.RequestException, ValueError, RuntimeError):
            failures.add(event['kind'])
        finally:
            if not delivered:
                with repo().connect(write=True) as conn:
                    conn.execute('UPDATE jad_outbox SET claimed_until=NULL WHERE event_id=?', (event['event_id'],))
    remaining = repo().all('SELECT DISTINCT kind FROM jad_outbox WHERE owner_service=? AND delivered_at IS NULL',
                           (current_app.config['SERVICE_NAME'],))
    failures.update(row['kind'] for row in remaining)
    return [f'{kind} delivery pending; saved for retry' for kind in sorted(failures)]


def changed(data, message, status=200):
    return success(data, message, status, warnings=flush_outbox())


def install(app, blueprint, service_name, overrides=None):
    from common.app_setup import configure_app
    app.config.update(DATABASE_PATH=config.DATABASE_PATH, SERVICE_NAME=service_name, MAX_CONTENT_LENGTH=1048576,
                      AUDIT_HOOK=None, NOTIFICATION_HOOK=None, LOGS_SERVICE_URL=None)
    app.config.update(overrides or {})
    app.extensions['jad_repository'] = JadRepository(app.config['DATABASE_PATH'])
    prefix = app.config.get('JAD_ROUTE_PREFIX', os.getenv('JAD_ROUTE_PREFIX', ''))
    app.register_blueprint(blueprint, url_prefix=prefix or None)
    configure_app(app, 'Jad Moharam')

    @app.errorhandler(ApiError)
    def api_error(exc):
        return error(exc.message, exc.status)

    @app.errorhandler(sqlite3.IntegrityError)
    def integrity_error(exc):
        if 'UNIQUE constraint' in str(exc):
            return error('Duplicate record or step number', 409)
        return error('Invalid database relationship or value', 400)

    @app.errorhandler(sqlite3.OperationalError)
    def database_error(exc):
        app.logger.warning('Database integration error: %s', exc)
        return error('Database dependency unavailable; confirm the shared users/assets schema', 503)

    return app
