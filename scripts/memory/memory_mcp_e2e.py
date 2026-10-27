"""Synthetic MCP acceptance; no model inference. All writes have fixture sources."""
import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time
import uuid

TOOLS={'health','propose','remember','search','review','supersede','forget','checkpoint'}


def unwrap(value):
    for _ in range(6):
        if isinstance(value,str):value=json.loads(value);continue
        if isinstance(value,dict) and 'ok' in value:return value
        if isinstance(value,dict) and 'structuredContent' in value:value=value['structuredContent'];continue
        if isinstance(value,dict) and 'result' in value:value=value['result'];continue
        if isinstance(value,dict) and isinstance(value.get('error'),str):
            value=json.loads(value['error']);continue
        if isinstance(value,dict) and 'content' in value:
            texts=[v['text'] for v in value['content'] if v.get('type')=='text']
            if len(texts)!=1:raise RuntimeError('mcp_response_shape')
            value=texts[0];continue
        raise RuntimeError('mcp_response_shape')
    raise RuntimeError('mcp_response_depth')


class Session:
    def __init__(self,command):
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)
        self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)
        self.pending=bytearray();self.number=0
        self.rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'choms-memory-synthetic-check','version':'1'}})
        self.send({'jsonrpc':'2.0','method':'notifications/initialized'})
        names={t['name'] for t in self.rpc('tools/list',{})['tools']}
        if names!=TOOLS:raise RuntimeError('tools_mismatch')
    def send(self,value):
        self.process.stdin.write(json.dumps(value).encode()+b'\n');self.process.stdin.flush()
    def rpc(self,method,params):
        self.number+=1;number=self.number
        self.send({'jsonrpc':'2.0','id':number,'method':method,'params':params})
        deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            if b'\n' in self.pending:
                line,_,rest=self.pending.partition(b'\n');self.pending[:]=rest
                value=json.loads(line)
                if value.get('id')==number:
                    if 'error' in value:raise RuntimeError('jsonrpc_error')
                    return value['result']
            for key,_ in self.selector.select(.2):
                block=os.read(key.fd,65536)
                if not block:raise RuntimeError('mcp_transport_closed')
                self.pending.extend(block)
                if len(self.pending)>131072:raise RuntimeError('mcp_response_limit')
        raise TimeoutError('mcp_call_timeout')
    def call(self,operation,args):return unwrap(self.rpc('tools/call',{'name':operation,'arguments':args}))
    def close(self):
        self.selector.close()
        self.process.stdin.close()
        try:self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=8)


def check(value,name):
    if not value:raise RuntimeError('CHECK_FAIL '+name)
    print('CHECK_PASS '+name,flush=True)


