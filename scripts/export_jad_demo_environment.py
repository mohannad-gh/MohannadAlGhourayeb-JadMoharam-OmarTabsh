"""Export expiring development tokens locally; the generated file is ignored by Git."""
import json
from pathlib import Path
from common.auth import create_token


if __name__=='__main__':
    values=[]
    for variable,role,ident in [('admin','admin',1),('analyst','analyst',2),('user','user',3),
                                ('auditor','auditor',4),('other_user','user',6)]:
        values.append({'key':variable+'_token','value':create_token(ident,role+'_dev',role),'enabled':True,'type':'secret'})
    path=Path('postman/JadMoharam.local.postman_environment.json')
    path.write_text(json.dumps({'name':'Jad Moharam - Local Demo','values':values,
                                '_postman_variable_scope':'environment'},indent=2),encoding='utf-8')
    print(f'Local environment written to {path}. Import privately; tokens expire in 60 minutes.')
