"""Jad Moharam — all six Security Playbook and Response Automation APIs."""
from flask import Blueprint, g
from common.jad_support import (ApiError, ACTION_STATUSES, CATEGORIES, SEVERITIES,
    body, changed, enum, integer, now, protect, record, repo, text, user)
from common.responses import success

bp = Blueprint('jad_playbooks', __name__)


def playbook(playbook_id):
    return repo().one('SELECT * FROM playbooks WHERE playbook_id=?', (playbook_id,), 'Playbook not found')


def action(action_id):
    return repo().one('SELECT * FROM response_actions WHERE action_id=?', (action_id,), 'Response action not found')


def assignee(value):
    if value is None:
        return None
    row = user(integer(value, 'assigned_user_id'))
    if row['role'] not in ('admin', 'analyst'):
        raise ApiError('Response actions must be assigned to an active administrator or analyst')
    return value


def history(conn, row, event, old=None):
    old = old or {}
    conn.execute('INSERT INTO action_history(action_id,playbook_id,actor_id,event,old_status,new_status,'
        'old_assigned_user_id,new_assigned_user_id,description,step_number,changed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
        (row['action_id'], row['playbook_id'], g.current_user['user_id'], event, old.get('status'),
         row['status'], old.get('assigned_user_id'), row['assigned_user_id'], row['description'], row['step_number'], now()))


# Jad Moharam — Create Response Playbook
@bp.post('/playbooks')
@protect('admin')
def create():
    data = body(('name', 'description', 'incident_category', 'severity'))
    values = (text(data['name'], 'name', 200), text(data['description'], 'description'),
              enum(data['incident_category'], 'incident_category', CATEGORIES),
              enum(data['severity'], 'severity', SEVERITIES), g.current_user['user_id'], now())
    with repo().connect(write=True) as conn:
        ident = conn.execute('INSERT INTO playbooks(name,description,incident_category,severity,created_by,created_at) '
                             'VALUES(?,?,?,?,?,?)', values).lastrowid
        record(conn, 'PLAYBOOK_CREATED', f'Playbook {ident} created')
    return changed(playbook(ident), 'Playbook created', 201)


# Jad Moharam — Retrieve All Playbooks
@bp.get('/playbooks')
@protect('admin', 'analyst', 'auditor')
def all_playbooks():
    rows = repo().all('SELECT * FROM playbooks ORDER BY playbook_id DESC')
    return success(rows, count=len(rows))


# Jad Moharam — Retrieve Specific Playbook and Ordered Actions
@bp.get('/playbooks/<int:playbook_id>')
@protect('admin', 'analyst', 'auditor')
def detail(playbook_id):
    row = playbook(playbook_id)
    actions = repo().all('SELECT * FROM response_actions WHERE playbook_id=? ORDER BY step_number', (playbook_id,))
    for item in actions:
        item['history'] = repo().all('SELECT * FROM action_history WHERE action_id=? ORDER BY history_id', (item['action_id'],))
    row['actions'] = actions
    row['progress'] = {'total': len(actions), 'completed': sum(a['status'] == 'Completed' for a in actions)}
    return success(row)


# Jad Moharam — Add Response Action (explicit authorization list includes Analysts)
@bp.post('/playbooks/<int:playbook_id>/actions')
@protect('admin', 'analyst')
def add_action(playbook_id):
    data = body(('description', 'step_number'), ('assigned_user_id',))
    description = text(data['description'], 'description')
    step = integer(data['step_number'], 'step_number')
    assigned = assignee(data.get('assigned_user_id'))
    with repo().connect(write=True) as conn:
        if conn.execute('SELECT 1 FROM playbooks WHERE playbook_id=?', (playbook_id,)).fetchone() is None:
            raise ApiError('Playbook not found', 404)
        existing = conn.execute('SELECT COALESCE(MAX(step_number),0) FROM response_actions WHERE playbook_id=?', (playbook_id,)).fetchone()[0]
        if step <= existing:
            raise ApiError('Duplicate step number', 409)
        if step != existing + 1:
            raise ApiError(f'Next step_number must be {existing+1}')
        ident = conn.execute('INSERT INTO response_actions(playbook_id,description,step_number,assigned_user_id) VALUES(?,?,?,?)',
                             (playbook_id, description, step, assigned)).lastrowid
        row = dict(conn.execute('SELECT * FROM response_actions WHERE action_id=?', (ident,)).fetchone())
        history(conn, row, 'created')
        record(conn, 'RESPONSE_ACTION_ADDED', f'Action {ident} added to playbook {playbook_id}')
    return changed(action(ident), 'Response action added', 201)


