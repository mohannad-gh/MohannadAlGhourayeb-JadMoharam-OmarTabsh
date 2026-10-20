"""Flask setup only: domain APIs are added one at a time."""

import os
from pathlib import Path

from flask import Flask, jsonify

from common.db import close_db, get_db


def create_app():
    app = Flask(__name__)
    root = Path(__file__).resolve().parents[1]
    database = Path(os.getenv("DATABASE_PATH", "database/security.db"))
    if not database.is_absolute():
        database = root / database
    database.parent.mkdir(parents=True, exist_ok=True)
    app.config["DATABASE_PATH"] = str(database)
    app.teardown_appcontext(close_db)

    # Jad Moharam - optional local setup check; not one of the 18 graded APIs.
    @app.get("/jad-moharam/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return jsonify(status="ok", database="reachable")

    return app
