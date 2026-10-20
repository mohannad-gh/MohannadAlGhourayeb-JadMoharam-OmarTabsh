"""Behavior and permission tests for Jad's 18 APIs using isolated fixtures."""
import sqlite3

import pytest

from common import config
from common.auth import create_token
from common.jad_support import flush_outbox
from scripts.seed_jad_demo import seed_demo
from services.incidents.app import create_app as incidents
from services.notifications.app import create_app as notifications
from services.playbooks.app import create_app as playbooks


@pytest.fixture
def jad(tmp_path):
    path = str(tmp_path / 'jad.db')
    seed_demo(path)
    events = []
    def audit(**event):
        events.append(event)
        return True
    apps = {name: factory(dict(TESTING=True, DATABASE_PATH=path, AUDIT_HOOK=audit,
                               NOTIFICATION_HOOK=lambda payload: True))
            for name, factory in [('i', incidents), ('n', notifications), ('p', playbooks)]}
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO incidents VALUES(1,'Phishing','Suspicious email','Phishing','High',3,1,2,'Open','2026-10-20T10:00:00Z',NULL)")
        conn.execute("INSERT INTO notifications VALUES(1,3,'Alert','Message','Security Alert','High','Unread','2026-10-20T10:00:00Z',NULL)")
        conn.execute("INSERT INTO notifications VALUES(2,2,'Assignment','Message','Incident Assignment','High','Unread','2026-10-20T10:00:00Z',NULL)")
        conn.execute("INSERT INTO playbooks VALUES(1,'Phishing response','Investigate','Phishing','High',1,'2026-10-20T10:00:00Z')")
        conn.execute("INSERT INTO response_actions VALUES(1,1,'Identify email',1,'Pending',2,NULL)")
    def headers(role, user_id=None):
        ident = user_id or {'admin':1, 'analyst':2, 'user':3, 'auditor':4}[role]
        return {'Authorization': 'Bearer ' + create_token(ident, role+'_dev', role)}
    return apps, path, events, headers


CASES = [
 ('i','POST','/incidents', {'title':'Malware','description':'Investigate','category':'Malware','severity':'High','asset_id':1}, {'admin','user'}),
 ('i','GET','/incidents',None, {'admin','auditor'}),
 ('i','GET','/incidents/1',None, {'admin','analyst','user','auditor'}),
 ('i','PUT','/incidents/1/assign',{'analyst_id':5}, {'admin'}),
 ('i','PUT','/incidents/1/status',{'status':'Under Investigation'}, {'admin','analyst'}),
 ('i','POST','/incidents/1/notes',{'content':'Evidence preserved'}, {'admin','analyst'}),
 ('n','POST','/notifications',{'user_id':3,'title':'Alert','message':'Investigate','type':'Security Alert','severity':'High'}, {'admin'}),
 ('n','GET','/notifications/user/3',None, {'admin','analyst','user','auditor'}),
 ('n','GET','/notifications/1',None, {'admin','analyst','user','auditor'}),
 ('n','PUT','/notifications/1/read',None, {'admin','analyst','user'}),
 ('n','GET','/notifications/search',None, {'admin','analyst','auditor'}),
 ('n','DELETE','/notifications/1',None, {'admin'}),
 ('p','POST','/playbooks',{'name':'Malware response','description':'Isolate','incident_category':'Malware','severity':'Critical'}, {'admin'}),
 ('p','GET','/playbooks',None, {'admin','analyst','auditor'}),
 ('p','GET','/playbooks/1',None, {'admin','analyst','auditor'}),
 ('p','POST','/playbooks/1/actions',{'description':'Isolate host','step_number':2}, {'admin','analyst'}),
 ('p','PUT','/actions/1/status',{'status':'In Progress'}, {'admin','analyst'}),
 ('p','DELETE','/playbooks/1',None, {'admin'}),
]


@pytest.mark.parametrize('service,method,path,payload,allowed', CASES)
@pytest.mark.parametrize('role', ['admin','analyst','user','auditor'])
def test_all_endpoint_permissions(jad, service, method, path, payload, allowed, role):
    apps, _, events, headers = jad
    if role == 'analyst' and service == 'n':
        path = path.replace('/user/3','/user/2').replace('/notifications/1','/notifications/2')
    response = apps[service].test_client().open(path, method=method, json=payload, headers=headers(role))
    if role in allowed:
        assert response.status_code in (200,201), response.json
    else:
        assert response.status_code == 403, response.json
        assert any(e['action']=='UNAUTHORIZED_ACCESS' for e in events)
    assert response.headers['X-Developed-By']=='Jad Moharam'


@pytest.mark.parametrize('service,method,path,payload,allowed', CASES)
@pytest.mark.parametrize('bad_header', [None, 'Bearer forged-token'])
def test_all_endpoints_require_identity(jad, service, method, path, payload, allowed, bad_header):
    apps, _, _, _ = jad
    headers = {'Authorization':bad_header} if bad_header else {}
    response = apps[service].test_client().open(path,method=method,json=payload,headers=headers)
    assert response.status_code==401


