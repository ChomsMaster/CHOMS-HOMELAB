"""Native MCP acceptance without inference; synthetic fixtures only.
Run with --discover-only --registered after registration to avoid writes.
"""
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--ssh-target',required=True)
parser.add_argument('--registered',action='store_true')
parser.add_argument('--discover-only',action='store_true')
parser.add_argument('--verify-only')
parser.add_argument('--report')
options=parser.parse_args()
import json,subprocess,selectors,time,pathlib,os,sys,tempfile
repo=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'scripts/memory'))
from memory_mcp_e2e import exercise,unwrap,TOOLS
with tempfile.TemporaryDirectory(prefix='choms-memory-codex-candidate-') as home:
 candidate={'command':'python3','args':['-I',str(repo/'scripts/memory/choms_memory_mcp.py'),'--ssh-target',options.ssh_target,'--client','codex'],'cwd':str(repo),'startup_timeout_sec':30,'tool_timeout_sec':120}
 if options.registered:
  import tomllib
  candidate=tomllib.loads((pathlib.Path.home()/'.codex/config.toml').read_text())['mcp_servers']['choms-memory']
 config='[mcp_servers.choms-memory]\n'+'\n'.join(key+' = '+json.dumps(value) for key,value in candidate.items())+'\n'
 pathlib.Path(home,'config.toml').write_text(config)
 env=dict(os.environ,CODEX_HOME=home)
 p=subprocess.Popen(['codex','app-server','--listen','stdio://','-c','analytics.enabled=false'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,bufsize=0,cwd=repo)
 selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ);buffer=bytearray();number=0
 def rpc(method,params):
  global number
  number+=1;identifier=number
  p.stdin.write(json.dumps({'id':identifier,'method':method,'params':params}).encode()+b'\n');p.stdin.flush()
  deadline=time.monotonic()+120
  while time.monotonic()<deadline:
   if b'\n' in buffer:
    line,_,rest=buffer.partition(b'\n');buffer[:]=rest
    value=json.loads(line)
    if value.get('id')==identifier:
     if 'error' in value:raise RuntimeError('codex_rpc_'+method+'_'+str(value['error'].get('code')))
     return value['result']
   for key,_ in selector.select(.2):
    block=os.read(key.fd,65536)
    if not block:raise RuntimeError('codex_transport_closed')
    buffer.extend(block)
  raise TimeoutError(method)
 try:
  rpc('initialize',{'clientInfo':{'name':'choms-memory-native-e2e','version':'1'},'capabilities':{'experimentalApi':True}})
  p.stdin.write(b'{"method":"initialized"}\n');p.stdin.flush()
  thread=rpc('thread/start',{'cwd':str(repo),'ephemeral':True,'approvalPolicy':'never','sandbox':'read-only'})['thread']['id']
  status=rpc('mcpServerStatus/list',{'threadId':thread,'serverName':'choms-memory','detail':'full'})
  candidates=[v for v in status['data'] if v['name']=='choms-memory']
  assert len(candidates)==1 and set(candidates[0]['tools'])==TOOLS
  print('CODEX_NATIVE_DISCOVERY_PASS tools=8',flush=True)
  def call(name,args):return unwrap(rpc('mcpServer/tool/call',{'threadId':thread,'server':'choms-memory','tool':name,'arguments':args}))
  if options.discover_only:
   h=call('health',{});assert h['ok'] and h['data']['status']=='ready'
   result={'client':'codex','discovery':'PASS','tools':8,'capture':False}
  elif options.verify_only:
   previous=json.loads(pathlib.Path(options.verify_only).read_text())
   h=call('health',{'audit_ids':previous['ids']})
   assert h['ok'] and h['data']['blocked_automatic_outbound_attempts']==0
   assert all(a['canonical_rows']==a['graph_artifacts']==a['vector_schemas']==a['cache_entries']==a['content_receipts']==0 and a['tombstone'] for a in h['data']['audit'])
   found=call('search',{**previous['scope'],'query':'violet satellite'})
   assert found['ok'] and found['data']['records']==[]
   print('CHECK_PASS codex_native_after_restart_no_resurrection_and_zero_egress',flush=True)
   result=previous
  else:
   result=exercise(call,'codex-native')
  if options.report:pathlib.Path(options.report).write_text(json.dumps(result))
  print(json.dumps(result))
 finally:
  selector.close();p.terminate()
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.kill();p.wait()
