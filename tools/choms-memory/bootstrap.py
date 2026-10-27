"""Explicit fresh-only bootstrap and scoped apply on the authorized control plane.
Input: JSON {objects: [...]} containing sanitized versioned memory resources.
Secrets are generated remotely in process memory and supplied over stdin only.
Existing credentials are never read, printed or rotated. Partial state fails closed.
"""
import json,subprocess,secrets,base64,sys
bundle=json.load(sys.stdin)
objects=bundle['objects']
ns='choms-memory'
def k(args,data=None,ok=(0,),timeout=60):
 p=subprocess.run(['kubectl','--request-timeout=25s','-n',ns]+args,input=data,text=True,capture_output=True,timeout=timeout)
 if p.returncode not in ok:raise RuntimeError('kubernetes_operation_failed_exit_'+str(p.returncode))
 return p.stdout

def pg(query):
 return k(['exec','-i','deployment/postgresql','--','sh','-c','PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X -U postgres -d cognee -v ON_ERROR_STOP=1 -At'],query).strip()

manifest=json.dumps({'apiVersion':'v1','kind':'List','items':objects})
k(['apply','--dry-run=server','-f','-'],manifest)
print('CHECK_PASS server_dry_run',flush=True)
diff=k(['diff','-f','-'],manifest,ok=(0,1))
# Only explicitly named memory resources are sent; the diff never includes Secret payloads.
print('CHECK_PASS scoped_diff resources='+str(len(objects)),flush=True)
role=pg("SELECT count(*) FROM pg_roles WHERE rolname='choms_memory_adapter'")
schema=pg("SELECT count(*) FROM pg_namespace WHERE nspname='choms_memory'")
secret=k(['get','secret','choms-memory-runtime','--ignore-not-found','-o','name']).strip()
if role=='0' and schema=='0' and not secret:
 password=secrets.token_hex(32)
 data={'database-password':password,'codex':secrets.token_hex(32),'hermes':secrets.token_hex(32)}
 s={'apiVersion':'v1','kind':'Secret','metadata':{'name':'choms-memory-runtime','namespace':ns,'labels':{'app.kubernetes.io/name':'choms-memory'}},'type':'Opaque','data':{key:base64.b64encode(value.encode()).decode() for key,value in data.items()}}
 k(['apply','--dry-run=server','-f','-'],json.dumps(s))
 pg("BEGIN; CREATE ROLE choms_memory_adapter LOGIN PASSWORD '"+password+"' NOSUPERUSER NOCREATEDB NOCREATEROLE; GRANT CONNECT,CREATE ON DATABASE cognee TO choms_memory_adapter; CREATE SCHEMA choms_memory AUTHORIZATION choms_memory_adapter; COMMIT;")
 k(['apply','-f','-'],json.dumps(s))
 print('CHECK_PASS isolated_role_secret_bootstrap',flush=True)
elif not (role=='1' and schema=='1' and secret):raise RuntimeError('bootstrap_state_ambiguous')
if pg("SELECT r.rolname FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner WHERE n.nspname='choms_memory'")!='choms_memory_adapter':raise RuntimeError('shared_schema_rejected')
k(['apply','-f','-'],manifest)
try:k(['rollout','status','deployment/choms-memory','--timeout=160s'],timeout=180)
except Exception:
 p=json.loads(k(['get','pods','-l','app.kubernetes.io/name=choms-memory','-o','json']))['items']
 for item in p:
  for st in item['status'].get('containerStatuses',[]):
   print(json.dumps({'reason':st.get('state',{}).get('waiting',{}).get('reason'),'terminated_exit':st.get('lastState',{}).get('terminated',{}).get('exitCode')}),flush=True)
 logs=k(['logs','deployment/choms-memory','--tail=5'],ok=(0,1))
 for line in logs.splitlines():
  try:
   value=json.loads(line)
   if set(value)<= {'event','class','code'}:print(json.dumps(value),flush=True)
  except ValueError:pass
 raise
pod=json.loads(k(['get','pods','-l','app.kubernetes.io/name=choms-memory','-o','json']))['items'][0]
st=pod['status']['containerStatuses'][0]
print(json.dumps({'stage':'central_ready','node':pod['spec']['nodeName'],'ready':st['ready'],'restarts':st['restartCount'],'image':pod['spec']['containers'][0]['image'],'imageID':st['imageID']}),flush=True)