def test_incident_lifecycle_notes_and_ownership(jad):
    apps, path, events, headers = jad
    client=apps['i'].test_client()
    assert client.get('/incidents/1',headers=headers('analyst',5)).status_code==403
    assert client.get('/incidents/1',headers=headers('user',6)).status_code==403
    assert client.put('/incidents/1/status',json={'status':'Closed'},headers=headers('analyst')).status_code==400
    for status in ('Under Investigation','Mitigated','Resolved','Closed'):
        result=client.put('/incidents/1/status',json={'status':status},headers=headers('analyst'))
        assert result.status_code==200, result.json
    assert result.json['data']['resolved_at'] is not None
    assert client.put('/incidents/1/status',json={'status':'Open'},headers=headers('admin')).status_code==400
    result=client.post('/incidents/1/notes',json={'content':"O'Brien preserved the email"},headers=headers('analyst'))
    assert result.status_code==201
    assert client.get('/incidents/1',headers=headers('auditor')).json['data']['notes'][0]['content']=="O'Brien preserved the email"
    assert {'INCIDENT_STATUS_CHANGED','INCIDENT_NOTE_ADDED'} <= {event['action'] for event in events}
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT count(*) FROM investigation_notes').fetchone()[0]==1


def test_assignment_failure_and_retryable_notifications(jad):
    apps, path, events, headers=jad
    app=apps['i']; client=app.test_client()
    assert client.put('/incidents/1/assign',json={'analyst_id':3},headers=headers('admin')).status_code==400
    assert client.put('/incidents/1/assign',json={'analyst_id':7},headers=headers('admin')).status_code==403
    app.config['AUDIT_HOOK']=lambda **event: False
    assert client.put('/incidents/1/assign',json={'analyst_id':5},headers=headers('admin')).status_code==503
    assert client.get('/incidents/1',headers=headers('admin')).json['data']['assigned_analyst_id']==2
    app.config['AUDIT_HOOK']=lambda **event: True
    app.config['NOTIFICATION_HOOK']=lambda payload: False
    response=client.put('/incidents/1/assign',json={'analyst_id':5},headers=headers('admin'))
    assert response.status_code==200 and response.json['warnings']
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM jad_outbox WHERE kind='notification' AND delivered_at IS NULL").fetchone()[0]==1
    received=[]
    app.config['NOTIFICATION_HOOK']=lambda payload: received.append(payload) or True
    with app.app_context():
        assert flush_outbox()==[]
    assert len(received)==1 and received[0]['user_id']==5


def test_notification_privacy_filters_and_timestamps(jad):
    apps, _, _, headers=jad
    client=apps['n'].test_client()
    for method,path in [('GET','/notifications/1'),('PUT','/notifications/1/read'),('GET','/notifications/user/3')]:
        assert client.open(path,method=method,headers=headers('analyst')).status_code==403
    assert client.get('/notifications/search?user_id=3',headers=headers('analyst')).status_code==403
    assert client.get('/notifications/search',headers=headers('analyst')).json['count']==1
    assert client.get('/notifications/search?status=Unread&severity=High&type=Security%20Alert',headers=headers('admin')).json['count']==1
    assert client.get('/notifications/user/6',headers=headers('admin')).json['data']==[]
    a=client.put('/notifications/1/read',headers=headers('user')).json['data']
    b=client.put('/notifications/1/read',headers=headers('user')).json['data']
    assert a['status']=='Read' and a['read_at'] and a['read_at']==b['read_at']
    payload=CASES[6][3]
    assert client.post('/notifications',json=payload,headers={'X-Service-Key':config.SERVICE_API_KEY}).status_code==201
    assert client.post('/notifications',json=payload,headers={'X-Service-Key':'wrong'}).status_code==401


def test_playbook_order_history_and_deletion(jad):
    apps, path, _, headers=jad
    client=apps['p'].test_client(); auth=headers('analyst')
    assert client.post('/playbooks/1/actions',json={'description':'Gap','step_number':3},headers=auth).status_code==400
    assert client.post('/playbooks/1/actions',json={'description':'Duplicate','step_number':1},headers=auth).status_code==409
    result=client.post('/playbooks/1/actions',json={'description':'Isolate','step_number':2,'assigned_user_id':2},headers=auth)
    ident=result.json['data']['action_id']
    assert client.put(f'/actions/{ident}/status',json={'status':'In Progress'},headers=auth).status_code==400
    assert client.put('/actions/1/status',json={'status':'Completed'},headers=auth).status_code==400
    for action_id in (1,ident):
        for status in ('In Progress','Completed'):
            result=client.put(f'/actions/{action_id}/status',json={'status':status},headers=auth)
            assert result.status_code==200, result.json
    response=client.get('/playbooks/1',headers=headers('auditor')).json['data']
    assert [a['step_number'] for a in response['actions']]==[1,2]
    assert response['progress']=={'total':2,'completed':2}
    assert response['actions'][1]['history'][-1]['new_status']=='Completed'
    assert client.delete('/playbooks/1',headers=headers('admin')).status_code==200
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT count(*) FROM response_actions').fetchone()[0]==0
        assert conn.execute('SELECT count(*) FROM action_history').fetchone()[0]>=6


