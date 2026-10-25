import os,sys,json,pathlib,hashlib,importlib,importlib.metadata,subprocess,traceback,asyncio,sqlite3,time,resource,socket
started=time.monotonic();stage='python_syntax_and_frozen_dependencies';result={};attempts=[]
def audit(event,args):
 if event=='socket.getaddrinfo' or event=='socket.connect' and args[0].family in (socket.AF_INET,socket.AF_INET6):
  attempts.append(event);raise RuntimeError('Network forbidden during final image test')
sys.addaudithook(audit)
try:
 metadata=json.loads(pathlib.Path('/provenance.json').read_text());baseline=json.loads(pathlib.Path('/baseline.json').read_text())
 for f in metadata['files']:
  p=pathlib.Path('/src')/f['path'];data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==f['patched_sha256'];compile(data,str(p),'exec')
 deps=sorted((x.metadata['Name'],x.version) for x in importlib.metadata.distributions());assert hashlib.sha256(json.dumps(deps).encode()).hexdigest()==baseline['packages_sha256'];assert hashlib.sha256(pathlib.Path('/src/uv.lock').read_bytes()).hexdigest()==baseline['uv_lock_sha256'];result['syntax_and_frozen_dependencies']='PASS'
 stage='ten_offline_regressions'
 r=subprocess.run([sys.executable,'/regression.py','-v'],capture_output=True,timeout=90);result['regression_exit_code']=r.returncode;result['ten_regressions_passed']=r.returncode==0 and b'Ran 10 tests' in r.stderr and b'\nOK\n' in r.stderr
 if not result['ten_regressions_passed']:raise RuntimeError('Offline regression failed')
 stage='offline_import_and_packaged_cost_map'
 import cognee,litellm
 info=importlib.import_module('litellm.litellm_core_utils.get_model_cost_map').get_model_cost_map_source_info();assert info['source']=='local' and info['is_env_forced'] and info.get('url') is None;result['packaged_cost_map']='PASS'
 stage='synthetic_cognee_add'
 path=pathlib.Path('/work/fixture.txt');path.write_text('Synthetic alpha component connects to synthetic beta component. This fixture contains no real project data.')
 asyncio.run(cognee.add([str(path)],dataset_name='synthetic-tokenizer-smoke'))
 stage='synthetic_dataset_persistence'
 count=0;rows=0
 for p in pathlib.Path('/work').rglob('*'):
  if not p.is_file() or p.stat().st_size<16:continue
  with p.open('rb') as f:header=f.read(16)
  if header!=b'SQLite format 3\x00':continue
  with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as db:
   tables={r[0] for r in db.execute('select name from sqlite_master where type=\'table\'')}
   if {'datasets','data'}<=tables:
    count+=db.execute('select count(*) from datasets where name=?',('synthetic-tokenizer-smoke',)).fetchone()[0]
    rows+=db.execute('select count(*) from data where dataset_id in (select id from datasets where name=?)',('synthetic-tokenizer-smoke',)).fetchone()[0]
 assert count==1 and rows>=1;assert not attempts
 result.update(status='PASS',synthetic_dataset_count=count,synthetic_data_rows=rows,stores={'relational':'sqlite_temporary','vector':'lancedb_temporary','graph':'kuzu_temporary_no_cognify'},network_attempts=0);exitcode=0
except BaseException as e:
 result.update(status='FAIL',stage=stage,error_class=type(e).__name__,error_module=type(e).__module__,network_attempts=len(attempts),frames=[{'file':pathlib.Path(f.filename).name,'line':f.lineno,'operation':f.name} for f in traceback.extract_tb(e.__traceback__)][-14:]);exitcode=1
 if hasattr(e,'errors'):result['validation_fields']=[{'field':list(x['loc']),'type':x['type']} for x in e.errors(include_input=False,include_context=False,include_url=False)]
result.update(duration_seconds=round(time.monotonic()-started,3),cpu_seconds=round(resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,3),max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
print('FINAL_DERIVED_TEST='+json.dumps(result),flush=True)
sys.exit(exitcode)
