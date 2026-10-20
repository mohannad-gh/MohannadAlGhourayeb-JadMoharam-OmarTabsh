"""Jad Moharam: real password login, real Assets, and all three Jad services over HTTP."""
import importlib
import json
import os
import sqlite3
from pathlib import Path

import requests

from common import config
from scripts.run_team_services import prepare_database
from services.audit_logging.app import create_app as logs
from services.incidents.app import create_app as incidents
from services.notifications.app import create_app as notifications
from services.playbooks.app import create_app as playbooks
from services.threat_intelligence.app import create_app as threats
from services.security_reports.app import create_app as reports
from tests.test_integration import LiveServer


def test_real_users_login_assets_and_jad_services(tmp_path, monkeypatch):
    path, uri = prepare_database(tmp_path/'real-team.db')
    monkeypatch.setenv('TEAM_DATABASE_URI', uri)
    monkeypatch.setenv('JWT_SECRET_KEY', config.JWT_SECRET_KEY)
    users_module = importlib.import_module('services.users.app')
    assets_module = importlib.import_module('services.assets.app')
    servers=[]; evidence=[]
    session=requests.Session();session.trust_env=False
    def serve(app):
        server=LiveServer(app);servers.append(server);return server.url
    def redact(value):
        if isinstance(value,dict):return {k:('[redacted]' if k in ('password','access_token') else redact(v)) for k,v in value.items()}
        if isinstance(value,list):return [redact(v) for v in value]
        return value
    def call(url,method,route,expected,body=None,token=None):
        headers={'Authorization':'Bearer '+token} if token else {}
        r=session.request(method,url+route,json=body,headers=headers,timeout=15)
        data=r.json()
        evidence.append({'method':method,'path':route,'request':redact(body),'status':r.status_code,'expected':expected,'response':redact(data)})
        assert r.status_code==expected, (route,r.status_code,data)
        return data
    try:
        users=serve(users_module.app);assets=serve(assets_module.app)
        log=serve(logs({'DATABASE_PATH':str(path)}))
        notice=serve(notifications({'DATABASE_PATH':str(path),'LOGS_SERVICE_URL':log}))
        incident=serve(incidents({'DATABASE_PATH':str(path),'LOGS_SERVICE_URL':log,'NOTIFICATIONS_SERVICE_URL':notice}))
        playbook=serve(playbooks({'DATABASE_PATH':str(path),'LOGS_SERVICE_URL':log}))
        threat=serve(threats({'DATABASE_PATH':str(path),'LOGS_SERVICE_URL':log}))
        report=serve(reports({'LOGS_SERVICE_URL':log,'SERVICE_URLS':{'users':users,'assets':assets,'incidents':incident,'threats':threat,'logs':log,'vulnerabilities':'http://127.0.0.1:9'}}))
        ids={};tokens={}
        for name,role in [('admin','Security Administrator'),('analyst','Security Analyst'),('employee','Regular User'),('auditor','Auditor')]:
            data=call(users,'POST','/users/register',201,{'full_name':'Team '+name,'username':'team_'+name,'email':name+'@example.test','password':'LocalEvidence2026!','department':'Security'})
            ids[name]=data['user_id']
            # Test administrator provisioning only. Registration remains Regular User.
            with sqlite3.connect(path) as conn:conn.execute('UPDATE users SET role=? WHERE id=?',(role,ids[name]))
            data=call(users,'POST','/users/login',200,{'username':'team_'+name,'password':'LocalEvidence2026!'})
            tokens[name]=data['access_token']
        call(users,'POST','/users/login',401,{'username':'team_employee','password':'IncorrectPassword!'})
        data=call(assets,'POST','/assets',201,{'asset_name':'Real team workstation','asset_type':'Workstation','department':'Security','owner_id':ids['employee'],'criticality':'High'},tokens['admin'])
        asset_id=data['asset']['asset_id']
        data=call(incident,'POST','/incidents',201,{'title':'Real login incident','description':'Integration with submitted Users and Assets','category':'Phishing','severity':'High','asset_id':asset_id},tokens['employee'])
        iid=data['data']['incident_id']
        call(incident,'PUT',f'/incidents/{iid}/assign',200,{'analyst_id':ids['analyst']},tokens['admin'])
        data=call(notice,'GET',f'/notifications/user/{ids["analyst"]}',200,token=tokens['analyst'])
        assert data['data'][0]['type']=='Incident Assignment'
        call(incident,'GET',f'/incidents/{iid}',200,token=tokens['analyst'])
        call(incident,'GET','/incidents',403,token=tokens['employee'])
        for status in ('Under Investigation','Mitigated','Resolved','Closed'):
            call(incident,'PUT',f'/incidents/{iid}/status',200,{'status':status},tokens['analyst'])
        call(incident,'POST',f'/incidents/{iid}/notes',201,{'content':'Real analyst login verified'},tokens['analyst'])
        data=call(playbook,'POST','/playbooks',201,{'name':'Real login playbook','description':'Team verification','incident_category':'Phishing','severity':'High'},tokens['admin'])
        pid=data['data']['playbook_id']
        data=call(playbook,'POST',f'/playbooks/{pid}/actions',201,{'description':'Investigate email','step_number':1,'assigned_user_id':ids['analyst']},tokens['analyst'])
        aid=data['data']['action_id']
        for status in ('In Progress','Completed'):
            call(playbook,'PUT',f'/actions/{aid}/status',200,{'status':status},tokens['analyst'])
        data=call(report,'GET','/reports/summary',200,token=tokens['auditor'])
        assert data['data']['users']==4 and data['data']['assets']==1
        call(report,'GET','/reports/assets',200,token=tokens['auditor'])
        call(report,'GET','/reports/incidents',200,token=tokens['auditor'])
        call(report,'GET','/reports/vulnerabilities',503,token=tokens['auditor'])
        with sqlite3.connect(path) as conn:conn.execute("UPDATE users SET account_status='Suspended' WHERE id=?",(ids['employee'],))
        call(users,'POST','/users/login',403,{'username':'team_employee','password':'LocalEvidence2026!'})
        call(incident,'GET',f'/incidents/{iid}',401,token=tokens['employee'])
        with sqlite3.connect(path) as conn:
            conn.execute("UPDATE users SET role='Regular User' WHERE id=?",(ids['analyst'],))
        call(playbook,'GET',f'/playbooks/{pid}',401,token=tokens['analyst'])
        with sqlite3.connect(path) as conn:
            assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
            assert conn.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0].startswith('$2')
        if os.environ.get('JAD_TEAM_EVIDENCE_PATH'):
            Path(os.environ['JAD_TEAM_EVIDENCE_PATH']).write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    finally:
        session.close()
        for server in reversed(servers):server.stop();server.server.server_close()
