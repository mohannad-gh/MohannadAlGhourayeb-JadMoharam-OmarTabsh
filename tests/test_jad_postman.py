"""Execute the actual exported collection's requests against live Flask apps."""
import json
import re
from pathlib import Path

import requests

from common.auth import create_token
from scripts.seed_jad_demo import seed_demo
from services.audit_logging.app import create_app as logs
from services.incidents.app import create_app as incidents
from services.notifications.app import create_app as notifications
from services.playbooks.app import create_app as playbooks
from tests.test_integration import LiveServer


def test_exported_postman_collection_over_real_http(tmp_path):
    path=str(tmp_path/'collection.db'); seed_demo(path)
    servers=[]
    def serve(app):
        server=LiveServer(app); servers.append(server); return server.url
    session=requests.Session(); session.trust_env=False
    variables={}
    def replace(value):
        return re.sub(r'\{\{([^}]+)\}\}',lambda match:str(variables[match.group(1)]),value)
    try:
        audit=serve(logs({'DATABASE_PATH':path}))
        notification=serve(notifications({'DATABASE_PATH':path,'LOGS_SERVICE_URL':audit}))
        variables['notifications_url']=notification
        variables['incidents_url']=serve(incidents({'DATABASE_PATH':path,'LOGS_SERVICE_URL':audit,'NOTIFICATIONS_SERVICE_URL':notification}))
        variables['playbooks_url']=serve(playbooks({'DATABASE_PATH':path,'LOGS_SERVICE_URL':audit}))
        variables['$timestamp']='test-collection'
        for key,role,ident in [('admin','admin',1),('analyst','analyst',2),('user','user',3),('auditor','auditor',4),('other_user','user',6)]:
            variables[key+'_token']=create_token(ident,role+'_dev',role)
        collection=json.loads((Path(__file__).resolve().parents[1]/'postman/JadMoharam-Services.postman_collection.json').read_text())
        executed=0
        for folder in collection['item']:
            for item in folder['item']:
                spec=item['request']
                headers={header['key']:replace(header['value']) for header in spec['header']}
                payload=replace(spec['body']['raw']) if 'body' in spec else None
                response=session.request(spec['method'],replace(spec['url']),headers=headers,data=payload,timeout=15)
                script='\n'.join(item['event'][0]['script']['exec'])
                expected=int(re.search(r'HTTP (\d+)',script).group(1))
                assert response.status_code==expected, (item['name'],response.status_code,response.text)
                body=response.json()
                assert body['status']==('success' if expected<400 else 'error')
                capture=re.search(r'collectionVariables.set\("([^"]+)", pm.response.json\(\).data.([a-z_]+)\)',script)
                if capture:
                    variables[capture[1]]=body['data'][capture[2]]
                executed+=1
        assert executed==47
    finally:
        session.close()
        for server in reversed(servers):
            server.stop(); server.server.server_close()
