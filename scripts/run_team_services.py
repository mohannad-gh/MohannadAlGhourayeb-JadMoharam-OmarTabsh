"""Jad Moharam: launch all nine real services against one SQLite file."""
import os
import subprocess
import sys
import sqlite3
from pathlib import Path

from flask import Flask
from common import config


def prepare_database(path):
    from services.users.models import db as users_db
    from services.assets.models import db as assets_db
    from services.vulnerabilities.models import db as vulnerability_db
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with sqlite3.connect(path) as conn:
            columns = {row[1] for row in conn.execute('PRAGMA table_info(users)')}
        if columns and 'id' not in columns:
            raise RuntimeError('This is an older fixture database. Set DATABASE_PATH to a fresh team database; existing data was not changed.')
    uri = 'sqlite:///' + path.as_posix()
    for db in (users_db, assets_db, vulnerability_db):
        app = Flask('team_database_setup')
        app.config['SQLALCHEMY_DATABASE_URI'] = uri
        db.init_app(app)
        with app.app_context():
            db.create_all()
    return path, uri


def main():
    path, uri = prepare_database(config.DATABASE_PATH)
    env = dict(os.environ, DATABASE_PATH=str(path), TEAM_DATABASE_URI=uri,
               JWT_SECRET_KEY=config.JWT_SECRET_KEY, SERVICE_API_KEY=config.SERVICE_API_KEY)
    modules = ('audit_logging', 'users', 'assets', 'incidents', 'threat_intelligence',
               'security_reports', 'vulnerabilities', 'notifications', 'playbooks')
    children = []
    try:
        # Importing the two original applications preserves their implementation;
        # app.run here disables debug reload subprocesses for deterministic shutdown.
        for name in modules:
            port = {'audit_logging':5005, 'users':5001, 'assets':5002, 'incidents':5003,
                    'threat_intelligence':5004, 'security_reports':5006, 'vulnerabilities':5007,
                    'notifications':5008, 'playbooks':5009}[name]
            factory = 'app' if name in ('users','assets','vulnerabilities') else 'create_app()'
            code = f'from services.{name}.app import {"app" if factory == "app" else "create_app"}; {factory}.run(host="127.0.0.1", port={port}, use_reloader=False)'
            children.append(subprocess.Popen([sys.executable, '-c', code], env=env, cwd=config.BASE_DIR))
        print(f'Nine services use {path}.', flush=True)
        for child in children:
            child.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            child.wait()


if __name__ == '__main__':
    main()