@pytest.mark.parametrize('service,method,path,payload', [
 ('i','POST','/incidents',{}),
 ('i','POST','/incidents',dict(CASES[0][3],severity='Extreme')),
 ('i','POST','/incidents',dict(CASES[0][3],asset_id=True)),
 ('i','POST','/incidents',dict(CASES[0][3],asset_id=999)),
 ('i','POST','/incidents',dict(CASES[0][3],reporter_id=999)),
 ('i','POST','/incidents/1/notes',{'content':' '}),
 ('n','POST','/notifications',dict(CASES[6][3],type='Email')),
 ('n','POST','/notifications',dict(CASES[6][3],user_id=999)),
 ('n','GET','/notifications/search?status=Unknown',None),
 ('n','GET','/notifications/search?user_id=1.5',None),
 ('n','GET','/notifications/search?status=Read&status=Unread',None),
 ('p','POST','/playbooks',dict(CASES[12][3],created_by=3)),
 ('p','POST','/playbooks/1/actions',{'description':'X','step_number':0}),
 ('p','PUT','/actions/1/status',{'status':'Done'}),
 ('p','PUT','/actions/1/status',{'completed_at':'nonsense'}),
])
def test_validation(jad,service,method,path,payload):
    apps,_,_,headers=jad
    response=apps[service].test_client().open(path,method=method,json=payload,headers=headers('admin'))
    assert response.status_code in (400,404), response.json
    assert response.json['status']=='error'


@pytest.mark.parametrize('service,method,path,payload', [
 ('i','GET','/incidents/999',None),
 ('i','PUT','/incidents/999/assign',{'analyst_id':2}),
 ('i','PUT','/incidents/999/status',{'status':'Under Investigation'}),
 ('i','POST','/incidents/999/notes',{'content':'Note'}),
 ('n','GET','/notifications/999',None),
 ('n','PUT','/notifications/999/read',None),
 ('n','DELETE','/notifications/999',None),
 ('p','GET','/playbooks/999',None),
 ('p','POST','/playbooks/999/actions',{'description':'X','step_number':1}),
 ('p','PUT','/actions/999/status',{'status':'In Progress'}),
 ('p','DELETE','/playbooks/999',None),
])
def test_missing_resources(jad,service,method,path,payload):
    apps,_,_,headers=jad
    assert apps[service].test_client().open(path,method=method,json=payload,headers=headers('admin')).status_code==404


def test_stale_role_suspended_and_sql_binding(jad):
    apps,path,_,headers=jad
    client=apps['n'].test_client()
    assert client.get('/notifications/search',headers=headers('analyst',7)).status_code==401
    assert client.get('/notifications/search',headers=headers('admin',3)).status_code==401
    assert client.get('/notifications/search',headers=headers('admin',999)).status_code==401
    payload=dict(CASES[6][3],title="Robert'); DROP TABLE users;--")
    assert client.post('/notifications',json=payload,headers=headers('admin')).status_code==201
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT count(*) FROM users').fetchone()[0]==7
    assert client.post('/notifications',json=[],headers=headers('admin')).status_code==400
    assert client.post('/notifications',data='broken json',content_type='application/json',headers=headers('admin')).status_code==400


def test_demo_seed_refuses_existing_team_database(tmp_path):
    path=str(tmp_path/'real.db')
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE users (user_id INTEGER PRIMARY KEY)')
    with pytest.raises(RuntimeError):
        seed_demo(path)


def test_full_name_prefix_and_foreign_key_enforcement(jad):
    apps,path,events,headers=jad
    app=incidents({'DATABASE_PATH':path,'JAD_ROUTE_PREFIX':'/jad-moharam','AUDIT_HOOK':lambda **event: True})
    assert app.test_client().get('/jad-moharam/incidents',headers=headers('auditor')).status_code==200
    assert app.test_client().get('/incidents',headers=headers('auditor')).status_code==404
    repository=apps['i'].extensions['jad_repository']
    with repository.connect() as conn:
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0]==1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO investigation_notes(incident_id,analyst_id,content,created_at) VALUES(999,2,'X','date')")


def test_outbox_claim_prevents_parallel_duplicate_delivery(jad):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from common.jad_support import queue
    apps,_,_,_=jad
    app=apps['i']; started=Event(); release=Event(); sent=[]
    def deliver(payload):
        sent.append(payload); started.set()
        assert release.wait(timeout=5)
        return True
    app.config['NOTIFICATION_HOOK']=deliver
    with app.app_context():
        with app.extensions['jad_repository'].connect(write=True) as conn:
            queue(conn,'notification',{'user_id':2})
    def flush():
        with app.app_context():
            return flush_outbox()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(flush)
        assert started.wait(timeout=5)
        second=pool.submit(flush)
        try:
            assert second.result(timeout=5)
        finally:
            release.set()
        assert first.result(timeout=5)==[]
    assert len(sent)==1
