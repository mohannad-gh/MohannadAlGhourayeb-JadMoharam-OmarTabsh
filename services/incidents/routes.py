"""Jad Moharam — all six Incident Management APIs."""
from flask import Blueprint, g
from common.audit_client import audit_event
from common.jad_support import (ApiError, CATEGORIES, SEVERITIES, INCIDENT_STATUSES,
    body, changed, deny, enum, incident_access, integer, now, protect, queue,
    record, repo, text, user)
from common.responses import success

bp = Blueprint('jad_incidents', __name__)


def incident(incident_id):
    return repo().one('SELECT * FROM incidents WHERE incident_id=?', (incident_id,), 'Incident not found')


# Jad Moharam — Create Incident
@bp.post('/incidents')
@protect('admin', 'user')
def create():
    data = body(('title', 'description', 'category', 'severity', 'asset_id'), ('reporter_id',))
    reporter = integer(data.get('reporter_id', g.current_user['user_id']), 'reporter_id')
    if g.current_user['role'] == 'user' and reporter != g.current_user['user_id']:
        deny('Users cannot report incidents under another identity')
    user(reporter)
    asset = integer(data['asset_id'], 'asset_id')
    repo().asset(asset)
    values = (text(data['title'], 'title', 200), text(data['description'], 'description'),
              enum(data['category'], 'category', CATEGORIES), enum(data['severity'], 'severity', SEVERITIES),
              reporter, asset, now())
    with repo().connect(write=True) as conn:
        ident = conn.execute('INSERT INTO incidents(title,description,category,severity,reporter_id,asset_id,created_at) '
                             'VALUES(?,?,?,?,?,?,?)', values).lastrowid
        record(conn, 'INCIDENT_CREATED', f'Incident {ident} created')
    return changed(incident(ident), 'Incident created', 201)


# Jad Moharam — Retrieve All Incidents (list in data for Omar's Reports service)
@bp.get('/incidents')
@protect('admin', 'auditor')
def all_incidents():
    rows = repo().all('SELECT * FROM incidents ORDER BY incident_id DESC')
    return success(rows, count=len(rows))


# Jad Moharam — Retrieve Specific Incident, including Investigation Notes
@bp.get('/incidents/<int:incident_id>')
@protect('admin', 'analyst', 'user', 'auditor')
def detail(incident_id):
    row = incident(incident_id)
    incident_access(row)
    row['notes'] = repo().all('SELECT * FROM investigation_notes WHERE incident_id=? ORDER BY note_id', (incident_id,))
    return success(row)


# Jad Moharam — Assign Incident to Security Analyst
@bp.put('/incidents/<int:incident_id>/assign')
@protect('admin')
def assign(incident_id):
    data = body(('analyst_id',))
    analyst_id = integer(data['analyst_id'], 'analyst_id')
    analyst = user(analyst_id)
    if analyst['role'] != 'analyst':
        raise ApiError('Assigned user must have the Security Analyst role')
    row = incident(incident_id)
    if row['status'] == 'Closed':
        raise ApiError('Closed incidents cannot be reassigned', 409)
    if row['assigned_analyst_id'] == analyst_id:
        raise ApiError('Incident is already assigned to this analyst', 409)
    # Never call Omar's HTTP writer while holding a SQLite write lock.
    # This record authorizes the assignment; successful commit is queued below.
    if not audit_event('INCIDENT_ASSIGNMENT_AUTHORIZED',
            f'Assignment authorized: incident {incident_id} to analyst {analyst_id}',
            user_id=g.current_user['user_id']):
        raise ApiError('Assignment cancelled: audit service is unavailable', 503)
    with repo().connect(write=True) as conn:
        updated = conn.execute('UPDATE incidents SET assigned_analyst_id=? WHERE incident_id=? '
            'AND assigned_analyst_id IS ? AND status=?',
            (analyst_id, incident_id, row['assigned_analyst_id'], row['status']))
        if not updated.rowcount:
            raise ApiError('Incident changed concurrently; retrieve it and retry', 409)
        record(conn, 'INCIDENT_ASSIGNED', f'Incident {incident_id} assigned to analyst {analyst_id}')
        queue(conn, 'notification', dict(user_id=analyst_id, title='Incident assignment',
            message=f'You were assigned incident {incident_id}: {row["title"]}',
            type='Incident Assignment', severity=row['severity']))
    return changed(incident(incident_id), 'Incident assigned')


# Jad Moharam — Update Incident Status
@bp.put('/incidents/<int:incident_id>/status')
@protect('admin', 'analyst')
def status(incident_id):
    data = body(('status',))
    target = enum(data['status'], 'status', INCIDENT_STATUSES)
    incident_access(incident(incident_id))
    with repo().connect(write=True) as conn:
        raw = conn.execute('SELECT * FROM incidents WHERE incident_id=?', (incident_id,)).fetchone()
        if raw is None:
            raise ApiError('Incident not found', 404)
        row = dict(raw)
        # Recheck after acquiring the write lock to reject concurrent reassignment.
        if g.current_user['role'] == 'analyst' and row['assigned_analyst_id'] != g.current_user['user_id']:
            raise ApiError('Incident was reassigned; retrieve it and retry', 409)
        index = INCIDENT_STATUSES.index(row['status'])
        if index == len(INCIDENT_STATUSES)-1 or target != INCIDENT_STATUSES[index+1]:
            raise ApiError('Invalid incident status transition')
        resolved = now() if target == 'Resolved' else row['resolved_at']
        conn.execute('UPDATE incidents SET status=?,resolved_at=? WHERE incident_id=?', (target, resolved, incident_id))
        record(conn, 'INCIDENT_STATUS_CHANGED', f'Incident {incident_id}: {row["status"]} -> {target}')
    return changed(incident(incident_id), 'Incident status updated')


# Jad Moharam — Add Investigation Note
@bp.post('/incidents/<int:incident_id>/notes')
@protect('admin', 'analyst')
def notes(incident_id):
    data = body(('content',))
    content = text(data['content'], 'content')
    incident_access(incident(incident_id))
    with repo().connect(write=True) as conn:
        row = conn.execute('SELECT * FROM incidents WHERE incident_id=?', (incident_id,)).fetchone()
        if row is None:
            raise ApiError('Incident not found', 404)
        if g.current_user['role'] == 'analyst' and row['assigned_analyst_id'] != g.current_user['user_id']:
            raise ApiError('Incident was reassigned; retrieve it and retry', 409)
        ident = conn.execute('INSERT INTO investigation_notes(incident_id,analyst_id,content,created_at) VALUES(?,?,?,?)',
                             (incident_id, g.current_user['user_id'], content, now())).lastrowid
        record(conn, 'INCIDENT_NOTE_ADDED', f'Note {ident} added to incident {incident_id}')
    return changed(repo().one('SELECT * FROM investigation_notes WHERE note_id=?', (ident,)), 'Investigation note added', 201)
