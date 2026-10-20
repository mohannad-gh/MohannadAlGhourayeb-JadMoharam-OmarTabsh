# Windows run guide — Jad Moharam

The local branch is `jad-moharam`. It includes Omar's original commits and Jad's services. The local `.env`, demo database, virtual environment and token export are ignored by Git.

## Start

Open PowerShell in this project folder. Dependencies are installed in `.venv`.

Terminal 1 — Omar's Audit Logging:

```powershell
.\.venv\Scripts\python.exe -m services.audit_logging.app
```

Terminal 2 — all three Jad services:

```powershell
.\.venv\Scripts\python.exe run.py
```

Incidents runs on 5003, Notifications on 5008, Playbooks on 5009. Ctrl+C stops the launcher and its three children. To start Omar's Threats, Logs and Reports together instead, use `python -m scripts.run_tabsh_services` in terminal 1. Do not start Audit Logging twice on port 5005.

## Postman

1. Import `postman/JadMoharam-Services.postman_collection.json`.
2. Refresh the expiring local tokens with `.\.venv\Scripts\python.exe -m scripts.export_jad_demo_environment`.
3. Import `postman/JadMoharam.local.postman_environment.json` and select **Jad Moharam - Local Demo**. This file contains private bearer tokens; it is ignored by Git.
4. Run the five collection folders in order. There are 47 requests covering all 18 APIs, lifecycle transitions, negative cases and cleanup. IDs are saved automatically.
5. Capture actual request/response screenshots and database before/after evidence yourself. Caption each with `Jad Moharam — API title — operation`.

The local `.env` points to **database/jad_demo.db**, with separate development fixture users/assets. These records are not Mohannad's user-management implementation. Final authentication evidence must use his real login endpoint once available.

Demo identities: admin 1, analyst 2, regular user 3, auditor 4, another analyst 5, another regular user 6, suspended analyst 7. Asset 1 is a demo workstation. No passwords or login endpoint are supplied by Jad's fixture script.

## A fresh checkout

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set private `JWT_SECRET_KEY` and `SERVICE_API_KEY` values in `.env`. Share the actual agreed values privately with teammates. For standalone development, set `DATABASE_PATH` to the absolute path of `database/jad_demo.db`, then run:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_jad_demo
.\.venv\Scripts\python.exe -m scripts.export_jad_demo_environment
```

The seed command refuses a pre-existing unmarked database. It never drops tables or resets team data. Do not point it at the team's real database.

## Tests and pending deliveries

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.retry_jad_outbox
```

Retry sends up to 100 pending events per service per run. Run it again if pending events remain. Audit/notification failures return warnings; messages persist in `jad_outbox`. Assignment authorization specifically fails with 503 if Omar's audit service is unavailable.

`JAD_ROUTE_PREFIX=/jad-moharam` optionally adds the full-name URL prefix. Set Postman service URL variables to include that prefix, and set `NOTIFICATIONS_SERVICE_URL=http://127.0.0.1:5008/jad-moharam` and `INCIDENTS_SERVICE_URL=http://127.0.0.1:5003/jad-moharam` so internal notifications and Omar's reports use matching URLs. Confirm the professor's exact full-name route interpretation.
