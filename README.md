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

- **Tokens:** use `POST /users/login`. Until the Users service is merged,
  `python -m scripts.dev_token` prints a development token for each role.
- **Postman:** import `postman/OmarTabsh-Services.postman_collection.json` and fill in
  the token variables and `service_key`.
- **Automated tests:** `python -m pytest`
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
requests. A separate, ignored `database/jad_demo.db` provides development fixtures
until Mohannad's real user/asset services are integrated; it does not implement
his services. Real Postman screenshots and real-login evidence remain to be collected.
