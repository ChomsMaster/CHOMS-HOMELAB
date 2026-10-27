"""Explicitly authorized, synthetic-only Kubernetes integration gate. No real records."""
import base64,json,os,pathlib,secrets,subprocess,sys,time,hashlib
# Executed on node-01 with source-only payload on stdin; credentials stay in memory.
if '--remote-synthetic' not in sys.argv:
 import argparse,shlex
 parser=argparse.ArgumentParser(description='Isolated synthetic purge gate; never accepts real memories')
 parser.add_argument('--execute-synthetic',action='store_true',required=True)
 parser.add_argument('--ssh-target',required=True)
 args=parser.parse_args()
 import re
 if not re.fullmatch(r'[a-z_][a-z0-9_-]*@[a-zA-Z0-9.-]+',args.ssh_target):
  parser.error('invalid SSH destination')
 root=pathlib.Path(__file__).resolve().parents[2]
 bundle={n:(root/'tools/choms-memory'/n).read_text() for n in ('purge.py','gate_adapter.py')}
 command='python3 -c '+shlex.quote(pathlib.Path(__file__).read_text())+' --remote-synthetic'
 result=subprocess.run(['ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','ConnectTimeout=6',
  '-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','ForwardAgent=no',
  '-o','IdentityAgent=none',args.ssh_target,command],input=json.dumps(bundle),text=True)
 raise SystemExit(result.returncode)
bundle=json.loads(sys.stdin.read())
suffix=secrets.token_hex(6)
name='choms-memory-purge-'+suffix
schema='choms_memory_e2e_'+suffix
role=schema
password=secrets.token_hex(32)
access=secrets.token_hex(32)
ns='choms-memory'
COGNEE_REPOSITORY = 'docker.io/library/choms-cognee-local-tokenizer'
COGNEE_TAG = '1.6.5-p204a2a7e1d17'
label={'app.kubernetes.io/name':name}
created=False
role_created=False
stage='initial'

def run(argv,data=None,timeout=60,ok=(0,)):
 p=subprocess.run(argv,input=data,text=True,capture_output=True,timeout=timeout)
 if p.returncode not in ok:
  # No raw errors, command strings, stdin or runtime config in session output.
  lines=p.stderr.splitlines()
  classification='command_failed'
  for enum in ('Forbidden','NotFound','Timeout','Connection refused','Permission denied'):
   if any(enum in line for line in lines): classification=enum.replace(' ','_')
  raise RuntimeError(json.dumps({'stage':stage,'exit':p.returncode,'classification':classification}))
 return p

def k(args,data=None,**kw):
 return run(['kubectl','--request-timeout=30s','-n',ns]+args,data,**kw)

def pg(query):
 return k(['exec','-i','deployment/postgresql','--','sh','-c',
           'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -X -U postgres -d cognee -v ON_ERROR_STOP=1 -At'],query).stdout.strip()

def report(check,**observed):
 print(json.dumps({'check':check,**observed}),flush=True)

def wait_ready():
 k(['rollout','status','deployment/'+name,'--timeout=180s'],timeout=200)
 p=json.loads(k(['get','pods','-l','app.kubernetes.io/name='+name,'-o','json']).stdout)['items']
 if len(p)!=1: raise RuntimeError('pod_count')
 return p[0]

def call(operation,args=None):
 code='''import json,urllib.request,urllib.error,pathlib
payload=json.loads(PAYLOAD)
request=urllib.request.Request('http://127.0.0.1:8080/',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+pathlib.Path('/auth/access').read_text().strip(),'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(request,timeout=60) as response: print(response.read().decode())
except urllib.error.HTTPError as error: print(error.read().decode())
'''.replace('PAYLOAD',repr(json.dumps({'operation':operation,'args':args or {}})))
 result=json.loads(k(['exec',podname,'--','/src/.venv/bin/python','-c',code],timeout=90).stdout)
 if 'result' not in result:
  report('operation_error',operation=operation,diagnostic=result)
  raise RuntimeError('operation_'+operation+'_failed')
 return result['result']

