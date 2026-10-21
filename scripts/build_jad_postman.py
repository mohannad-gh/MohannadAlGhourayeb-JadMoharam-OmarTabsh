"""Build Jad Moharam's documented, ordered Postman collection."""
import json
from pathlib import Path

COLLECTION = 'postman/JadMoharam-Services.postman_collection.json'
FOLDERS = {}


def add(folder, name, service, method, path, role='admin', payload=None, expected=200, capture=None, description=''):
    token = '{{'+role+'_token}}'
    request = {'method':method,'header':[],
               'url':'{{'+service+'_url}}'+path,
               'description': description or f'{name}. Expected HTTP {expected}; requires the documented role and valid record ownership.'}
    if role != 'none':
        request['header'].append({'key':'Authorization','value':'Bearer '+token,'type':'text'})
    if payload is not None:
        request['header'].append({'key':'Content-Type','value':'application/json','type':'text'})
        request['body']={'mode':'raw','raw':json.dumps(payload,indent=2),'options':{'raw':{'language':'json'}}}
    tests=[f'pm.test("HTTP {expected}", () => pm.response.to.have.status({expected}));',
           'pm.test("JSON response", () => pm.response.to.be.json);',
           f'pm.test("Response status", () => pm.expect(pm.response.json().status).to.eql("{"success" if expected<400 else "error"}"));']
    if capture:
        variable,field=capture
        tests.append(f'if (pm.response.code === {expected}) pm.collectionVariables.set("{variable}", pm.response.json().data.{field});')
    FOLDERS.setdefault(folder,[]).append({'name':'Jad Moharam - '+name,'request':request,
        'event':[{'listen':'test','script':{'type':'text/javascript','exec':tests}}]})


