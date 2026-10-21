"""Separate development fixtures, not Mohannad's user/asset implementation.

Creates only an empty or previously marked demo database; never resets team data.
Run: python -m scripts.seed_jad_demo
"""
import argparse
import sqlite3
from pathlib import Path


def seed_demo(path):
    Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables and 'jad_demo_marker' not in tables:
            raise RuntimeError('Refusing to modify an existing non-demo database')
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS jad_demo_marker (version INTEGER);
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL, account_status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assets (
                asset_id INTEGER PRIMARY KEY, asset_name TEXT NOT NULL);
        ''')
        conn.executemany('INSERT OR IGNORE INTO users VALUES(?,?,?,?)', [
            (1, 'admin_dev', 'admin', 'Active'), (2, 'analyst_dev', 'analyst', 'Active'),
            (3, 'user_dev', 'user', 'Active'), (4, 'auditor_dev', 'auditor', 'Active'),
            (5, 'analyst2_dev', 'analyst', 'Active'), (6, 'user2_dev', 'user', 'Active'),
            (7, 'suspended_dev', 'analyst', 'Suspended')])
        conn.execute("INSERT OR IGNORE INTO assets VALUES(1,'Demo workstation')")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='database/jad_demo.db')
    args = parser.parse_args()
    seed_demo(args.database)
    print(f'Demo fixture database ready: {args.database}. No user login API is provided.')