try:
 stage='health_and_collisions'
 deployments=json.loads(k(['get','deployment','cognee-api','postgresql','-o','json']).stdout)['items']
 if any(d['status'].get('readyReplicas')!=1 for d in deployments): raise RuntimeError('existing_not_ready')
 if k(['get','deployment,service,configmap,secret,networkpolicy','-l','app.kubernetes.io/name='+name,'-o','name']).stdout.strip(): raise RuntimeError('collision')
 if pg("SELECT count(*) FROM pg_roles WHERE rolname='"+role+"'")!='0':raise RuntimeError('role_collision')
 actual=json.loads(k(['get','pods','-l','app.kubernetes.io/name=cognee-api','-o','json']).stdout)['items'][0]['status']['containerStatuses'][0]['imageID']
 stage='isolated_role_and_schema'
 pg('BEGIN; CREATE ROLE '+role+" LOGIN PASSWORD '"+password+"' NOSUPERUSER NOCREATEDB NOCREATEROLE; GRANT CONNECT, CREATE ON DATABASE cognee TO "+role+'; CREATE SCHEMA '+schema+' AUTHORIZATION '+role+'; COMMIT;')
 role_created=True
 env={
 'MEMORY_SCHEMA':schema,'DB_HOST':'postgresql.choms-memory.svc.cluster.local','DB_NAME':'cognee','DB_USERNAME':role,
 'DB_PORT':'5432','DB_PROVIDER':'postgres','VECTOR_DB_PROVIDER':'pgvector','VECTOR_DATASET_DATABASE_HANDLER':'pgvector_shared',
 'ENABLE_BACKEND_ACCESS_CONTROL':'true','GRAPH_DATABASE_PROVIDER':'kuzu','SYSTEM_ROOT_DIRECTORY':'/state/system','DATA_ROOT_DIRECTORY':'/state/data',
 'TELEMETRY_DISABLED':'true','LITELLM_LOCAL_MODEL_COST_MAP':'True','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
 'HF_HOME':'/models','HF_HUB_CACHE':'/models/hub','ALLOW_HTTP_REQUESTS':'false',
 'MEMORY_EMBEDDING_PATH':'/models/hub/models--qdrant--bge-small-en-v1.5-onnx-q/snapshots/aa8f8b060edb00e03bfdd08813a2949946c8ba55',
 }
 def meta(n=name):return {'name':n,'namespace':ns,'labels':label}
 code_hash=hashlib.sha256(json.dumps(bundle,sort_keys=True).encode()).hexdigest()
 cm={'apiVersion':'v1','kind':'ConfigMap','metadata':meta(),'immutable':True,'data':bundle}
 secret={'apiVersion':'v1','kind':'Secret','metadata':meta(),'type':'Opaque','data':{key:base64.b64encode(value.encode()).decode() for key,value in {'db':password,'access':access}.items()}}
 policy={'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta(),'spec':{'podSelector':{'matchLabels':label},'policyTypes':['Ingress','Egress'],'ingress':[], 'egress':[{'to':[{'podSelector':{'matchLabels':{'app.kubernetes.io/name':'postgresql','app.kubernetes.io/part-of':'choms-memory'}}}],'ports':[{'protocol':'TCP','port':5432}]},{'to':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'kube-system'}},'podSelector':{'matchLabels':{'k8s-app':'kube-dns'}}}],'ports':[{'protocol':'UDP','port':53},{'protocol':'TCP','port':53}]}]}}
 pgpolicy={'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta(name+'-postgres'),'spec':{'podSelector':{'matchLabels':{'app.kubernetes.io/name':'postgresql','app.kubernetes.io/part-of':'choms-memory'}},'policyTypes':['Ingress'],'ingress':[{'from':[{'podSelector':{'matchLabels':label}}],'ports':[{'protocol':'TCP','port':5432}]}]}}
 service={'apiVersion':'v1','kind':'Service','metadata':meta(),'spec':{'type':'ClusterIP','selector':label,'ports':[{'port':8080,'targetPort':8080,'protocol':'TCP'}]}}
 deployment={'apiVersion':'apps/v1','kind':'Deployment','metadata':meta(),'spec':{'replicas':1,'selector':{'matchLabels':label},'strategy':{'type':'Recreate'},'template':{'metadata':{'labels':label,'annotations':{'choms.platforms/gate-code-sha256':code_hash}},'spec':{'nodeSelector':{'kubernetes.io/hostname':'choms-node-02'},'serviceAccountName':'choms-memory','automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'runAsUser':1000,'runAsGroup':1000,'fsGroup':1000,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'gate','image':COGNEE_REPOSITORY+':'+COGNEE_TAG,'imagePullPolicy':'Never','workingDir':'/src','command':['/src/.venv/bin/python','/app/gate_adapter.py'],'env':[{'name':key,'value':value} for key,value in env.items()]+[{'name':'DB_PASSWORD','valueFrom':{'secretKeyRef':{'name':name,'key':'db'}}}], 'resources':{'requests':{'cpu':'250m','memory':'1Gi'},'limits':{'cpu':'1','memory':'3Gi'}},'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'ports':[{'containerPort':8080}],'startupProbe':{'httpGet':{'path':'/ready','port':8080},'failureThreshold':36,'periodSeconds':5},'readinessProbe':{'httpGet':{'path':'/ready','port':8080},'periodSeconds':5},'volumeMounts':[{'name':'code','mountPath':'/app','readOnly':True},{'name':'auth','mountPath':'/auth','readOnly':True},{'name':'state','mountPath':'/state'},{'name':'tmp','mountPath':'/tmp'},{'name':'models','mountPath':'/models','subPath':'models-76fb6636f317812a','readOnly':True}]}],'volumes':[{'name':'code','configMap':{'name':name}},{'name':'auth','secret':{'secretName':name,'defaultMode':288}},{'name':'state','emptyDir':{'sizeLimit':'256Mi'}},{'name':'tmp','emptyDir':{'sizeLimit':'128Mi'}},{'name':'models','persistentVolumeClaim':{'claimName':'cognee-data','readOnly':True}}]}}}}
 items=[cm,policy,pgpolicy,service,deployment]
 stage='server_dry_run'
 manifest=json.dumps({'apiVersion':'v1','kind':'List','items':items})
 k(['apply','--dry-run=server','-f','-'],manifest)
 k(['apply','--dry-run=server','-f','-'],json.dumps(secret))
 stage='scoped_diff'
 diff=k(['diff','-f','-'],manifest,ok=(0,1)).stdout
 if not diff or any('--- '+s in diff for s in ['a/']):raise RuntimeError('unexpected_diff')
 report('scoped_diff',new_resources=len(items),secret_payload_printed=False)
 stage='apply_isolated_gate'
 k(['apply','-f','-'],json.dumps(secret))
 created=True
 k(['apply','-f','-'],manifest)
 stage='gate_ready'
 pod=wait_ready();podname=pod['metadata']['name']
 status=pod['status']['containerStatuses'][0]
 if pod['spec']['nodeName']!='choms-node-02' or status['restartCount'] or status['imageID']!=actual:raise RuntimeError('placement_or_image')
 report('isolated_gate_ready',imageID=status['imageID'],node='choms-node-02',restarts=0)
 stage='authentication'
 code="import urllib.request,urllib.error;\ntry: urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/',data=b'{}'),timeout=5)\nexcept urllib.error.HTTPError as e: print(e.code)"
 if k(['exec',podname,'--','/src/.venv/bin/python','-c',code]).stdout.strip()!='401':raise RuntimeError('authentication_not_required')
 if call('health')['status']!='ready':raise RuntimeError('health')
 stage='official_handler_regression'
 regression=call('regression')
 if regression!={'official_left_shadow':True,'wrapper_remaining':0,'second_execution':'pass'}:raise RuntimeError('regression')
 report('installed_handler_regression',**regression)
 stage='write_read_semantic_search'
 record=call('remember',{'text':'Synthetic violet satellite continuity requirement'})
 memory_id=record['id']
 if not call('review',{'memory_id':memory_id}):raise RuntimeError('read')
 if len(call('search',{'text':'violet satellite'}))!=1:raise RuntimeError('semantic_search')
 projections=call('projection_stats',{'memory_id':memory_id})
 if projections!={'nodes':1,'embeddings':1}:raise RuntimeError('projection_write')
 report('write_read_semantic_search',matches=1,**projections)
 stage='forget'
 result=call('forget',{'memory_id':memory_id})
 if result.get('state')!='forgotten':raise RuntimeError('purge_pending')
 if call('review',{'memory_id':memory_id}) is not None or call('search',{'text':'violet satellite'}):raise RuntimeError('residual_search')
 audit=call('audit',{'memory_id':memory_id})
 if audit!={'canonical_rows':0,'tombstones':1,'graph_artifacts':0,'cache_entries':0,'vector_schemas':0}:raise RuntimeError('residual_artifacts')
 # Role-owned schemas must now be the canonical schema ONLY.
 remaining=pg("SELECT count(*) FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner WHERE r.rolname='"+role+"'")
 if remaining!='1':raise RuntimeError('residual_vector_schema')
 report('logical_purge',**audit)
 stage='restart_and_recheck'
 k(['exec',podname,'--','/src/.venv/bin/python','-c','import os,signal; os.kill(1,signal.SIGINT)'])
 time.sleep(4)
 for _ in range(45):
  pod=json.loads(k(['get','pod',podname,'-o','json']).stdout)
  st=pod['status'].get('containerStatuses',[{}])[0]
  if st.get('restartCount')==1 and st.get('ready'):break
  time.sleep(3)
 else:raise RuntimeError('restart_timeout')
 if call('search',{'text':'violet satellite'}) or call('review',{'memory_id':memory_id}) is not None:raise RuntimeError('resurrection')
 if call('audit',{'memory_id':memory_id})!=audit:raise RuntimeError('post_restart_residual')
 if call('forget',{'memory_id':memory_id})!={'state':'forgotten'}:raise RuntimeError('second_forget')
 report('restart_no_resurrection',container_restarts=1,search_matches=0,tombstones=1)
 stage='complete'
 report('e2e',status='PASS',project= 'choms-memory-e2e-test')
