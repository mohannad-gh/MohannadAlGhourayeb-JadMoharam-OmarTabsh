-- Tables owned by Omar Tabsh's services (SQLite)
-- Omar Tabsh - 202400798
--
-- The services create these tables automatically on start-up; this script documents
-- the structure and can be run by hand:  sqlite3 database/security_system.db < database/schema_omar_tabsh.sql
-- The Security Reports service (Service 6) has no table: reports are computed on request.

-- Service 4: Threat Intelligence
CREATE TABLE IF NOT EXISTS threats (
    threat_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    threat_type  TEXT NOT NULL CHECK (threat_type IN ('IP Address', 'Domain', 'File Hash', 'Malware Signature', 'Other')),
    threat_value TEXT NOT NULL,
    description  TEXT NOT NULL,
    severity     TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    source       TEXT NOT NULL,
    date_added   TEXT NOT NULL,              -- UTC 'YYYY-MM-DD HH:MM:SS'
    last_updated TEXT,
    UNIQUE (threat_type, threat_value)       -- no duplicate indicators
);

-- Service 5: Security Audit Logging
CREATE TABLE IF NOT EXISTS logs (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,                 -- refers to users.user_id (relationship not enforced, see docs)
    action          TEXT NOT NULL,
    description     TEXT NOT NULL,
    timestamp       TEXT NOT NULL,           -- UTC 'YYYY-MM-DD HH:MM:SS'
    severity        TEXT NOT NULL CHECK (severity IN ('Information', 'Warning', 'Error', 'Critical')),
    related_service TEXT NOT NULL
);

-- Audit logs can never be modified after creation
CREATE TRIGGER IF NOT EXISTS logs_are_immutable
BEFORE UPDATE ON logs
BEGIN
    SELECT RAISE(ABORT, 'Audit log records are immutable and cannot be modified');
END;

CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs (user_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp);