def exercise(call,client):
    run=uuid.uuid4().hex[:10];project='choms-memory-e2e-'+client+'-'+run
    scope={'scope':'project','project_id':project};other={**scope,'project_id':project+'-other'}
    known=[];created=[]
    def invoke(op,args,expect=None):
        result=call(op,args)
        if expect:
            check(not result['ok'] and result['error']['code']==expect,client+'_'+expect)
            return result
        if not result['ok']:raise RuntimeError('CHECK_FAIL '+client+'_'+op+'_'+result['error']['code'])
        return result['data']
    def req():return str(uuid.uuid4())
    def record(summary,part=scope,**kw):
        return {**part,'summary':summary,'importance':'high','type':'decision','topic':'violet-'+run,
                'source_kind':'user_explicit','source_reference':'fixture:'+project,**kw}
    def add(body,operation='remember',**kw):
        args={'record':body,'request_id':req(),**kw}
        if operation=='remember':args['explicit']=True
        value=invoke(operation,args);known.append((value['id'],{k:body[k] for k in ('scope','project_id') if k in body}));created.append(value['id'])
        return value
    try:
        h=invoke('health',{});check(h['status']=='ready' and h['automatic_capture'] is False and not h['real_memory_allowed'],client+'_health_authenticated_capture_off')
        body=record('Synthetic violet satellite compass decision',source_kind='agent_inferred')
        candidate=add(body,'propose');check(candidate['state']=='candidate',client+'_propose')
        original_request=req()
        active=invoke('remember',{**scope,'id':candidate['id'],'expected_revision':1,'explicit':True,'request_id':original_request})
        check(active['state']=='active' and active['revision']==2,client+'_remember_cas')
        replay=invoke('remember',{**scope,'id':candidate['id'],'expected_revision':1,'explicit':True,'request_id':original_request})
        check(replay==active,client+'_idempotent_replay')
        row=invoke('review',{**scope,'id':active['id']})['records']
        check(len(row)==1 and row[0]['state']=='active',client+'_read_by_id')
        found=invoke('search',{**scope,'query':'violet satellite compass'})['records']
        check([r['id'] for r in found]==[active['id']],client+'_semantic_search')
        invoke('remember',{'request_id':req(),'explicit':True,'record':record('Synthetic violet satellite compass decision')},'duplicate')
        new=record('Synthetic violet satellite compass corrected decision')
        invoke('supersede',{**scope,'id':active['id'],'expected_revision':1,'explicit':True,'request_id':req(),'record':new},'cas_conflict')
        replacement=invoke('supersede',{**scope,'id':active['id'],'expected_revision':2,'explicit':True,'request_id':req(),'record':new})
        known.append((replacement['id'],scope));created.append(replacement['id'])
        old=invoke('review',{**scope,'id':active['id']})['records'][0]
        found=invoke('search',{**scope,'query':'violet satellite'})['records']
        check(old['state']=='superseded' and [r['id'] for r in found]==[replacement['id']],client+'_supersede_atomic')
        invoke('supersede',{**scope,'id':active['id'],'expected_revision':2,'explicit':True,'request_id':req(),'record':new},'cas_conflict')
        b=add(record('Synthetic violet satellite separate project',part=other))
        results=invoke('search',{**scope,'query':'violet satellite'})['records']
        check(b['id'] not in [r['id'] for r in results],client+'_project_isolation')
        invoke('review',{**scope,'id':b['id']},'not_found')
        global_row=add(record('Synthetic global violet convention',part={'scope':'global'},topic='global-'+run,importance='critical'))
        personal_row=add(record('Synthetic personal violet preference',part={'scope':'personal'},topic='personal-'+run,importance='medium',type='preference'))
        check(global_row['id'] in [r['id'] for r in invoke('search',{'scope':'global','query':'violet'})['records']],client+'_global_scope')
        p=invoke('search',{'scope':'personal','query':'violet'})['records']
        check(personal_row['id'] not in [r['id'] for r in p],client+'_importance_default')
        check(personal_row['id'] in [r['id'] for r in invoke('search',{'scope':'personal','query':'violet','include_medium':True})['records']],client+'_personal_scope')
        budget=invoke('search',{**scope,'query':'violet','limit':1,'budget_chars':1200})
        check(len(budget['records'])<=1 and budget['characters']<=1200,client+'_context_budget')
        checkpoint=add(record('Synthetic checkpoint of violet fixtures',topic='checkpoint-'+run,
            details='Objective: fixture; decisions: synthetic; minimum: isolation; restrictions: no real data; completed: tests; pending: cleanup; next: forget; discarded: external calls.'),'checkpoint',explicit=True)
        check(invoke('review',{**scope,'id':checkpoint['id']})['records'][0]['type']=='checkpoint',client+'_checkpoint')
        # Forget through supported MCP only, including superseded lineage.
        for memory_id,part in reversed(known):
            rows=invoke('review',{**part,'id':memory_id})['records']
            if rows:invoke('forget',{**part,'id':memory_id,'expected_revision':rows[0]['revision'],'explicit':True,'request_id':req()})
        audit=invoke('health',{'audit_ids':created})['audit']
        check(all(a['canonical_rows']==a['graph_artifacts']==a['vector_schemas']==a['cache_entries']==a['content_receipts']==0 and a['tombstone'] for a in audit),client+'_hard_delete_all_projections')
        check(all(a['tombstone_fields']==['id','request_ids','revision','state'] for a in audit),client+'_content_free_tombstones')
        fenced=invoke('remember',{**scope,'id':candidate['id'],'expected_revision':1,'explicit':True,'request_id':original_request})
        check(fenced['state']=='forgotten',client+'_tombstone_fences_retry')
        check(invoke('search',{**scope,'query':'violet satellite'})['records']==[],client+'_search_empty')
        return {'client':client,'project':project,'ids':created,'scope':scope,'checks':'PASS'}
    except Exception:
        # Do not claim cleanup on failure; preserve explicit synthetic IDs for diagnosis.
        print(json.dumps({'event':'synthetic_e2e_failed','client':client,'created_ids':created}),flush=True)
        raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--ssh-target',required=True);p.add_argument('--client',choices=('codex','hermes'),required=True)
    a=p.parse_args();launcher=Path(__file__).with_name('choms_memory_mcp.py')
    s=Session([sys.executable,str(launcher),'--ssh-target',a.ssh_target,'--client',a.client])
    try:result=exercise(s.call,a.client);print(json.dumps(result))
    finally:s.close()

if __name__=='__main__':main()
