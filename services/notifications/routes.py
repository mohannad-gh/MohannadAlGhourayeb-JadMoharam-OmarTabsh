"""Jad Moharam — all six Notification and Alert Management APIs."""
from flask import Blueprint, g, request
from common.jad_support import (ApiError, TYPES, SEVERITIES, body, changed,
    enum, integer, now, personal_access, protect, record, repo, text, user)
from common.responses import success

bp = Blueprint('jad_notifications', __name__)


def notification(notification_id):
    return repo().one('SELECT * FROM notifications WHERE notification_id=?',
                     (notification_id,), 'Notification not found')


# Jad Moharam — Create Notification
@bp.post('/notifications')
@protect('admin', allow_service=True)
def create():
    data = body(('user_id', 'title', 'message', 'type', 'severity'))
    user_id = integer(data['user_id'], 'user_id')
    user(user_id)
    values = (user_id, text(data['title'], 'title', 200), text(data['message'], 'message'),
              enum(data['type'], 'type', TYPES), enum(data['severity'], 'severity', SEVERITIES), now())
    with repo().connect(write=True) as conn:
        ident = conn.execute('INSERT INTO notifications(user_id,title,message,type,severity,created_at) '
                             'VALUES(?,?,?,?,?,?)', values).lastrowid
        record(conn, 'NOTIFICATION_CREATED', f'Notification {ident} created for user {user_id}')
    return changed(notification(ident), 'Notification created', 201)


# Jad Moharam — Retrieve User Notifications
@bp.get('/notifications/user/<int:user_id>')
@protect('admin', 'analyst', 'user', 'auditor')
def by_user(user_id):
    personal_access({'user_id': user_id})
    user(user_id, active=False)
    rows = repo().all('SELECT * FROM notifications WHERE user_id=? ORDER BY notification_id DESC', (user_id,))
    return success(rows, 'Notifications retrieved' if rows else 'No notifications found', count=len(rows))


# Jad Moharam — Retrieve Specific Notification
@bp.get('/notifications/<int:notification_id>')
@protect('admin', 'analyst', 'user', 'auditor')
def detail(notification_id):
    row = notification(notification_id)
    personal_access(row)
    return success(row)


# Jad Moharam — Mark Notification as Read
@bp.put('/notifications/<int:notification_id>/read')
@protect('admin', 'analyst', 'user')
def read(notification_id):
    row = notification(notification_id)
    personal_access(row)
    if request.content_length:
        raise ApiError('This endpoint does not accept a request body')
    with repo().connect(write=True) as conn:
        result = conn.execute("UPDATE notifications SET status='Read',read_at=? "
                              "WHERE notification_id=? AND status='Unread'", (now(), notification_id))
        if result.rowcount:
            record(conn, 'NOTIFICATION_READ', f'Notification {notification_id} marked read')
    return changed(notification(notification_id), 'Notification marked as read')


# Jad Moharam — Search Notifications
@bp.get('/notifications/search')
@protect('admin', 'analyst', 'auditor')
def search():
    unknown = request.args.keys() - {'user_id', 'type', 'severity', 'status'}
    if unknown or any(len(request.args.getlist(key)) != 1 for key in request.args):
        raise ApiError('Unknown or repeated search parameters')
    conditions, values = [], []
    requested_user = None
    if 'user_id' in request.args:
        raw = request.args['user_id']
        if not raw.isascii() or not raw.isdigit():
            raise ApiError('user_id must be a positive integer')
        requested_user = integer(int(raw), 'user_id')
    if g.current_user['role'] == 'analyst':
        requested_user = requested_user or g.current_user['user_id']
        personal_access({'user_id': requested_user})
    if requested_user is not None:
        conditions.append('user_id=?')
        values.append(requested_user)
    for field, choices in (('type', TYPES), ('severity', SEVERITIES), ('status', ('Unread', 'Read'))):
        if field in request.args:
            conditions.append(f'{field}=?')
            values.append(enum(request.args[field], field, choices))
    sql = 'SELECT * FROM notifications' + (' WHERE ' + ' AND '.join(conditions) if conditions else '')
    rows = repo().all(sql + ' ORDER BY notification_id DESC', values)
    return success(rows, count=len(rows))


# Jad Moharam — Delete Notification
@bp.delete('/notifications/<int:notification_id>')
@protect('admin')
def delete(notification_id):
    with repo().connect(write=True) as conn:
        result = conn.execute('DELETE FROM notifications WHERE notification_id=?', (notification_id,))
        if not result.rowcount:
            raise ApiError('Notification not found', 404)
        record(conn, 'NOTIFICATION_DELETED', f'Notification {notification_id} deleted')
    return changed({'notification_id': notification_id}, 'Notification deleted')
