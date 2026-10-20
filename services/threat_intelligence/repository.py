# Service 4 - Threat Intelligence: database access for the threats table
# Omar Tabsh - 202400798

import sqlite3
from datetime import datetime, timezone

from common.database import connect
from services.threat_intelligence.models import SEVERITIES, THREAT_TYPES


class DuplicateThreatError(Exception):
    def __init__(self, existing_id):
        super().__init__("Duplicate threat indicator")
        self.existing_id = existing_id


def _sql_list(values):
    return ", ".join(f"'{value}'" for value in values)


class ThreatRepository:
    """All SQL for threats lives here. Every query uses ? placeholders (no SQL injection)."""

    COLUMNS = ("threat_id", "threat_type", "threat_value", "description",
               "severity", "source", "date_added", "last_updated")

    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        return connect(self.db_path)

    def create_table(self):
        with self._connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS threats (
                    threat_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_type  TEXT NOT NULL CHECK (threat_type IN ({_sql_list(THREAT_TYPES)})),
                    threat_value TEXT NOT NULL,
                    description  TEXT NOT NULL,
                    severity     TEXT NOT NULL CHECK (severity IN ({_sql_list(SEVERITIES)})),
                    source       TEXT NOT NULL,
                    date_added   TEXT NOT NULL,
                    last_updated TEXT,
                    UNIQUE (threat_type, threat_value)
                )""")

    def _to_dict(self, row):
        return {column: row[column] for column in self.COLUMNS} if row else None

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def find_by_indicator(self, threat_type, threat_value):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM threats WHERE threat_type = ? AND threat_value = ?",
                               (threat_type, threat_value)).fetchone()
        return self._to_dict(row)

    def add(self, threat):
        existing = self.find_by_indicator(threat["threat_type"], threat["threat_value"])
        if existing:
            raise DuplicateThreatError(existing["threat_id"])
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO threats (threat_type, threat_value, description, severity, source, date_added) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (threat["threat_type"], threat["threat_value"], threat["description"],
                     threat["severity"], threat["source"], self._now()))
                new_id = cur.lastrowid
        except sqlite3.IntegrityError:
            # Two identical requests at the same moment: the UNIQUE constraint is the final guard
            existing = self.find_by_indicator(threat["threat_type"], threat["threat_value"])
            raise DuplicateThreatError(existing["threat_id"] if existing else None)
        return self.get_by_id(new_id)

    def get_all(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM threats ORDER BY threat_id").fetchall()
        return [self._to_dict(row) for row in rows]

    def get_by_id(self, threat_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM threats WHERE threat_id = ?", (threat_id,)).fetchone()
        return self._to_dict(row)

    def search(self, threat_type=None, threat_value=None, severity=None, source=None):
        """Type and severity must match exactly; value and source match partially (case-insensitive)."""
        conditions, params = [], []
        if threat_type:
            conditions.append("threat_type = ?")
            params.append(threat_type)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if threat_value:
            conditions.append("threat_value LIKE ? ESCAPE '\\'")
            params.append(f"%{_escape_like(threat_value)}%")
        if source:
            conditions.append("source LIKE ? ESCAPE '\\'")
            params.append(f"%{_escape_like(source)}%")

        query = "SELECT * FROM threats"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY threat_id"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._to_dict(row) for row in rows]

    def update(self, threat_id, changes):
        """changes only ever contains description/severity/source (checked by the validator)."""
        assignments = ", ".join(f"{field} = ?" for field in changes)
        with self._connect() as conn:
            conn.execute(f"UPDATE threats SET {assignments}, last_updated = ? WHERE threat_id = ?",
                         (*changes.values(), self._now(), threat_id))
        return self.get_by_id(threat_id)

    def delete(self, threat_id):
        with self._connect() as conn:
            deleted = conn.execute("DELETE FROM threats WHERE threat_id = ?", (threat_id,)).rowcount
        return deleted > 0


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
