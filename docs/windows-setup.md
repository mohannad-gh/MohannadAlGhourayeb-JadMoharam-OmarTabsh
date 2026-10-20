# Windows setup — Jad Moharam

The local project is on branch `jad-moharam`, based on the team's restored initial commit. Nothing from this setup has been pushed.

Setup verification passed: the running Flask server returned HTTP 200 with the expected JSON, SQLite foreign keys were enabled, and no domain tables were created. This was a local HTTP check; Postman screenshots for the assignment are still to be collected. The verification server was stopped afterward.

## Run the starter

Open PowerShell in this project folder. A local `.venv` is prepared when setup completes; for a fresh checkout create it first with `py -m venv .venv`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe run.py
```

Using the environment's Python directly avoids changing PowerShell execution policy. SQLite is included with Python; no database server is needed. `DATABASE_PATH` is resolved relative to the project folder.

In Postman, send `GET http://127.0.0.1:5003/jad-moharam/health`.

Expected response: HTTP 200 with `{"database":"reachable","status":"ok"}`. This is an optional setup check, not one of the 18 assignment APIs. It opens SQLite and executes `SELECT 1`; no domain tables or test records are created.

Stop the server with Ctrl+C. Read `integration-agreement.md`, then use `implementation-checklist.md` to track the graded endpoints.

## Proposed structure

```text
common/                shared app, database, later identity and error helpers
services/incidents/    Jad: Service 3
services/notifications/ Jad: Service 8
services/playbooks/    Jad: Service 9
database/              shared schema and agreed seed scripts
postman/               documented requests and tests
docs/                  agreement, checklist, report and evidence planning
run.py                 local setup server
requirements.txt       dependencies
.env.example           nonsecret configuration template
```

Only setup files exist so far. Teammate service folders are not generated. Separate service entry points will be added when shared interfaces are confirmed.

## What each setup file does

- `run.py` loads local environment values and starts Flask on localhost.
- `common/factory.py` creates the app and registers the setup check.
- `common/db.py` opens one connection per request, uses named row access and enables foreign keys. Connections close when the request finishes. Future SQL must use placeholders, never string interpolation of request data.
- `.env.example` records variable names and safe local defaults. `.env` stays out of Git.
- `.gitignore` excludes local credentials, databases, environments and Python caches.

## Development steps

The next graded endpoint is `POST /notifications`. Before writing it, obtain the exact users-table schema, authentication verification interface and service-credential contract. Then define the notifications table, implement validation and permission checks, and run successful, unauthorized, missing-field and invalid-recipient cases in Postman.

When a verified change is ready:

```powershell
git status
git diff
git add <specific-files>
git commit -m "Describe the actual completed change"
```

Push your branch and open a pull request after reviewing the change with the team. No author or contribution evidence should be fabricated.
