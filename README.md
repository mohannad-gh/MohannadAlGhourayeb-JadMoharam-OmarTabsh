# MohannadAlGhourayeb-JadMoharam-OmarTabsh
Security Incident Detection and Response Management System - Sprint 1

## Team and services

| Student | Services |
|---|---|
| Mohannad Al Ghourayeb | 1 Users and Identity Management, 2 Asset Management, 7 Vulnerability Management |
| Jad Moharam | 3 Incident Management, 8 Notification and Alert Management, 9 Security Playbook and Response Automation |
| Omar Tabsh | 4 Threat Intelligence, 5 Security Audit Logging, 6 Security Reports |

Shared conventions (ports, tokens, audit events, response format) are in
[docs/INTEGRATION_CONTRACT.md](docs/INTEGRATION_CONTRACT.md).

## Setup

The `jad-moharam` branch now includes the latest `main` and Mohannad's submitted Users/Assets. After setup, run `python -m scripts.run_team_services` to start all eight available services on ports 5001-5006 and 5008-5009 using one fresh shared database. Service 7 is still pending. Real password login is verified with Jad's services; see [current integration details](docs/JAD_INTEGRATION_NOTES.md).

Run from the project root:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Windows  (macOS/Linux: cp .env.example .env), then set the secrets
```

## Omar Tabsh's services (4, 5, 6)

Start all three (Audit Logging first) with:

```bash
python -m scripts.run_tabsh_services
```

Or one per terminal:

```bash
python -m services.audit_logging.app        # http://127.0.0.1:5005
python -m services.threat_intelligence.app  # http://127.0.0.1:5004
python -m services.security_reports.app     # http://127.0.0.1:5006
```

- **Tokens:** use the actual `POST /users/login`. `python -m scripts.dev_token` is only for isolated development fixtures.
- **Postman:** import `postman/OmarTabsh-Services.postman_collection.json` and fill in
  the token variables and `service_key`.
- **Automated tests:** `python -m pytest`
- **Submission zip:** `python -m scripts.package_submission Final_Report.docx` creates
  `MohannadAlGhourayeb-JadMoharam-OmarTabsh-430L.zip` (code, database, Postman, report; never `.env`).
- **API documentation:** [docs/OMAR_TABSH_API_DOCUMENTATION.md](docs/OMAR_TABSH_API_DOCUMENTATION.md)
- **Database:** tables `threats` and `logs` in `database/security_system.db`
  (structure: [database/schema_omar_tabsh.sql](database/schema_omar_tabsh.sql)).

## Jad Moharam's services (3, 8, 9)

All 18 APIs are implemented: Incidents on 5003, Notifications on 5008,
and Playbooks on 5009. This development branch includes Omar's services and
shared helpers with his original commit history.

Start Omar's Audit Logging service, then run Jad's services from a second terminal:

```powershell
.\.venv\Scripts\python.exe -m services.audit_logging.app
# Second terminal:
.\.venv\Scripts\python.exe run.py
```

- [Windows setup and Postman instructions](docs/windows-setup.md)
- [All 18 API contracts and database relationships](docs/JAD_API_DOCUMENTATION.md)
- [Integration with Omar and prerequisites for Mohannad](docs/JAD_INTEGRATION_NOTES.md)
- [Implementation and remaining submission checklist](docs/implementation-checklist.md)
- [Verification results](docs/JAD_VERIFICATION.md)

Import `postman/JadMoharam-Services.postman_collection.json` for the 47 ordered
requests. A separate, ignored `database/jad_demo.db` remains available for historical fixture-based tests. Use the team launcher with a fresh shared database for real Users/Assets integration. Native Postman screenshots of all 18 Jad operations and a sanitized real-login integration execution log accompany the shared report under `submission/`.