except Exception as e:
 report('e2e',status='FAIL',stage=stage,error_class=type(e).__name__)
 if stage=='gate_ready' and created:
  # Classify only source locations and exception classes; no free-text logs.
  logs=k(['logs','deployment/'+name,'--tail=35'],ok=(0,1)).stdout.splitlines()
  import re
  classes=[]
  for line in logs:
   m=re.match(r'^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):',line)
   if m:classes.append(m.group(1))
  report('startup_exception',classes=classes)
 sys.exitcode=1
finally:
 stage='cleanup'
 if created:
  k(['delete','deployment,service,configmap,secret,networkpolicy','-l','app.kubernetes.io/name='+name,'--wait=true','--timeout=90s'],timeout=110)
  k(['wait','--for=delete','pod','-l','app.kubernetes.io/name='+name,'--timeout=90s'],timeout=110)
 if role_created:
  pg('DROP OWNED BY '+role+'; DROP ROLE '+role+';')
 health=json.loads(k(['get','deployment','cognee-api','postgresql','-o','json']).stdout)['items']
 report('cleanup',synthetic_resources_remaining=bool(k(['get','pod,service,configmap,secret,networkpolicy','-l','app.kubernetes.io/name='+name,'-o','name']).stdout.strip()),live_ready=all(d['status'].get('readyReplicas')==1 for d in health))
if getattr(sys,'exitcode',0):sys.exit(sys.exitcode)
