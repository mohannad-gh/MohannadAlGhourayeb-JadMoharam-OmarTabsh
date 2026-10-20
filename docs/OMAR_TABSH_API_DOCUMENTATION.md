# API Documentation: Services 4, 5 and 6 (Omar Tabsh)

All requests need `Authorization: Bearer <token>` (from `POST /users/login`).
Every response has the header `X-Developed-By: Omar Tabsh`.

Common errors for every endpoint:

| Code | When |
|---|---|
| 401 | Token missing, malformed or expired |
| 403 | Role not allowed (recorded in the audit log as `UNAUTHORIZED_ACCESS`) |
| 400 | Invalid input, `{"status": "error", "message": "...", "errors": {"field": "problem"}}` |
| 404 | Record or endpoint not found |

---

## Service 4: Threat Intelligence (port 5004)

Threat types: `IP Address`, `Domain`, `File Hash`, `Malware Signature`, `Other`.
Severity: `Low`, `Medium`, `High`, `Critical` (case-insensitive input).

| # | API | Method / Endpoint | Roles |
|---|---|---|---|
| 1 | Add Threat Indicator | `POST /threats` | Admin |
| 2 | Retrieve All Threat Indicators | `GET /threats` | Admin, Analyst, Auditor |
| 3 | Retrieve Specific Threat Indicator | `GET /threats/{id}` | Admin, Analyst, Auditor |
| 4 | Search Threat Indicators | `GET /threats/search` | Admin, Analyst |
| 5 | Update Threat Information | `PUT /threats/{id}` | Admin |
| 6 | Delete Threat Indicator | `DELETE /threats/{id}` | Admin |

### 1. Add Threat Indicator: `POST /threats`
Request:
```json
{"threat_type": "IP Address", "threat_value": "185.220.101.45",
 "description": "Tor exit node seen in SSH brute-force attempts", "severity": "High", "source": "AbuseIPDB"}
```
Response `201`:
```json
{"status": "success", "message": "Threat indicator added successfully",
 "data": {"threat_id": 1, "threat_type": "IP Address", "threat_value": "185.220.101.45",
          "description": "...", "severity": "High", "source": "AbuseIPDB",
          "date_added": "2026-10-20 19:37:56", "last_updated": null}}
```
Validation:
- **IP Address:** valid IPv4/IPv6 (Python `ipaddress`).
- **Domain:** host name such as `evil.com` (no `http://` or path), stored lower-case.
- **File Hash:** hexadecimal MD5/SHA-1/SHA-256/SHA-512 (32/40/64/128 characters), stored lower-case.
- **Malware Signature:** at least 3 characters.
- **Other fields:** description up to 1000 characters, source up to 100; unknown fields are rejected.

Errors: `400` validation, `409` duplicate (same type + value; the response contains `existing_threat_id`).
Audit: `THREAT_CREATED`.

### 2. Retrieve All Threat Indicators: `GET /threats`
`200` → `{"status": "success", "count": 4, "data": [ {threat}, ... ]}`

### 3. Retrieve Specific Threat Indicator: `GET /threats/{id}`
`200` → `{"status": "success", "data": {threat}}`. Errors: `404` not found, `400` ID is not a positive integer.

### 4. Search Threat Indicators: `GET /threats/search`
Query parameters (at least one, combined with AND):

| Parameter | Matching |
|---|---|
| `threat_type` | exact (validated) |
| `severity` | exact (validated) |
| `threat_value` | partial, case-insensitive |
| `source` | partial, case-insensitive |

Example: `GET /threats/search?threat_type=Domain&severity=Critical` →
`200 {"status": "success", "message": "1 threat indicator(s) matched the search", "count": 1, "filters": {...}, "data": [...]}`.
An empty result returns `200` with `count: 0`. Errors: `400` for no filter, an unknown filter or an invalid type/severity.

### 5. Update Threat Information: `PUT /threats/{id}`
Only `description`, `severity` and `source` can be changed.
```json
{"severity": "Critical", "source": "CrowdStrike Falcon", "description": "Confirmed C2 server"}
```
`200` returns the updated threat plus `previous_values` (before/after). `last_updated` is set.
Errors: `400` (changing `threat_type`/`threat_value`, empty body, invalid severity), `404`.
Audit: `THREAT_UPDATED` with the old and new values.

### 6. Delete Threat Indicator: `DELETE /threats/{id}`
`200` → `{"status": "success", "message": "Threat indicator 1 deleted successfully", "data": {deleted threat}}`.
Errors: `403` for non-administrators, `404`. Audit: `THREAT_DELETED`.

---

## Service 5: Security Audit Logging (port 5005)