# Jad Moharam — Update Response Action Status and Assignment
@bp.put('/actions/<int:action_id>/status')
@protect('admin', 'analyst')
def status(action_id):
    data = body((), ('status', 'assigned_user_id', 'completed_at'))
    assigned = assignee(data['assigned_user_id']) if 'assigned_user_id' in data else None
    supplied_completion = None
    if 'completed_at' in data and data['completed_at'] is not None:
        from datetime import datetime, timezone
        try:
            stamp = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
            if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
                raise ValueError()
            supplied_completion = stamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        except (AttributeError, TypeError, ValueError):
            raise ApiError('completed_at must be a valid timezone-aware date, not in the future')
    with repo().connect(write=True) as conn:
        raw = conn.execute('SELECT * FROM response_actions WHERE action_id=?', (action_id,)).fetchone()
        if raw is None:
            raise ApiError('Response action not found', 404)
        old = dict(raw)
        row = dict(old)
        target = enum(data.get('status', old['status']), 'status', ACTION_STATUSES)
        if old['status'] == 'Completed':
            raise ApiError('Completed actions are immutable', 409)
        if target != old['status'] and ACTION_STATUSES.index(target) != ACTION_STATUSES.index(old['status'])+1:
            raise ApiError('Invalid action status transition')
        if 'assigned_user_id' in data:
            row['assigned_user_id'] = assigned
        if target != 'Pending':
            if row['assigned_user_id'] is None:
                raise ApiError('Assign a user before starting or completing an action')
            earlier = conn.execute("SELECT 1 FROM response_actions WHERE playbook_id=? AND step_number<? AND status!='Completed'",
                                   (row['playbook_id'], row['step_number'])).fetchone()
            if earlier:
                raise ApiError('Complete earlier actions before starting this step')
        if 'completed_at' in data and target != 'Completed':
            raise ApiError('completed_at may be supplied only when completing an action')
        row['status'] = target
        row['completed_at'] = (supplied_completion or now()) if target == 'Completed' else None
        conn.execute('UPDATE response_actions SET status=?,assigned_user_id=?,completed_at=? WHERE action_id=?',
                     (row['status'], row['assigned_user_id'], row['completed_at'], action_id))
        history(conn, row, 'updated', old)
        record(conn, 'RESPONSE_ACTION_UPDATED', f'Action {action_id}: {old["status"]} -> {target}')
    return changed(action(action_id), 'Response action updated')


# Jad Moharam — Delete Playbook, Retaining Execution History
@bp.delete('/playbooks/<int:playbook_id>')
@protect('admin')
def delete(playbook_id):
    with repo().connect(write=True) as conn:
        if conn.execute('SELECT 1 FROM playbooks WHERE playbook_id=?', (playbook_id,)).fetchone() is None:
            raise ApiError('Playbook not found', 404)
        for row in conn.execute('SELECT * FROM response_actions WHERE playbook_id=?', (playbook_id,)).fetchall():
            history(conn, dict(row), 'deleted', dict(row))
        conn.execute('DELETE FROM playbooks WHERE playbook_id=?', (playbook_id,))
        record(conn, 'PLAYBOOK_DELETED', f'Playbook {playbook_id} deleted; action history retained')
    return changed({'playbook_id': playbook_id}, 'Playbook deleted')
