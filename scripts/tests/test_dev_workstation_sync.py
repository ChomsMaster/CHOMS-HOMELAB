"""Isolated homes/Git origins; native edits are real, installation reuses a test double."""
from pathlib import Path
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'scripts/skills'))
import workstation as w
import runtime as rt


def command(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL)


def tree(root):
    result={}
    for p in root.rglob('*'):
        if p.is_symlink():result[str(p.relative_to(root))]=('link',os.readlink(p))
        elif p.is_file():result[str(p.relative_to(root))]=('file',hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns)
        else:result[str(p.relative_to(root))]=('dir',p.stat().st_mtime_ns)
    return result


class FakeInstaller:
    """Only the existing install API boundary is replaced: no second real installer."""
    calls=[]
    def __init__(self,root,source_root=None,create=True):
        self.root=root;self.source_root=source_root or REPO
        if create:
            for d in ['releases','receipts','bin']: (root/d).mkdir(parents=True,exist_ok=True)
    def current(self):return (self.root/'current').resolve().name
    def release(self,ident):return self.root/'releases'/ident
    def verify(self,ident):
        if not self.release(ident).is_dir():raise ValueError('missing')
        return {'status':'PASS'}
    def prepare(self,lock):
        self.calls.append('existing_runtime_prepare');ident=hashlib.sha256(lock.read_bytes()).hexdigest()[:32]
        target=self.release(ident);target.mkdir(parents=True,exist_ok=True);(target/'MANIFEST.json').write_text('{}');return ident
    def environment(self,release):return os.environ|{'PYTHONDONTWRITEBYTECODE':'1'}
    def test(self,ident):
        self.calls.append('existing_runtime_test');rt.write_json(self.root/'receipts'/f'{ident}.json',{'status':'PASS'})
    def activate(self,ident):
        self.calls.append('existing_runtime_activate');rt.atomic_link(self.root/'current','releases/'+ident)
        rt.atomic_link(self.root/'bin/choms-runtime',self.source_root/'scripts/skills/runtime.py')


class WorkstationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='choms-workstation-git-');base=Path(cls.temp.name)
        cls.repo=base/'source';cls.repo.mkdir();command(cls.repo,'init')
        for folder in ['tools/choms-skills','tools/choms-workstations','scripts/skills']:
            shutil.copytree(REPO/folder,cls.repo/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (cls.repo/'user-project.txt').write_text('published fixture')
        command(cls.repo,'add','.');command(cls.repo,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','published fixture')
        cls.origin=base/'origin.git';subprocess.run(['git','init','--bare',str(cls.origin)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        command(cls.repo,'remote','add','origin',str(cls.origin));command(cls.repo,'push','origin','HEAD:refs/heads/base');command(cls.repo,'fetch','origin')
        cls.source=w.Source(cls.repo,'origin/base')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.temp_home=tempfile.TemporaryDirectory(prefix='choms-home-');self.addCleanup(self.temp_home.cleanup)
        self.home=Path(self.temp_home.name);self.ws=w.Workstation(self.source,self.home,'node-dev-02')
        FakeInstaller.calls=[];self.patch=patch.object(w.rt,'Runtime',FakeInstaller);self.patch.start();self.addCleanup(self.patch.stop)
    def apply(self):return self.ws.apply(self.ws.plan()['plan_sha256'])

    def test_check_plan_are_byte_and_metadata_read_only(self):
        (self.home/'project').mkdir();(self.home/'project/draft').write_text('unpublished')
        before=tree(self.home);self.ws.plan();self.ws.plan();self.assertEqual(before,tree(self.home))
        self.assertEqual(FakeInstaller.calls,[])

    def test_apply_uses_existing_runtime_and_is_idempotent(self):
        self.assertTrue(self.apply()['converged']);self.assertIn('existing_runtime_prepare',FakeInstaller.calls)
        self.assertTrue(self.ws.plan()['converged']);before=tree(self.home);self.assertFalse(self.apply()['changed']);self.assertEqual(before,tree(self.home))

    def test_foreign_skill_blocks_everything(self):
        path=self.home/'.agents/skills/choms-browser-qa';path.mkdir(parents=True);(path/'SKILL.md').write_text('user draft')
        before=tree(self.home)
        with self.assertRaisesRegex(ValueError,'conflicts'):self.apply()
        self.assertEqual(before,tree(self.home));self.assertEqual(FakeInstaller.calls,[])

    def test_foreign_mcp_and_sentinel_preserved(self):
        path=self.home/'.codex/config.toml';path.parent.mkdir();path.write_text('[mcp_servers.choms_playwright]\ncommand="foreign"\nargs=[]\n')
        before=tree(self.home)
        with self.assertRaisesRegex(ValueError,'conflicts'):self.apply()
        self.assertEqual(before,tree(self.home))

    def test_unrelated_oauth_configuration_preserved_and_rollback(self):
        p=self.home/'.codex/config.toml';p.parent.mkdir();original='model="local"\n[mcp_servers.choms_figma]\nurl="https://mcp.figma.com/mcp"\nenabled=true\n';p.write_text(original)
        token=self.home/'.codex/private-session';token.write_text('sentinel')
        self.apply();self.assertTrue(p.read_text().startswith(original));self.assertEqual(token.read_text(),'sentinel')
        with p.open('a') as out:out.write('\n[mcp_servers.foreign]\ncommand="custom"\n')
        self.ws.rollback();self.assertIn(original,p.read_text());self.assertIn('[mcp_servers.foreign]',p.read_text());self.assertEqual(token.read_text(),'sentinel')
        self.assertFalse((self.home/'.hermes/config.yaml').exists())

    def test_stale_plan_rejected_before_install(self):
        plan=self.ws.plan();p=self.home/'.codex/config.toml';p.parent.mkdir();p.write_text('model="changed"\n')
        with self.assertRaisesRegex(ValueError,'plan_changed'):self.ws.apply(plan['plan_sha256'])
        self.assertEqual(FakeInstaller.calls,[])

    def test_source_advance_requires_manual_fetch_replan(self):
        with patch.object(w.Source,'publication',side_effect=ValueError('remote_ref_changed_fetch_and_replan')):
            before=tree(self.home)
            with self.assertRaisesRegex(ValueError,'remote_ref_changed'):self.apply()
            self.assertEqual(before,tree(self.home))

    def test_user_changes_prevent_rollback_without_partial_edits(self):
        self.apply();p=self.home/'.codex/config.toml';p.write_text(p.read_text().replace('playwright-mcp','custom'))
        before=tree(self.home)
        with self.assertRaisesRegex(ValueError,'modified_since_apply'):self.ws.rollback()
        self.assertEqual(before,tree(self.home))

    def test_foreign_git_draft_is_not_used_or_changed(self):
        p=self.repo/'user-project.txt';p.write_text('unpublished user change')
        try:
            before=command(self.repo,'status','--porcelain');self.apply()
            self.assertEqual(p.read_text(),'unpublished user change');self.assertEqual(before,command(self.repo,'status','--porcelain'))
            self.assertFalse(any(self.ws.root.glob('sources/*/user-project.txt')))
        finally:p.write_text('published fixture')

    def test_unpublished_controller_rejected(self):
        with patch.object(w.Source,'read',autospec=True,side_effect=lambda obj,p: b'unpublished' if p=='scripts/skills/workstation.py' else command(obj.repo,'show',obj.commit+':'+p)):
            before=tree(self.home)
            with self.assertRaisesRegex(ValueError,'controller_differs'):self.apply()
            self.assertEqual(before,tree(self.home))

    def test_partial_config_failure_rolls_back_only_owned_resources(self):
        original=self.ws.write_config
        def fail(path,before,after):
            if path==self.ws.configs['hermes']:raise OSError('synthetic failure')
            return original(path,before,after)
        with patch.object(self.ws,'write_config',side_effect=fail),self.assertRaises(OSError):self.apply()
        self.assertFalse((self.home/'.codex/config.toml').exists());self.assertFalse((self.home/'.agents/skills/choms-browser-qa').exists())
        self.assertFalse((self.ws.runtime_root/'current').exists())

    def test_yaml_foreign_fields_comments_and_empty_mapping(self):
        for original in ['theme: dark\nmcp_servers: {} # keep\nnext: 2\n','theme: dark\nmcp_servers:\n  foreign:\n    command: custom\nnext: 2\n']:
            p=self.home/'.hermes/config.yaml';p.parent.mkdir(exist_ok=True);p.write_text(original)
            self.apply();text=p.read_text();self.assertIn('theme: dark',text);self.assertIn('next: 2',text)
            self.ws.rollback();self.assertEqual(w.yaml_module(self.home).safe_load(p.read_text()),w.yaml_module(self.home).safe_load(original))
            if '# keep' in original:self.assertIn('# keep',p.read_text())

    def test_real_runtime_read_only_inspection_creates_nothing(self):
        original=__import__('importlib').util.spec_from_file_location('readonly_runtime',REPO/'scripts/skills/runtime.py')
        module=__import__('importlib').util.module_from_spec(original);original.loader.exec_module(module)
        with patch.object(w.rt,'Runtime',module.Runtime):
            before=tree(self.home);self.ws.plan();self.assertEqual(before,tree(self.home))

    def test_changed_launcher_blocks_rollback_before_configuration_edits(self):
        self.apply();path=self.ws.runtime_root/'bin/choms-runtime';path.unlink();path.symlink_to(self.home/'user-script')
        before=tree(self.home)
        with self.assertRaisesRegex(ValueError,'launcher_changed'):self.ws.rollback()
        self.assertEqual(before,tree(self.home))

    def test_model_and_comfyui_state_are_outside_convergence(self):
        p=self.home/'ComfyUI/models';p.mkdir(parents=True);(p/'user-model').write_text('synthetic preserved asset')
        before=tree(self.home/'ComfyUI');self.apply();self.assertEqual(before,tree(self.home/'ComfyUI'))

    def test_published_skill_snapshot_ignores_working_tree_draft(self):
        p=self.repo/'tools/choms-skills/modules/browser-QA/choms-browser-qa/SKILL.md';before=p.read_bytes();p.write_text('unpublished draft')
        try:
            self.apply();self.assertEqual(p.read_text(),'unpublished draft')
            self.assertEqual((self.home/'.agents/skills/choms-browser-qa/SKILL.md').read_bytes(),before)
        finally:p.write_bytes(before)

    def test_configuration_symlink_is_preserved(self):
        target=self.home/'project-config';target.write_text('model="private"\n')
        p=self.home/'.codex/config.toml';p.parent.mkdir();p.symlink_to(target)
        before=tree(self.home)
        with self.assertRaisesRegex(ValueError,'conflicts'):self.apply()
        self.assertEqual(before,tree(self.home))

    def test_second_native_root_failure_restores_first_root(self):
        original=w.native.activate;calls=[]
        def fail(roots,*args,**kwargs):
            calls.append(roots)
            if len(calls)==2:raise OSError('synthetic root failure')
            return original(roots,*args,**kwargs)
        with patch.object(w.native,'activate',side_effect=fail),self.assertRaises(OSError):self.apply()
        self.assertFalse((self.home/'.agents/skills/choms-browser-qa').exists())
        self.assertFalse((self.home/'.codex/config.toml').exists())

    def test_legacy_owned_links_migrate_to_immutable_source_reversibly(self):
        package=self.source.packages()['choms-browser-qa'];legacy_target=self.repo/package['path']
        link=self.home/'.agents/skills/choms-browser-qa';link.parent.mkdir(parents=True);link.symlink_to(legacy_target)
        receipt=self.home/'.local/share/choms-skills/activation-node-dev-02.json';receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps({'created':[{'path':str(link),'target':str(legacy_target)}]}))
        self.apply();self.assertNotEqual(link.resolve(),legacy_target);self.assertTrue(str(link.resolve()).startswith(str(self.ws.root/'sources')))
        self.ws.rollback();self.assertEqual(link.resolve(),legacy_target)
