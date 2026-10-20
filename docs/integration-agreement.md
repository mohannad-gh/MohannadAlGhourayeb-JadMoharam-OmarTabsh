# Proposed integration agreement

This proposal needs confirmation from Mohannad, Tabsh and Jad before domain implementation.

- **Stack:** Flask and SQLite. Use the standard Python `sqlite3` module for this starter; confirm whether teammates use an ORM before defining shared tables.
- **Processes:** independent Flask services communicating through HTTP. Suggested ports are 5001–5009, matching service numbers. These ports are a convention, not an assignment requirement.
- **Storage:** one shared SQLite file and one agreed schema. Enable foreign keys on every connection. Agree on migrations and table creation ownership; do not let individual services recreate or reset teammates' data.
- **Ownership:** Mohannad owns users, assets and vulnerabilities; Tabsh owns threats, audit logs and reports; Jad owns incidents, investigation notes, notifications, playbooks and response actions.
- **Authentication:** Mohannad supplies login and identity verification. Confirm token format, signature verification, expiry, account status checks and exact role names. A role supplied by the client is never evidence of permission. No separate login service is included in this starter.
- **Authorization:** follow each service's explicit role list, with analyst incident access limited to assigned incidents and regular-user incident access limited to their reports. Personal notifications must be restricted to their recipient unless the role permits organizational access.
- **IDs and timestamps:** propose integer primary keys, snake_case JSON names and UTC ISO 8601 timestamps. Final names must match the agreed schema.
- **Audit API (Tabsh):** confirm endpoint, authentication and body shape. Proposed fields: `user_id`, `action`, `description`, `severity`, `related_service`. Record unauthorized attempts and data changes; incident assignment specifically requires an audit record.
- **Notification API (Jad):** proposed fields: `user_id`, `title`, `message`, `type`, `severity`. Incidents trigger assignment notifications; Mohannad's vulnerability service and Tabsh's threat service call it for their alerts. Agree on service credentials rather than allowing unauthenticated creation.
- **Unavailable dependencies:** propose short HTTP timeouts. Reject an assignment if its required audit cannot be recorded. Agree on reliable retry/outbox handling for failed notifications and other audit events so they are not silently lost. These failure policies are design proposals, not detailed rules in the assignment.
- **Enumerations:** use the assignment's exact role, incident status and notification type spellings. Notification severity is not enumerated in the document; propose Low/Medium/High/Critical and confirm with the team.
- **Execution history:** propose an additional `action_history` table. The assignment requires history preservation but does not prescribe this table. Agree how history survives playbook deletion.
- **Errors:** propose 400 validation, 401 missing/invalid identity, 403 denied permission, 404 unknown resource, 409 duplicates and 503 dependency unavailable. Use `{"status":"error","message":"..."}` consistently.
- **Ambiguities to confirm:** the assignment says every route must include the student's full name. Confirm whether this means the URL or source annotation; do not assume comments alone satisfy it. The playbook add-action description mentions administrators, while its authorization list also allows analysts; use the explicit list pending clarification.
- **Git:** personal branches, small meaningful commits and reviewed pull requests. Keep `.env`, credentials, virtual environments and local databases out of Git.

No teammate interfaces or agreement are represented as already implemented or approved.
