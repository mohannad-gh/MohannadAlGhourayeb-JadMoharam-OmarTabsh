# Team Integration Contract (proposal)

Prepared by **Omar Tabsh** for Mohannad Al Ghourayeb and Jad Moharam. Nothing here
is final until all three of us agree. If something does not suit your service,
say so before we build on it.

## 1. Architecture

- 9 independent Flask services, one per service in the project document.
- Each service runs on port `500N`, where N is its service number:

  | Port | Service | Owner |
  |---|---|---|
  | 5001 | Users and Identity Management | Mohannad Al Ghourayeb |
  | 5002 | Asset Management | Mohannad Al Ghourayeb |
  | 5003 | Incident Management | Jad Moharam |
  | 5004 | Threat Intelligence | Omar Tabsh |
  | 5005 | Security Audit Logging | Omar Tabsh |
  | 5006 | Security Reports | Omar Tabsh |
  | 5007 | Vulnerability Management | Mohannad Al Ghourayeb |
  | 5008 | Notification and Alert Management | Jad Moharam |
  | 5009 | Security Playbook and Response Automation | Jad Moharam |

- **One SQLite database file** (`database/security_system.db`, path in `common/config.py`).
  Each service creates and touches **only its own tables**. Data that belongs to
  another service is always obtained by calling that service's API. A single
  database lets us draw one schema diagram with the foreign keys the document asks for.
- Code layout: `services/<service_name>/app.py` with `create_app()`. Run with
  `python -m services.<service_name>.app` from the project root.

## 2. Authentication (Users service issues, everyone verifies)

- `POST /users/login` (Mohannad) checks the hashed password and account status, then returns
  a JWT created with `common.auth.create_token(user_id, username, role)`.
- Token claims: `user_id` (int), `username`, `role`, `exp` (60 minutes).
- `role` must be one of the constants in `common/roles.py`:
  `admin`, `analyst`, `user`, `auditor`.
- Every protected route uses the decorator:

  ```python
  from common.auth import require_roles
  from common.roles import ADMIN, AUDITOR

  @bp.get("/assets")
  @require_roles(ADMIN, AUDITOR)
  def get_all_assets():
      user = g.current_user          # {"user_id": 1, "username": "...", "role": "admin"}
  ```

  - Missing, invalid or expired token: **401**.
  - Valid token but the role isn't allowed: **403**.
  - Both are logged automatically as `UNAUTHORIZED_ACCESS`; you don't need to log them yourself.
  - Never trust a role sent in the request body.
- Secrets live in `.env` (copy `.env.example`). All of us must use the **same**
  `JWT_SECRET_KEY` and `SERVICE_API_KEY`. Share them privately and never commit `.env`.

## 3. Automatic audit logging (everyone sends, Omar's service stores)

Call this after every successful data change (and for logins):

```python
from common.audit_client import audit_event
from common import audit_events as events

audit_event(events.USER_DELETED, f"User #{user_id} '{username}' deleted",
            events.WARNING, user_id=g.current_user["user_id"])
```

- `app.config["SERVICE_NAME"]` must be set to your `related_service` value from
  `common/audit_events.py`, e.g. `events.USERS_SERVICE`.
- The client posts to `POST http://127.0.0.1:5005/logs` with the header
  `X-Service-Key: <SERVICE_API_KEY>`. Normal users cannot forge logs because they
  don't have the key; administrators may also create logs (document requirement).
- If the logging service is down, your request still succeeds and a warning is printed.
- `user_id` may be `None` when the user is unknown, e.g. a failed login with a
  non-existing username. Put the attempted username in the description.

Payload stored by `POST /logs`:

```json
{ "user_id": 7, "action": "LOGIN_FAILED", "description": "Wrong password for 'jdoe'",
  "severity": "Warning", "related_service": "Users" }
```

`log_id` and `timestamp` are always set by the server.

### Events each service must send (use the constants, the activity report counts them)

| Service | Actions |
|---|---|
| Users | `LOGIN_SUCCESS`, `LOGIN_FAILED`, `USER_CREATED`, `USER_UPDATED`, `USER_DELETED`, `ROLE_CHANGED` |
| Assets | `ASSET_CREATED`, `ASSET_UPDATED`, `ASSET_DELETED` |
| Incidents | `INCIDENT_CREATED`, `INCIDENT_ASSIGNED`, `INCIDENT_STATUS_CHANGED`, `INCIDENT_NOTE_ADDED` |
| Vulnerabilities | `VULNERABILITY_CREATED`, `VULNERABILITY_UPDATED`, `VULNERABILITY_DELETED` |
| Notifications | `NOTIFICATION_CREATED`, `NOTIFICATION_READ`, `NOTIFICATION_DELETED` |
| Playbooks | `PLAYBOOK_CREATED`, `PLAYBOOK_DELETED`, `RESPONSE_ACTION_ADDED`, `RESPONSE_ACTION_UPDATED` |
| Threats (done) | `THREAT_CREATED`, `THREAT_UPDATED`, `THREAT_DELETED` |
| All (automatic) | `UNAUTHORIZED_ACCESS` |

Severities: `Information`, `Warning`, `Error`, `Critical`.

## 4. Response format

```json
{"status": "success", "message": "...", "count": 3, "data": [ ... ]}
{"status": "error", "message": "User does not have permission to perform this operation"}
```

Use `common.responses.success()` and `error()`. Status codes: 200, 201 (created),
400 (validation), 401, 403, 404, 405, 409 (duplicate), 500, 502/503 (another service failed).

## 5. What the Reports service needs from your services

The Reports service calls your **"retrieve all"** endpoint and forwards the caller's
token. Admin and Auditor are allowed on all of them in the document, so no extra
permissions are needed. Please return the records as a list in `data`, using these
field names (or tell Omar what you use instead):

| Endpoint | Fields used |
|---|---|
| `GET /users` (5001) | one object per user (only counted) |
| `GET /assets` (5002) | `asset_id`, `asset_name`, `asset_type`, `criticality_level` |
| `GET /incidents` (5003) | `incident_id`, `severity`, `status` |
| `GET /vulnerabilities` (5007) | `vulnerability_id`, `title`, `cve_id`, `severity_level`, `status` |

Use the exact value spellings from the document: `Low/Medium/High/Critical`, `Open`,
`Under Investigation`, `Mitigated`, `Resolved`, `Closed`, `In Progress`.

## 6. Open decisions

1. **Name in every route.** The document says each route must include the student's
   full name. Is a comment and Postman request name enough, or must the URL contain it?
   (Omar's services support an optional URL prefix: `TABSH_ROUTE_PREFIX=/omar-tabsh`.)
   Ask the instructor.
2. **Auditor search on threats / analyst access to logs.** The per-service tables and the
   role lists in the document disagree. We follow the per-service tables. Ask the instructor.
3. **`logs.user_id` → `users.user_id`.** Shown in the schema diagram but not enforced as a
   database constraint. Enforcing it would block deleting any user who has logs, or (with
   CASCADE) erase their audit trail. Mohannad, please don't add `ON DELETE CASCADE` towards logs.
4. **"Open incidents"** in the summary report means status Open, Under Investigation or
   Mitigated (not yet resolved). Jad, please confirm.
5. Git: each of us works on our own branch (`mohannad-services`, `omar-tabsh-services`, ...)
   and merges into `main` through a pull request reviewed by another member.
