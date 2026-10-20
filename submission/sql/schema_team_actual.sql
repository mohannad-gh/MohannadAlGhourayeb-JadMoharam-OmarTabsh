-- Actual schema of the isolated nine-service integration database
PRAGMA foreign_keys=ON;

CREATE TABLE users (
	id INTEGER NOT NULL,
	full_name VARCHAR(150) NOT NULL,
	username VARCHAR(80) NOT NULL,
	email VARCHAR(150) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	department VARCHAR(100) NOT NULL,
	role VARCHAR(30) NOT NULL,
	account_status VARCHAR(20) NOT NULL,
	created_date DATETIME,
	last_login_date DATETIME,
	PRIMARY KEY (id),
	UNIQUE (username),
	UNIQUE (email)
);

CREATE TABLE assets (
	id INTEGER NOT NULL,
	asset_name VARCHAR(150) NOT NULL,
	asset_type VARCHAR(80) NOT NULL,
	ip_address VARCHAR(45),
	department VARCHAR(100) NOT NULL,
	owner_id INTEGER NOT NULL,
	criticality VARCHAR(20) NOT NULL,
	status VARCHAR(30) NOT NULL,
	created_date DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE vulnerabilities (
	id INTEGER NOT NULL,
	title VARCHAR(200) NOT NULL,
	description TEXT NOT NULL,
	cve_id VARCHAR(30),
	asset_id INTEGER NOT NULL,
	severity VARCHAR(20) NOT NULL,
	cvss_score FLOAT,
	status VARCHAR(30) NOT NULL,
	remediation TEXT,
	discovered_date DATETIME,
	updated_date DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE logs (
                    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER,           -- logical reference to users.user_id
                    action          TEXT NOT NULL,
                    description     TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,     -- UTC, 'YYYY-MM-DD HH:MM:SS'
                    severity        TEXT NOT NULL CHECK (severity IN ('Information', 'Warning', 'Error', 'Critical')),
                    related_service TEXT NOT NULL
                );

CREATE TABLE incidents (
 incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL, description TEXT NOT NULL, category TEXT NOT NULL,
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 reporter_id INTEGER NOT NULL REFERENCES users(id),
 asset_id INTEGER REFERENCES assets(id),
 assigned_analyst_id INTEGER REFERENCES users(id),
 status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','Under Investigation','Mitigated','Resolved','Closed')),
 created_at TEXT NOT NULL, resolved_at TEXT
);

CREATE TABLE investigation_notes (
 note_id INTEGER PRIMARY KEY AUTOINCREMENT,
 incident_id INTEGER NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
 analyst_id INTEGER NOT NULL REFERENCES users(id),
 content TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE TABLE notifications (
 notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id),
 title TEXT NOT NULL, message TEXT NOT NULL,
 type TEXT NOT NULL CHECK(type IN ('Incident Assignment','Security Alert','System Notification','Threat Alert','Vulnerability Alert')),
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 status TEXT NOT NULL DEFAULT 'Unread' CHECK(status IN ('Unread','Read')),
 created_at TEXT NOT NULL, read_at TEXT
);

CREATE TABLE playbooks (
 playbook_id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL COLLATE NOCASE UNIQUE, description TEXT NOT NULL,
 incident_category TEXT NOT NULL,
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 created_by INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL
);

CREATE TABLE response_actions (
 action_id INTEGER PRIMARY KEY AUTOINCREMENT,
 playbook_id INTEGER NOT NULL REFERENCES playbooks(playbook_id) ON DELETE CASCADE,
 description TEXT NOT NULL, step_number INTEGER NOT NULL CHECK(step_number>0),
 status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Completed')),
 assigned_user_id INTEGER REFERENCES users(id), completed_at TEXT,
 UNIQUE(playbook_id,step_number)
);

CREATE TABLE action_history (
 history_id INTEGER PRIMARY KEY AUTOINCREMENT,
 action_id INTEGER NOT NULL, playbook_id INTEGER NOT NULL,
 actor_id INTEGER NOT NULL, event TEXT NOT NULL,
 old_status TEXT, new_status TEXT, old_assigned_user_id INTEGER,
 new_assigned_user_id INTEGER, description TEXT NOT NULL, step_number INTEGER NOT NULL,
 changed_at TEXT NOT NULL
);

CREATE TABLE jad_outbox (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT,
 owner_service TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('audit','notification')),
 payload TEXT NOT NULL, created_at TEXT NOT NULL, delivered_at TEXT, claimed_until TEXT
);

CREATE TABLE threats (
                    threat_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_type  TEXT NOT NULL CHECK (threat_type IN ('IP Address', 'Domain', 'File Hash', 'Malware Signature', 'Other')),
                    threat_value TEXT NOT NULL,
                    description  TEXT NOT NULL,
                    severity     TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
                    source       TEXT NOT NULL,
                    date_added   TEXT NOT NULL,
                    last_updated TEXT,
                    UNIQUE (threat_type, threat_value)
                );

CREATE INDEX idx_logs_user_id ON logs (user_id);

CREATE INDEX idx_logs_timestamp ON logs (timestamp);

CREATE INDEX idx_incidents_reporter ON incidents(reporter_id);

CREATE INDEX idx_incidents_analyst ON incidents(assigned_analyst_id);

CREATE INDEX idx_notes_incident ON investigation_notes(incident_id);

CREATE INDEX idx_notifications_user ON notifications(user_id);

CREATE INDEX idx_history_action ON action_history(action_id);

CREATE TRIGGER logs_are_immutable
                BEFORE UPDATE ON logs
                BEGIN
                    SELECT RAISE(ABORT, 'Audit log records are immutable and cannot be modified');
                END;
