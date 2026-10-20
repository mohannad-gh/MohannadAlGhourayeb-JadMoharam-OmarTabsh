# Service 5 - Security Audit Logging: database access for the logs table
# Omar Tabsh - 202400798
#
# Immutability: there is no update method, the API has no update route, and a
# database trigger rejects any UPDATE on the logs table, even from a SQL tool.
#
# logs.user_id refers to users.user_id (Users service). The relationship is shown
# in the schema but deliberately NOT enforced with a FOREIGN KEY constraint:
#   - an enforced key would block deleting any user who has logs, or (with CASCADE)
#     erase that user's audit trail, and
#   - failed logins with an unknown username have no user (user_id is NULL).

from datetime import datetime, timezone

from common.audit_events import LOG_SEVERITIES
from common.database import connect


class AuditLogRepository:

    COLUMNS = ("log_id", "user_id", "action", "description", "timestamp", "severity", "related_service")

    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        return connect(self.db_path)

    def create_table(self):
        severities = ", ".join(f"'{severity}'" for severity in LOG_SEVERITIES)
        with self._connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS logs (
                    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER,           -- logical reference to users.user_id
                    action          TEXT NOT NULL,
                    description     TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,     -- UTC, 'YYYY-MM-DD HH:MM:SS'
                    severity        TEXT NOT NULL CHECK (severity IN ({severities})),
                    related_service TEXT NOT NULL
                )""")
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS logs_are_immutable
                BEFORE UPDATE ON logs
                BEGIN
                    SELECT RAISE(ABORT, 'Audit log records are immutable and cannot be modified');
                END""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs (user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp)")

    def _to_dict(self, row):
        return {column: row[column] for column in self.COLUMNS} if row else None

    def add(self, entry):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            new_id = conn.execute(
                "INSERT INTO logs (user_id, action, description, timestamp, severity, related_service) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (entry["user_id"], entry["action"], entry["description"], timestamp,
                 entry["severity"], entry["related_service"])).lastrowid
        return self.get_by_id(new_id)

    def get_all(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM logs ORDER BY log_id DESC").fetchall()
        return [self._to_dict(row) for row in rows]

    def get_by_id(self, log_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM logs WHERE log_id = ?", (log_id,)).fetchone()
        return self._to_dict(row)

    def get_by_user(self, user_id):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM logs WHERE user_id = ? ORDER BY log_id DESC",
                                (user_id,)).fetchall()
        return [self._to_dict(row) for row in rows]

    def search(self, user_id=None, date=None, date_from=None, date_to=None,
               action=None, severity=None, related_service=None):
        conditions, params = [], []
        for column, value in (("user_id", user_id), ("action", action),
                              ("severity", severity), ("related_service", related_service)):
            if value is not None:
                conditions.append(f"{column} = ?")
                params.append(value)
        # substr(timestamp, 1, 10) is the 'YYYY-MM-DD' part of the timestamp
        if date:
            conditions.append("substr(timestamp, 1, 10) = ?")
            params.append(date)
        if date_from:
            conditions.append("substr(timestamp, 1, 10) >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("substr(timestamp, 1, 10) <= ?")
            params.append(date_to)

        query = "SELECT * FROM logs"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY log_id DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._to_dict(row) for row in rows]

    def delete(self, log_id):
        with self._connect() as conn:
            deleted = conn.execute("DELETE FROM logs WHERE log_id = ?", (log_id,)).rowcount
        return deleted > 0
