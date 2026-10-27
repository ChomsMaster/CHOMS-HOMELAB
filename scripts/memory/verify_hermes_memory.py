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
import sys,os,site,json,contextlib,io,logging,pathlib
sys.dont_write_bytecode=True
os.environ['HERMES_DISABLE_LAZY_INSTALLS']='1'
root=pathlib.Path.home()/'.hermes/hermes-agent';sys.path.insert(0,str(root))
from pm.environments import committed_venv,site_packages
venv=committed_venv(root);assert venv
site.addsitedir(str(site_packages(venv)));sys.path.insert(0,str(root))
logging.disable(logging.CRITICAL)
repo=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo/'scripts/memory'))
from memory_mcp_e2e import exercise,unwrap,TOOLS
from tools.mcp_tool_discovery import register_mcp_servers
from tools.mcp_tool_lifecycle import shutdown_mcp_servers
from tools.mcp_tool_schema import mcp_prefixed_tool_name
from tools.registry import registry
config={'command':'python3','args':['-I',str(repo/'scripts/memory/choms_memory_mcp.py'),'--ssh-target',options.ssh_target,'--client','hermes'],
        'cwd':str(repo),'tools':{'include':sorted(TOOLS),'resources':False,'prompts':False},'timeout':120}
if options.registered:
 config=json.loads((pathlib.Path.home()/'.hermes/config.yaml').read_text())['mcp_servers']['choms-memory']
# Never changes existing MCP allowlists.
try:
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  names=register_mcp_servers({'choms-memory':config})
 expected={mcp_prefixed_tool_name('choms-memory',n) for n in TOOLS}
 assert set(names)==expected,(len(names),len(expected))
 print('HERMES_NATIVE_DISCOVERY_PASS tools=8',flush=True)
 def call(name,args):
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   raw=registry.dispatch(mcp_prefixed_tool_name('choms-memory',name),args)
  return unwrap(raw)
 if options.discover_only:
  h=call('health',{});assert h['ok'] and h['data']['status']=='ready'
  result={'client':'hermes','discovery':'PASS','tools':8,'capture':False}
 elif options.verify_only:
  previous=json.loads(pathlib.Path(options.verify_only).read_text())
  h=call('health',{'audit_ids':previous['ids']})
  assert h['ok'] and h['data']['blocked_automatic_outbound_attempts']==0
  assert all(a['canonical_rows']==a['graph_artifacts']==a['vector_schemas']==a['cache_entries']==a['content_receipts']==0 and a['tombstone'] for a in h['data']['audit'])
  found=call('search',{**previous['scope'],'query':'violet satellite'})
  assert found['ok'] and found['data']['records']==[]
  print('CHECK_PASS hermes_native_after_restart_no_resurrection_and_zero_egress',flush=True)
  result=previous
 else:
  result=exercise(call,'hermes')
 if options.report:pathlib.Path(options.report).write_text(json.dumps(result))
 print(json.dumps(result))
finally:
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):shutdown_mcp_servers()
