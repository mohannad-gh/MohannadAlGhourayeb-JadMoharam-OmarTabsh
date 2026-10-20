# Jad Moharam — integration with Omar Tabsh

## What Omar added and how to use it

Omar's `omar-tabsh-services` branch contains Services 4, 5 and 6, shared JWT/role/response/audit helpers, a Postman collection and tests. It is integrated into Jad's local branch. Keep his files and history: they supply the audit endpoint and reports your services depend on.

Jad uses `common.auth`, `common.roles`, `common.responses`, `common.audit_client` and `common.audit_events` from Omar. Existing Omar source files were retained. His tests run alongside the new ones.

- Audit: writes are sent to `POST /logs` on 5005 using `X-Service-Key` and his exact event/severity/service names.
- Reports: `GET /incidents` returns `data` as a list with `incident_id`, `severity` and `status`, so Omar's Incident Report needs no adapter.
- Notifications: Omar's Threat service does not currently call Jad's notification endpoint. A threat-alert call still needs to be added by Omar; the endpoint already accepts the shared service key. Mohannad must make the equivalent call for vulnerability alerts. These are teammate tasks, not represented as finished here.
- Open incidents matches Omar's definition: Open, Under Investigation or Mitigated.

## What to coordinate with Mohannad

Mohannad's Users and Assets commit `601de89` is now merged with its authorship preserved. Vulnerabilities remains unavailable. Jad's integration changes to his apps are limited to package-safe model imports and an optional `TEAM_DATABASE_URI`; his endpoint logic is retained.

Expected shared tables:

```text
users(id PRIMARY KEY, username, role, account_status, ...)  # Mohannad model
assets(id PRIMARY KEY, ...)                               # Mohannad model
```

Jad automatically recognizes the actual `id` keys and the earlier `user_id`/`asset_id` fixture keys. On a fresh shared database its schema creates foreign keys to the detected columns. Existing demo databases are not migrated into real Users databases: use a fresh database for team setup. JWTs may use Omar's claims or Mohannad's flask_jwt_extended `sub` identity and full role titles. Account status must be `Active`; stale roles are rejected. This is verified using real password login over HTTP.

Start the eight available services with `python -m scripts.run_team_services`. It creates the real SQLAlchemy Users/Assets tables before the Jad tables and gives every service the same absolute database path and private secrets. Standalone Users/Assets launches retain their old separate database defaults when `TEAM_DATABASE_URI` is absent. There is no public endpoint to promote an account to administrator; administrator provisioning remains a team deployment decision.

**A proposed difference from Omar's contract:** his document says other services' data is always read through APIs. Jad currently reads only user identity/status/role and asset existence from the common SQLite schema for authorization and foreign-key validation. It never writes those tables outside the separate demo seeder. This avoids inventing user endpoints analysts are not allowed to call. Confirm these read-only lookups with the team, or replace the `user()`/asset lookup with Mohannad's agreed internal verification API once he supplies it.

All five domain tables, plus execution history and an outbox, are in `database/schema_jad_moharam.sql`; service initialization adapts its legacy FK column names for Mohannad's real schema. Jad apps do not create users/assets tables. A missing or incompatible teammate schema returns 503. Jad connections enforce SQLite foreign keys. Mohannad must also enable foreign-key enforcement on his SQLAlchemy connections before relying on deletion restrictions; the current integration test checks consistency without deleting referenced parents.

Current teammate gaps include Service 7, the sixth Asset search operation, Users/Assets audit events, and Threat/Vulnerability producers calling the notification API. These are not claimed as completed by this integration change. The summary and asset reports now work with the real supplied services; the vulnerability report still returns 503.

## Reliable side effects and known limits

Successful data changes and their audit/notification events are saved in one local transaction. HTTP delivery happens after commit, avoiding deadlock when Omar's logging service writes the same SQLite file. Pending events return warnings and can be retried. Event ownership prevents one service from recursively sending another's notification job; 30-second claims prevent parallel workers from delivering the same job simultaneously.

Delivery is at least once: a crash after the remote service accepts an event but before local acknowledgement can produce a duplicate on retry. Exactly-once delivery would require a team-wide idempotency key contract. No always-running retry daemon is installed; run `scripts.retry_jad_outbox` after an outage or schedule it as a team deployment task.

Incident assignment first records `INCIDENT_ASSIGNMENT_AUTHORIZED` through Omar's API and returns 503 without changing the assignment if that call fails. The committed change then queues `INCIDENT_ASSIGNED` and the notification. The authorization record documents intent, not proof of a successful later commit; these are distinct events because HTTP and SQLite do not share a distributed transaction.

Design choices beyond explicit requirements: consecutive playbook steps; Pending -> In Progress -> Completed; assigned responders restricted to active administrators/analysts; completed actions immutable. Execution history snapshots survive deleting playbooks/actions. No real response actions such as account resets or network isolation are performed: this service tracks the response procedure.

## Branch workflow

Review the changes on `jad-moharam` and open a PR to `main` for team review when ready. Do not replace Omar's branch or force-push his history. The old removed code was not restored from its deleted branch; these services target Omar's actual interfaces.
