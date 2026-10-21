"""Real HTTP integration: Jad's services with Omar's Logs and Reports."""
import sqlite3

import requests

from common.auth import create_token
from common.jad_support import flush_outbox
from scripts.seed_jad_demo import seed_demo
from services.audit_logging.app import create_app as logs
from services.incidents.app import create_app as incidents
from services.notifications.app import create_app as notifications
from services.security_reports.app import create_app as reports
from tests.test_integration import LiveServer


def test_assignment_delivers_notification_and_reports_match_database(tmp_path):
    path=str(tmp_path/'http.db'); seed_demo(path)
    servers=[]
    def serve(app):
        server=LiveServer(app); servers.append(server)
        return server
    admin={'Authorization':'Bearer '+create_token(1,'admin_dev','admin')}
    analyst={'Authorization':'Bearer '+create_token(2,'analyst_dev','analyst')}
    auditor={'Authorization':'Bearer '+create_token(4,'auditor_dev','auditor')}
    session=requests.Session(); session.trust_env=False
    try:
        audit=serve(logs({'DATABASE_PATH':path}))
        notification=serve(notifications({'DATABASE_PATH':path,'LOGS_SERVICE_URL':audit.url}))
        app=incidents({'DATABASE_PATH':path,'LOGS_SERVICE_URL':audit.url,
                       'NOTIFICATIONS_SERVICE_URL':notification.url})
        incident=serve(app)
        report=serve(reports({'LOGS_SERVICE_URL':audit.url,'SERVICE_URLS':{'incidents':incident.url}}))
        response=session.post(incident.url+'/incidents',headers=admin,json={
            'title':'HTTP phishing','description':'Investigate real request',
            'category':'Phishing','severity':'High','asset_id':1},timeout=10)
        assert response.status_code==201,response.text
        ident=response.json()['data']['incident_id']
        response=session.put(f'{incident.url}/incidents/{ident}/assign',headers=admin,json={'analyst_id':2},timeout=10)
        assert response.status_code==200 and response.json()['warnings']==[],response.text
        notices=session.get(notification.url+'/notifications/user/2',headers=analyst,timeout=10).json()['data']
        assert len(notices)==1 and notices[0]['type']=='Incident Assignment'
        response=session.get(report.url+'/reports/incidents',headers=auditor,timeout=10)
        assert response.status_code==200,response.text
        assert response.json()['data']['incidents_by_severity']['High']==1
        # A notification outage leaves a durable message, without losing the assignment.
        app.config['NOTIFICATIONS_SERVICE_URL']='http://127.0.0.1:9'
        response=session.put(f'{incident.url}/incidents/{ident}/assign',headers=admin,json={'analyst_id':5},timeout=10)
        assert response.status_code==200 and response.json()['warnings']
        app.config['NOTIFICATIONS_SERVICE_URL']=notification.url
        with app.app_context():
            assert flush_outbox()==[]
        with sqlite3.connect(path) as conn:
            assert conn.execute('SELECT count(*) FROM notifications').fetchone()[0]==2
            assert conn.execute("SELECT count(*) FROM logs WHERE action='INCIDENT_ASSIGNED'").fetchone()[0]==2
            assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
        # Mandatory audit failure cancels an assignment rather than silently accepting it.
        app.config['LOGS_SERVICE_URL']='http://127.0.0.1:9'
        response=session.put(f'{incident.url}/incidents/{ident}/assign',headers=admin,json={'analyst_id':2},timeout=10)
        assert response.status_code==503
        assert session.get(f'{incident.url}/incidents/{ident}',headers=admin,timeout=10).json()['data']['assigned_analyst_id']==5
    finally:
        session.close()
        for server in reversed(servers):
            server.stop()
            server.server.server_close()