| # | API | Method / Endpoint | Roles |
|---|---|---|---|
| 7 | Create Log Record | `POST /logs` | Admin, trusted services (`X-Service-Key`) |
| 8 | Retrieve All Logs | `GET /logs` | Admin, Auditor |
| 9 | Retrieve Specific Log | `GET /logs/{id}` | Admin, Auditor, Analyst |
| 10 | Search Logs | `GET /logs/search` | Admin, Auditor, Analyst |
| 11 | Delete Logs | `DELETE /logs/{id}` | Admin |
| 12 | Retrieve Logs By User | `GET /logs/user/{user_id}` | Admin, Auditor |

Logs are **immutable**:
- There is no update API.
- `PUT`/`PATCH /logs/{id}` return `405`, and the attempt is logged.
- A database trigger rejects any `UPDATE` on the `logs` table.

### 7. Create Log Record: `POST /logs`
```json
{"user_id": 7, "action": "LOGIN_FAILED", "description": "Wrong password for 'jdoe'",
 "severity": "Warning", "related_service": "Users"}
```
- `user_id`: a positive integer, or `null` if the user is unknown.
- `action`: UPPER_SNAKE_CASE.
- `severity`: `Information`, `Warning`, `Error` or `Critical`.
- `related_service`: one of the values in `common/audit_events.py`.
- `log_id` and `timestamp` (UTC) are set by the server; sending them gives `400`.

Response: `201` with the stored record.

### 8. Retrieve All Logs: `GET /logs`
`200` → `{"status": "success", "count": n, "data": [...]}` (newest first).

### 9. Retrieve Specific Log: `GET /logs/{id}`
`200` with the record. Errors: `404` unknown ID, `400` non-numeric ID.

### 10. Search Logs: `GET /logs/search`

| Parameter | Example |
|---|---|
| `user_id` | `?user_id=7` |
| `date` | `?date=2026-10-20` (UTC day) |
| `date_from`, `date_to` | `?date_from=2026-10-01&date_to=2026-10-20` |
| `action` | `?action=LOGIN_FAILED` |
| `severity` | `?severity=Warning` |
| `related_service` | `?related_service=Threat Intelligence` |

Filters are combined with AND. Errors: `400` for no filter, an unknown filter or a bad date.

### 11. Delete Logs: `DELETE /logs/{id}`
`200` with the deleted record. A new `LOG_DELETED` record (who deleted what) is
created automatically. Errors: `403` for analysts, auditors and users; `404` otherwise.

### 12. Retrieve Logs By User: `GET /logs/user/{user_id}`
`200` → `{"status": "success", "message": "2 log record(s) found for user 7", "count": 2, "user_id": 7, "data": [...]}`.
A user without logs gets `200` with `"data": []` and `"message": "No log records found for user 9999"`.

---

## Service 6: Security Reports (port 5006)

Roles: **Admin and Auditor** only (Analyst and Regular User get `403`).
Reports are computed when they're requested, from the live data returned by the other
services' APIs. The caller's token is forwarded. Nothing is stored or hard-coded. Every
report includes `generated_at` and `data_sources` (which endpoint the data came from).
If a source service is down the report returns `503` (unreachable) or `502` (bad answer)
naming that service.

| # | API | Endpoint | Data source | Contents |
|---|---|---|---|---|
| 13 | Security Summary | `GET /reports/summary` | `GET /users`, `/assets`, `/incidents`, `/threats` | `users`, `assets`, `open_incidents` (Open/Under Investigation/Mitigated), `critical_threats` |
| 14 | Incident Report | `GET /reports/incidents` | `GET /incidents` | `total_incidents`, `incidents_by_severity`, `incidents_by_status` |
| 15 | Asset Report | `GET /reports/assets` | `GET /assets` | `total_assets`, `critical_assets`, `critical_asset_list`, `assets_by_type`, `assets_by_criticality` |
| 16 | Threat Report | `GET /reports/threats` | `GET /threats` | `total_threats`, `threats_by_severity`, `threats_by_type`, `recently_added_threats` (5 newest) |
| 17 | Vulnerability Report | `GET /reports/vulnerabilities` | `GET /vulnerabilities` | `total_vulnerabilities`, `vulnerabilities_by_severity`, `vulnerabilities_by_status`, `critical_vulnerabilities`, `critical_vulnerability_list` |
| 18 | Activity Report | `GET /reports/activity` | `GET /logs` | `total_user_activities`, `login_attempts`, `successful_logins`, `failed_login_attempts`, `unauthorized_access_attempts`, `most_performed_actions` (top 5), `activities_by_severity` |

Example `GET /reports/threats` → `200`:
```json
{"status": "success", "message": "Threat Report generated successfully",
 "data": {"total_threats": 3,
          "threats_by_severity": {"Low": 0, "Medium": 1, "High": 0, "Critical": 2},
          "threats_by_type": {"IP Address": 0, "Domain": 1, "File Hash": 1, "Malware Signature": 1, "Other": 0},
          "recently_added_threats": [ ... ],
          "generated_at": "2026-10-20 19:37:57 UTC",
          "data_sources": ["Threat Intelligence service: GET http://127.0.0.1:5004/threats"]}}
```
