# Jad Moharam — implementation checklist

Status: setup only. None of the 18 graded APIs is implemented yet.

## Sequence

1. Verify the Flask/SQLite starter and agree on shared interfaces.
2. Define the schema and test data with the team; do not duplicate their user or asset implementation.
3. Implement Notifications, one API at a time.
4. Implement Incidents, including authenticated ownership, lifecycle, audit and assignment notifications.
5. Implement Playbooks, ordered actions and execution history.
6. Run integrated Postman tests, collect actual evidence and complete the common report.

For each API: explain the input and database change, implement it, test allowed roles and denied roles, test invalid input and missing resources, capture real evidence, then make a meaningful commit.

## Required APIs

Admin = Security Administrator; Analyst = Security Analyst; User = Regular Employee/User.

| Done | Method and endpoint from assignment | Allowed roles | Key checks |
|---|---|---|---|
| [ ] | POST /incidents | Admin, User | Required fields, severity, user/asset links; prevent forged reporter identity |
| [ ] | GET /incidents | Admin, Auditor | Multiple incidents, current status and assignee |
| [ ] | GET /incidents/{id} | Admin, Analyst, User, Auditor | Analyst assigned only; User own reports only; include notes; invalid ID |
| [ ] | PUT /incidents/{id}/assign | Admin | Existing incident and analyst role; audit record; assignment notification |
| [ ] | PUT /incidents/{id}/status | Admin, Analyst | Analyst assigned only; reject invalid transitions |
| [ ] | POST /incidents/{id}/notes | Admin, Analyst | Analyst assigned only; nonempty note; authenticated author; retrieve with incident |
| [ ] | POST /notifications | Admin; authorized service calls | Existing recipient, required fields, type, severity; verify service identity |
| [ ] | GET /notifications/user/{user_id} | Admin, Analyst, User, Auditor | Analyst/User own only; existing user with no notifications |
| [ ] | GET /notifications/{id} | Admin, Analyst, User, Auditor | Analyst/User own only; invalid ID |
| [ ] | PUT /notifications/{id}/read | Admin, Analyst, User | Analyst/User own only; read timestamp; Auditor denied |
| [ ] | GET /notifications/search | Admin, Analyst, Auditor | User/type/severity/status filters; Analyst own only |
| [ ] | DELETE /notifications/{id} | Admin | Successful removal; denied deletion; invalid ID |
| [ ] | POST /playbooks | Admin | Name, description, category, severity; creator from authenticated identity |
| [ ] | GET /playbooks | Admin, Analyst, Auditor | Multiple records and empty results |
| [ ] | GET /playbooks/{id} | Admin, Analyst, Auditor | Include actions in step order; invalid ID |
| [ ] | POST /playbooks/{id}/actions | Admin, Analyst | Existing playbook; description, step number; preserve order |
| [ ] | PUT /actions/{id}/status | Admin, Analyst | Valid status, assignment, completion timestamp; preserve history |
| [ ] | DELETE /playbooks/{id} | Admin | Authorized/denied deletion; decide action/history retention |

The endpoint spellings above come from the assignment. Resolve its full-student-name route requirement before registering graded routes.

Incident lifecycle: Open → Under Investigation → Mitigated → Resolved → Closed. All other transitions must be rejected.

Action statuses: Pending, In Progress, Completed. Maintaining order and history is required; a strict action transition graph is a design choice to confirm, not explicitly specified like the incident graph.

Notification types: Incident Assignment, Security Alert, System Notification, Threat Alert, Vulnerability Alert. Statuses: Unread, Read.

## Schema proposal

All names below are proposals. Confirm them against teammates' actual tables.

| Table | Fields and relationships |
|---|---|
| incidents | id PK; title; description; category; severity; reporter_id FK users; asset_id FK assets; assigned_analyst_id FK users; status; created_at; resolved_at |
| investigation_notes | id PK; incident_id FK incidents; analyst_id FK users; content; created_at |
| notifications | id PK; user_id FK users; title; message; type; severity; status; created_at; read_at |
| playbooks | id PK; name; description; incident_category; severity; created_by FK users; created_at |
| response_actions | id PK; playbook_id FK playbooks; description; step_number; status; assigned_user_id FK users; completed_at |
| action_history (proposed) | id PK; action identity; actor; old/new status and assignee; timestamp; retention strategy |

Users and Assets are Mohannad's tables. Logs are Tabsh's table. Your implementation must use their agreed IDs and authentication, not trust a caller's role field. Confirm nullability, deletion behavior, uniqueness and transaction boundaries before creating tables.

## Supporting work

- [x] Clean clone from restored main; local `jad-moharam` branch.
- [x] Flask application and SQLite connection setup; no domain tables or teammate services.
- [ ] Confirm team agreement and route naming.
- [ ] Final schema with foreign keys and an ER diagram.
- [ ] Authentication verification using Mohannad's implementation.
- [ ] Audit and notification service calls, including dependency failures.
- [ ] Input validation, sanitization, parameterized SQL and consistent errors.
- [ ] Documented Postman collection: body, parameters, responses and errors for every API.
- [ ] Actual Postman evidence for valid and invalid requests, identity checks and permissions.
- [ ] Real database evidence before/after changes and stored relationships.
- [ ] Caption each screenshot: Jad Moharam — API title — operation demonstrated.
- [ ] Common report: title, contents with page numbers and responsible member, introduction, architecture diagram, implementation, database diagram, validation/errors, API documentation, authentication/authorization, Git history, references.
- [ ] Explain at least three APIs in the report; mark responsible sections with full names.
- [ ] Document where and why AI assistance was used in the report's References, as the assignment requires.
- [ ] Real Git contribution evidence from all members; do not invent history or results.
- [ ] All members attend a 30-minute CREATES session at least three days before the deadline and apply feedback.
- [ ] Package source, database/scripts, Postman JSON and common report; include GitHub link/history evidence. Each student uploads the common work to Moodle.

Submission naming: StudentFullName1-StudentFullName2-StudentFullName3-430L. Confirm the deadline and teammates' exact names before preparing the final package.
