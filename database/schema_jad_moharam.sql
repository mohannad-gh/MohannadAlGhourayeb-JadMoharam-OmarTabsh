-- Jad Moharam: tables owned by services 3, 8 and 9.
-- Users(user_id, username, role, account_status) and Assets(asset_id) are
-- integration prerequisites owned by Mohannad, not created by this schema.
CREATE TABLE IF NOT EXISTS incidents (
 incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL, description TEXT NOT NULL, category TEXT NOT NULL,
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 reporter_id INTEGER NOT NULL REFERENCES users(user_id),
 asset_id INTEGER REFERENCES assets(asset_id),
 assigned_analyst_id INTEGER REFERENCES users(user_id),
 status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','Under Investigation','Mitigated','Resolved','Closed')),
 created_at TEXT NOT NULL, resolved_at TEXT
);
CREATE TABLE IF NOT EXISTS investigation_notes (
 note_id INTEGER PRIMARY KEY AUTOINCREMENT,
 incident_id INTEGER NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
 analyst_id INTEGER NOT NULL REFERENCES users(user_id),
 content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
 notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(user_id),
 title TEXT NOT NULL, message TEXT NOT NULL,
 type TEXT NOT NULL CHECK(type IN ('Incident Assignment','Security Alert','System Notification','Threat Alert','Vulnerability Alert')),
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 status TEXT NOT NULL DEFAULT 'Unread' CHECK(status IN ('Unread','Read')),
 created_at TEXT NOT NULL, read_at TEXT
);
CREATE TABLE IF NOT EXISTS playbooks (
 playbook_id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL COLLATE NOCASE UNIQUE, description TEXT NOT NULL,
 incident_category TEXT NOT NULL,
 severity TEXT NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
 created_by INTEGER NOT NULL REFERENCES users(user_id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS response_actions (
 action_id INTEGER PRIMARY KEY AUTOINCREMENT,
 playbook_id INTEGER NOT NULL REFERENCES playbooks(playbook_id) ON DELETE CASCADE,
 description TEXT NOT NULL, step_number INTEGER NOT NULL CHECK(step_number>0),
 status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Completed')),
 assigned_user_id INTEGER REFERENCES users(user_id), completed_at TEXT,
 UNIQUE(playbook_id,step_number)
);
-- Snapshots intentionally have no cascading FK: history survives deletion.
CREATE TABLE IF NOT EXISTS action_history (
 history_id INTEGER PRIMARY KEY AUTOINCREMENT,
 action_id INTEGER NOT NULL, playbook_id INTEGER NOT NULL,
 actor_id INTEGER NOT NULL, event TEXT NOT NULL,
 old_status TEXT, new_status TEXT, old_assigned_user_id INTEGER,
 new_assigned_user_id INTEGER, description TEXT NOT NULL, step_number INTEGER NOT NULL,
 changed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jad_outbox (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT,
 owner_service TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('audit','notification')),
 payload TEXT NOT NULL, created_at TEXT NOT NULL, delivered_at TEXT, claimed_until TEXT
);
CREATE INDEX IF NOT EXISTS idx_incidents_reporter ON incidents(reporter_id);
CREATE INDEX IF NOT EXISTS idx_incidents_analyst ON incidents(assigned_analyst_id);
CREATE INDEX IF NOT EXISTS idx_notes_incident ON investigation_notes(incident_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_history_action ON action_history(action_id);
