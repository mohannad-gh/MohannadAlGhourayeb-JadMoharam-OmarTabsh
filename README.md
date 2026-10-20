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
