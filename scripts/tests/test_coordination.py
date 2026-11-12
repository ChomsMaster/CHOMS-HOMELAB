import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/coordination'))
import coordinator
import unified_skills_inventory
import choms_coordinator_mcp


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='choms-coordinator-test-')
        self.base=Path(self.temp.name)
        self.root=self.base/'projects';self.root.mkdir()
        self.workspace=self.root/'fixture';self.workspace.mkdir()
        subprocess.run(['git','init','-q',str(self.workspace)],check=True)
        self.state=self.base/'state'
        self.fake=self.base/'codex'
        self.fake.write_text('#!/usr/bin/env python3\nimport os,pathlib,sys\na=sys.argv\np=pathlib.Path(a[a.index("--output-last-message")+1]);p.write_text("synthetic delegated result;api_key_env="+str("OPENAI_API_KEY" in os.environ))\n')
        self.fake.chmod(0o700)

    def tearDown(self): self.temp.cleanup()

    def test_delegate_status_result_cleanup(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'synthetic-only-test-value'}):
            submitted=coordinator.submit(task='Return a synthetic result',workspace=str(self.workspace),
                workspace_root=self.root,state_dir=self.state,codex=str(self.fake))
        self.assertEqual(submitted['state'],'queued')
        with self.assertRaisesRegex(coordinator.CoordinationError,'workspace_has_active_job'):
            coordinator.submit(task='Do not overlap',workspace=str(self.workspace),
                workspace_root=self.root,state_dir=self.state,codex=str(self.fake))
        folder,_=coordinator.load_job(self.state,submitted['job_id'])
        deadline=time.monotonic()+10
        state='queued'
        while time.monotonic()<deadline:
            state=coordinator.status(job_id=submitted['job_id'],state_dir=self.state)['state']
            if state in ('succeeded','failed'):break
            time.sleep(.05)
        self.assertEqual(state,'succeeded')
        result=coordinator.result(job_id=submitted['job_id'],state_dir=self.state)
        self.assertEqual(result['result'],'synthetic delegated result;api_key_env=False')
        self.assertEqual(coordinator.remove(job_id=submitted['job_id'],state_dir=self.state,explicit=True)['state'],'removed')
        self.assertFalse(folder.exists())

    def test_workspace_and_profile_are_fail_closed(self):
        with self.assertRaisesRegex(coordinator.CoordinationError,'workspace_outside_authorized_root'):
            coordinator.submit(task='x',workspace=str(self.base),workspace_root=self.root,state_dir=self.state)
        with self.assertRaisesRegex(coordinator.CoordinationError,'invalid_codex_profile'):
            coordinator.submit(task='x',workspace=str(self.workspace),workspace_root=self.root,state_dir=self.state,profile='nous')
        (self.workspace/'untracked.txt').write_text('preserve')
        with self.assertRaisesRegex(coordinator.CoordinationError,'workspace_must_be_clean_git_worktree'):
            coordinator.submit(task='x',workspace=str(self.workspace),workspace_root=self.root,state_dir=self.state)
        protected=self.root/'CHOMS BoardView';protected.mkdir();subprocess.run(['git','init','-q',str(protected)],check=True)
        with self.assertRaisesRegex(coordinator.CoordinationError,'protected_workspace'):
            coordinator.submit(task='x',workspace=str(protected),workspace_root=self.root,state_dir=self.state)

    def test_memory_target_is_read_from_registered_yaml_without_rewriting_it(self):
        config=self.base/'hermes.yaml'
        source='mcp_servers:\n  choms_memory:\n    args: ["-I", "bridge.py", "--ssh-target", "fixture@memory.invalid"]\n'
        config.write_text(source)
        self.assertEqual(choms_coordinator_mcp.registered_memory_target(config),'fixture@memory.invalid')
        self.assertEqual(config.read_text(),source)

    def test_job_id_and_terminal_result_guards(self):
        with self.assertRaisesRegex(coordinator.CoordinationError,'invalid_job_id'):
            coordinator.status(job_id='../secrets',state_dir=self.state)
        submitted=coordinator.submit(task='x',workspace=str(self.workspace),workspace_root=self.root,state_dir=self.state)
        with self.assertRaisesRegex(coordinator.CoordinationError,'job_not_terminal'):
            coordinator.result(job_id=submitted['job_id'],state_dir=self.state)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if coordinator.status(job_id=submitted['job_id'],state_dir=self.state)['state'] in ('succeeded','failed'):break
            time.sleep(.05)

    def test_stdio_mcp_delegate_result_recovery(self):
        proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/coordination/choms_coordinator_mcp.py'),
            '--workspace-root',str(self.root),'--state-dir',str(self.state),'--codex',str(self.fake)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        next_id=0
        def rpc(method,params=None):
            nonlocal next_id
            next_id+=1
            proc.stdin.write(json.dumps({'jsonrpc':'2.0','id':next_id,'method':method,'params':params or {}})+'\n')
            proc.stdin.flush()
            value=json.loads(proc.stdout.readline())
            self.assertEqual(value.get('id'),next_id)
            return value['result']
        try:
            rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}})
            self.assertEqual(len(rpc('tools/list')['tools']),5)
            delegated=rpc('tools/call',{'name':'delegate','arguments':{'task':'Return a synthetic result','workspace':str(self.workspace)}})
            job_id=delegated['structuredContent']['job_id']
            deadline=time.monotonic()+10
            while time.monotonic()<deadline:
                state=rpc('tools/call',{'name':'status','arguments':{'job_id':job_id}})['structuredContent']['state']
                if state in ('succeeded','failed'):break
                time.sleep(.05)
            self.assertEqual(state,'succeeded')
            recovered=rpc('tools/call',{'name':'result','arguments':{'job_id':job_id}})['structuredContent']
            self.assertEqual(recovered['result'],'synthetic delegated result;api_key_env=False')
        finally:
            proc.terminate();proc.wait(timeout=3)
            proc.stdin.close();proc.stdout.close()


class UnifiedInventoryTests(unittest.TestCase):
    def test_exact_content_dedup_without_copying_sources(self):
        source=ROOT/'tools/choms-skills/skills/choms-memory-governance/SKILL.md'
        raw=source.read_bytes()
        import hashlib
        record={'path':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        with tempfile.TemporaryDirectory(prefix='choms-skills-audit-fixture-') as tmp:
            audit=Path(tmp);(audit/'CHOMS_SKILLS_FUNCTIONAL_ANALYSIS.json').write_text(json.dumps({
                'total_skills':2,'skills':{'first':[record],'second':[record]}}))
            for host in ('node-dev-01','node-dev-02'):
                (audit/f'{host}-skills.json').write_text(json.dumps({'host':host,'skills':[
                    {'name':name,**record} for name in ('first','second')]}))
            (audit/'choms-unified-skills-comparison.json').write_text(json.dumps(
                {'total_records':4,'unique_names':2}))
            data=unified_skills_inventory.inventory(audit,ROOT)
        self.assertEqual(data['counts']['skills'],2)
        self.assertEqual(data['counts']['source_records'],4)
        self.assertEqual(data['counts']['verified_source_records'],4)
        self.assertEqual(data['counts']['exact_duplicate_groups'],1)
        self.assertTrue(all(e['activation']=='blocked' for e in data['skills']))
        self.assertEqual(source.read_bytes(),raw)


if __name__=='__main__': unittest.main()