def build():
    FOLDERS.clear()
    add('1 Notifications','Create Notification','notifications','POST','/notifications',payload={
        'user_id':3,'title':'Security alert','message':'Review suspicious email','type':'Security Alert','severity':'High'},expected=201,capture=('notification_id','notification_id'),
        description='Admin creates a notification. Required: user_id, title, message, type and severity. Authorized services may instead use X-Service-Key. Invalid fields: 400; unknown recipient: 404.')
    add('1 Notifications','Retrieve User Notifications','notifications','GET','/notifications/user/3',role='user')
    add('1 Notifications','Retrieve Specific Notification','notifications','GET','/notifications/{{notification_id}}',role='user')
    add('1 Notifications','Mark Notification Read','notifications','PUT','/notifications/{{notification_id}}/read',role='user')
    add('1 Notifications','Search Notifications','notifications','GET','/notifications/search?user_id=3&type=Security%20Alert&severity=High&status=Read')
    add('2 Incidents','Create Incident','incidents','POST','/incidents',payload={
        'title':'Suspicious email','description':'Investigate a reported phishing message','category':'Phishing','severity':'High','reporter_id':3,'asset_id':1},
        expected=201,capture=('incident_id','incident_id'),description='Admin or regular user creates an incident. Regular users can report only under their own identity. Creates status Open and server timestamp; existing asset and reporter are required.')
    add('2 Incidents','Retrieve All Incidents','incidents','GET','/incidents',role='auditor')
    add('2 Incidents','Retrieve Specific Incident','incidents','GET','/incidents/{{incident_id}}',role='user')
    add('2 Incidents','Assign Incident','incidents','PUT','/incidents/{{incident_id}}/assign',payload={'analyst_id':2},
        description='Admin assigns an active analyst. Requires Omar Audit Logging on 5005; 503 cancels assignment if audit authorization fails. Assignment queues a notification on 5008; warning means delivery is saved for retry.')
    for status in ('Under Investigation','Mitigated','Resolved','Closed'):
        add('2 Incidents','Set Incident '+status,'incidents','PUT','/incidents/{{incident_id}}/status',role='analyst',payload={'status':status})
    add('2 Incidents','Add Investigation Note','incidents','POST','/incidents/{{incident_id}}/notes',role='analyst',payload={'content':'Email headers preserved; sender investigated.'},expected=201)
    add('2 Incidents','Retrieve Incident with Notes','incidents','GET','/incidents/{{incident_id}}',role='auditor')
    add('3 Playbooks','Create Playbook','playbooks','POST','/playbooks',payload={
        'name':'Phishing response {{$timestamp}}','description':'Investigate and isolate affected systems',
        'incident_category':'Phishing','severity':'High'},expected=201,capture=('playbook_id','playbook_id'))
    add('3 Playbooks','Retrieve All Playbooks','playbooks','GET','/playbooks',role='analyst')
    add('3 Playbooks','Retrieve Specific Playbook','playbooks','GET','/playbooks/{{playbook_id}}',role='auditor')
    add('3 Playbooks','Add Response Action','playbooks','POST','/playbooks/{{playbook_id}}/actions',role='analyst',payload={
        'description':'Investigate malicious email','step_number':1,'assigned_user_id':2},expected=201,capture=('action_id','action_id'),
        description='Admin/analyst adds the next consecutive step. Positive, unique step_number and nonempty description are required; optional assigned_user_id must be an active admin or analyst.')
    for status in ('In Progress','Completed'):
        add('3 Playbooks','Set Action '+status,'playbooks','PUT','/actions/{{action_id}}/status',role='analyst',payload={'status':status},
            description='Admin/analyst updates status, optional assigned_user_id or completed_at. Progression is Pending -> In Progress -> Completed. Prior steps must be complete. Completion time defaults to server time. History is retained.')
    negatives=[
        ('Missing Token','incidents','GET','/incidents','none',None,401),
        ('Analyst Cannot List All Incidents','incidents','GET','/incidents','analyst',None,403),
        ('Other User Cannot Read Incident','incidents','GET','/incidents/{{incident_id}}','other_user',None,403),
        ('Missing Incident','incidents','GET','/incidents/999999','admin',None,404),
        ('Invalid Incident Severity','incidents','POST','/incidents','admin',{'title':'X','description':'X','category':'Malware','severity':'Extreme','asset_id':1},400),
        ('User Cannot Assign','incidents','PUT','/incidents/{{incident_id}}/assign','user',{'analyst_id':2},403),
        ('Invalid Analyst Role','incidents','PUT','/incidents/{{incident_id}}/assign','admin',{'analyst_id':3},400),
        ('Reject Backward Lifecycle','incidents','PUT','/incidents/{{incident_id}}/status','admin',{'status':'Open'},400),
        ('Empty Investigation Note','incidents','POST','/incidents/{{incident_id}}/notes','admin',{'content':' '},400),
        ('Other User Cannot Read Notification','notifications','GET','/notifications/{{notification_id}}','other_user',None,403),
        ('Auditor Cannot Mark Read','notifications','PUT','/notifications/{{notification_id}}/read','auditor',None,403),
        ('Invalid Notification Type','notifications','POST','/notifications','admin',{'user_id':3,'title':'X','message':'X','type':'Email','severity':'Low'},400),
        ('Empty Notification Request','notifications','POST','/notifications','admin',{},400),
        ('Missing Notification','notifications','GET','/notifications/999999','admin',None,404),
        ('User Cannot Delete Notification','notifications','DELETE','/notifications/{{notification_id}}','user',None,403),
        ('Analyst Cannot Search Others','notifications','GET','/notifications/search?user_id=3','analyst',None,403),
        ('Invalid Notification Filter','notifications','GET','/notifications/search?status=Maybe','admin',None,400),
        ('User Cannot Access Playbooks','playbooks','GET','/playbooks','user',None,403),
        ('Missing Playbook','playbooks','GET','/playbooks/999999','admin',None,404),
        ('Duplicate Step','playbooks','POST','/playbooks/{{playbook_id}}/actions','admin',{'description':'Duplicate','step_number':1},409),
        ('Step Gap','playbooks','POST','/playbooks/{{playbook_id}}/actions','admin',{'description':'Gap','step_number':3},400),
        ('Invalid Action Status','playbooks','PUT','/actions/{{action_id}}/status','admin',{'status':'Done'},400),
        ('Missing Action','playbooks','PUT','/actions/999999/status','admin',{'status':'In Progress'},404),
        ('Analyst Cannot Delete Playbook','playbooks','DELETE','/playbooks/{{playbook_id}}','analyst',None,403),
    ]
    for name,service,method,path,role,payload,expected in negatives:
        add('4 Negative cases',name,service,method,path,role,payload,expected)
    add('5 Cleanup','Delete Notification','notifications','DELETE','/notifications/{{notification_id}}')
    add('5 Cleanup','Delete Playbook','playbooks','DELETE','/playbooks/{{playbook_id}}')
    variables=[{'key':s+'_url','value':f'http://127.0.0.1:{p}'} for s,p in [('incidents',5003),('notifications',5008),('playbooks',5009)]]
    variables += [{'key':role+'_token','value':''} for role in ('admin','analyst','user','auditor','other_user')]
    collection={'info':{'name':'Jad Moharam - Services 3, 8 and 9',
        'schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
        'description':'Run folders in order against the separate demo database or compatible team data. Set tokens from real login for final evidence; temporary development tokens are supported until Mohannad merges Users. No response examples are presented as execution evidence.'},
        'variable':variables,'item':[{'name':name,'item':items} for name,items in FOLDERS.items()]}
    Path(COLLECTION).write_text(json.dumps(collection,indent=2),encoding='utf-8')
    print(f'Wrote {COLLECTION}: {sum(len(items) for items in FOLDERS.values())} requests')


if __name__=='__main__':
    build()
