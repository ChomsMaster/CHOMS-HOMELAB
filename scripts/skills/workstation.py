#!/usr/bin/env python3
"""Workstation convergence coordinator; tool installation stays in runtime.py."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
import sys
import uuid
sys.dont_write_bytecode = True
import runtime as rt
import activate_native as native

MANIFEST = 'tools/choms-workstations/BASE.json'
PROFILE = 'tools/choms-skills/PROFILE.json'
PREFIXES = ('tools/choms-skills/', 'scripts/skills/', 'tools/choms-workstations/')
SERVER = 'choms_playwright'
_VERIFIED_YAML=set()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    try:return subprocess.check_output(['git','-C',str(repo),*args],env=os.environ|{'GIT_OPTIONAL_LOCKS':'0'},stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:raise ValueError('git_source_unavailable_fetch_or_review_ref') from None


class Source:
    def __init__(self, repo, ref, revision=None):
        self.repo=repo.resolve();self.ref=ref
        if not ref.startswith('origin/') or ref.startswith('origin/HEAD'):
            raise ValueError('source_requires_explicit_fetched_origin_ref')
        self.head=git(repo,'rev-parse',ref+'^{commit}').decode().strip()
        self.commit=git(repo,'rev-parse',(revision or self.head)+'^{commit}').decode().strip()
        if subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',self.commit,self.head],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
            raise ValueError('source_not_in_published_ref')
        self.files=git(repo,'ls-tree','-r','--name-only',self.commit).decode().splitlines()
        self.spec=json.loads(self.read(MANIFEST));self.profile=json.loads(self.read(PROFILE))
        self.lock=json.loads(self.read('tools/choms-skills/runtime/RUNTIME.lock.json'))
        self.validate()

    def read(self, path):
        if not path.startswith(PREFIXES) or '..' in Path(path).parts:
            raise ValueError('source_path_outside_allowlist')
        return git(self.repo,'show',self.commit+':'+path)

    def validate(self):
        spec=self.spec
        if spec['schema_version']!=1 or set(spec['common']['mcp'])!={SERVER}:
            raise ValueError('unsupported_workstation_contract')
        if set(spec['common']['mcp'][SERVER])!={'tool','enabled'} or spec['common']['mcp'][SERVER]['tool']!='playwright-mcp' or spec['common']['mcp'][SERVER]['enabled'] is not True:
            raise ValueError('unsupported_mcp_template')
        if sha(self.read(PROFILE))!=spec['common']['profile_sha256'] or sha(self.read('tools/choms-skills/runtime/RUNTIME.lock.json'))!=spec['common']['runtime_lock_sha256']:
            raise ValueError('common_manifest_hash_mismatch')
        indexed={}
        for row in self.read('tools/choms-skills/SHA256SUMS').decode().splitlines():
            digest,name=row.split('  ',1)
            if name in indexed or sha(self.read('tools/choms-skills/'+name))!=digest:
                raise ValueError('profile_source_integrity')
            indexed[name]=digest
        actual={p[len('tools/choms-skills/'):] for p in self.files if p.startswith('tools/choms-skills/') and p!='tools/choms-skills/SHA256SUMS'}
        if actual!=set(indexed):raise ValueError('profile_source_coverage')
        for path,digest in self.lock['helpers'].items():
            if sha(self.read(path))!=digest:raise ValueError('runtime_helper_source_integrity')
        for path,key in [('tools/choms-skills/toolchain/package-lock.json','npm_package_lock_sha256'),('tools/choms-skills/toolchain/package.json','npm_package_json_sha256')]:
            if sha(self.read(path))!=self.lock[key]:raise ValueError('npm_source_integrity')
        if spec['common']['npm']!=json.loads(self.read('tools/choms-skills/toolchain/package-lock.json'))['packages']['']['dependencies']:raise ValueError('manifest_npm_versions_mismatch')
        if spec['common']['platform']!=self.lock['platform']:raise ValueError('manifest_platform_mismatch')
        if spec['common']['tools']!={a['name']:a['version'] for a in self.lock['artifacts']}:
            raise ValueError('manifest_tool_versions_mismatch')

    def publication(self):
        branch='refs/heads/'+self.ref[len('origin/'):]
        value=git(self.repo,'ls-remote','--exit-code','origin',branch).decode().split()
        if not value or value[0]!=self.head:raise ValueError('remote_ref_changed_fetch_and_replan')

    def packages(self):
        indexed={e['name']:e['path'] for e in self.profile['skills']}
        paths={n:indexed[n] for n in self.profile['activation']['selected']}
        paths.update({e['name']:e['path'] for e in self.profile['modular_profiles'].values()})
        result={}
        for name,path in paths.items():
            prefix='tools/choms-skills/'+str(Path(path).parent)+'/'
            items={p[len(prefix):]:sha(self.read(p)) for p in self.files if p.startswith(prefix)}
            result[name]={'path':prefix.rstrip('/'),'files':items,'digest':sha(json.dumps(items,sort_keys=True).encode())}
        if len(result)!=self.spec['common']['skill_count']:raise ValueError('skill_count_mismatch')
        return result

    def materialize(self, root):
        target=root/'sources'/self.commit
        if any(p.is_symlink() for p in target.rglob('*')) if target.exists() else False:raise ValueError('immutable_source_symlink')
        expected={p:sha(self.read(p)) for p in self.files if p.startswith(PREFIXES)}
        if target.exists():
            actual={str(p.relative_to(target)):rt.digest(p) for p in target.rglob('*') if p.is_file()}
            if actual!=expected:raise ValueError('immutable_source_changed')
            return target
        stage=root/'sources'/('.stage-'+uuid.uuid4().hex);stage.mkdir(parents=True)
        for name in expected:
            dest=rt.inside(stage,name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(self.read(name));dest.chmod(0o755 if name.endswith('/runtime.py') else 0o644)
        stage.rename(target)
        return target


def yaml_module(home):
    candidate=home/'.local/share/choms-skills/runtime/current/vendor/pyyaml-6.0.3/lib'
    if candidate.is_dir():
        key=str(candidate.resolve())
        if key not in _VERIFIED_YAML:
            verifier=rt.Runtime(home/'.local/share/choms-skills/runtime',create=False);verifier.verify(verifier.current());_VERIFIED_YAML.add(key)
        sys.path.insert(0,str(candidate))
    import yaml
    return yaml


def config_entry(text, kind, home):
    if not text.strip():return None
    if kind=='codex':
        import tomllib
        doc=tomllib.loads(text) if text.strip() else {}
    else:
        doc=yaml_module(home).safe_load(text) or {}
    if not isinstance(doc,dict):raise ValueError('config_mapping_required')
    servers=doc.get('mcp_servers',{})
    if not isinstance(servers,dict):raise ValueError('mcp_mapping_required')
    return servers.get(SERVER)


def config_span(text,kind,home):
    if kind=='codex':
        pattern=r'(?m)^\[mcp_servers\.'+SERVER+r'\][ \t]*(?:#[^\n]*)?\n'
        match=re.search(pattern,text)
        if not match:raise ValueError('unsupported_owned_toml_layout')
        next_header=re.search(r'(?m)^\s*\[',text[match.end():])
        start=match.start();end=match.end()+next_header.start() if next_header else len(text)
    else:
        yaml=yaml_module(home);top=yaml.compose(text)
        mapping=next(v for k,v in top.value if k.value=='mcp_servers')
        if mapping.flow_style:raise ValueError('nonempty_flow_mcp_mapping_requires_manual_review')
        key,value=next((k,v) for k,v in mapping.value if k.value==SERVER)
        start=text.rfind('\n',0,key.start_mark.index)+1;end=value.end_mark.index
        # Mapping end marks include indentation before the following key.
        if text[text.rfind('\n',0,end)+1:end].strip()=='':end=text.rfind('\n',0,end)+1
    tail=text[start:end].splitlines(keepends=True)
    while tail and (not tail[-1].strip() or tail[-1].lstrip().startswith('#')):end-=len(tail.pop())
    return start,end


def config_render(text,kind,entry,home):
    old=config_entry(text,kind,home)
    if entry is None:
        if old is None:return text
        start,end=config_span(text,kind,home);candidate=text[:start]+text[end:]
        if kind=='hermes' and (yaml_module(home).safe_load(candidate) or {}).get('mcp_servers') is None:
            candidate=re.sub(r'(?m)^mcp_servers:[ \t]*$', 'mcp_servers: {}', candidate)
        return candidate
    if kind=='codex':
        block='[mcp_servers.'+SERVER+']\ncommand = '+json.dumps(entry['command'])+'\nargs = '+json.dumps(entry['args'])+'\nenabled = true\n'
    else:
        block='  '+SERVER+':\n    command: '+json.dumps(entry['command'])+'\n    args: '+json.dumps(entry['args'])+'\n    enabled: true\n'
    if old is not None:
        start,end=config_span(text,kind,home);candidate=text[:start]+block+text[end:]
    elif kind=='codex':candidate=text+('\n' if text.endswith('\n') else '\n\n')+block
    elif not text.strip():candidate='mcp_servers:\n'+block
    else:
        yaml=yaml_module(home);top=yaml.compose(text)
        mapping=next((v for k,v in top.value if k.value=='mcp_servers'),None) if top else None
        if mapping is None:candidate=text+('\n' if text.endswith('\n') else '\n\n')+'mcp_servers:\n'+block
        elif mapping.flow_style and not mapping.value:
            candidate=text[:mapping.start_mark.index]+'\n'+block+text[mapping.end_mark.index:]
        elif mapping.flow_style:raise ValueError('nonempty_flow_mcp_mapping_requires_manual_review')
        else:
            end=mapping.end_mark.index
            if text[text.rfind('\n',0,end)+1:end].strip()=='':end=text.rfind('\n',0,end)+1
            candidate=text[:end]+block+text[end:]
    if (kind=='codex' or text.strip()) and config_entry(candidate,kind,home)!=entry:raise ValueError('rendered_mcp_mismatch')
    return candidate


def package_files(path):
    if not path.is_dir():return None
    result={}
    for p in path.rglob('*'):
        if p.is_symlink():return None
        if p.is_file():result[str(p.relative_to(path))]=rt.digest(p)
    return result


class Workstation:
    def __init__(self, source, home=None, host=None):
        self.source=source;self.home=(home or Path.home()).resolve();self.host=host or socket.gethostname()
        self.root=self.home/'.local/share/choms-workstation';self.runtime_root=self.home/'.local/share/choms-skills/runtime'
        self.state_path=self.root/'state.json'
        self.roots=[self.home/'.agents/skills',self.home/'.hermes/skills']
        self.configs={'codex':self.home/'.codex/config.toml','hermes':self.home/'.hermes/config.yaml'}

    def state(self):return json.loads(self.state_path.read_text()) if self.state_path.is_file() else {'links':{},'mcp':{}}

    def plan(self):
        state=self.state();actions=[];conflicts=[];tokens={};packages=self.source.packages()
        runtime=rt.Runtime(self.runtime_root,create=False);ident=sha(self.source.read('tools/choms-skills/runtime/RUNTIME.lock.json'))[:32]
        try:
            current=runtime.current();runtime.verify(current)
        except (OSError,ValueError):
            current=None
            if (self.runtime_root/'current').is_symlink():conflicts.append('runtime_integrity_failure')
        if current!=ident:actions.append({'kind':'runtime','target':ident})
        else:
            receipt=self.runtime_root/'receipts'/f'{ident}.json'
            if not receipt.is_file() or json.loads(receipt.read_text()).get('status')!='PASS':actions.append({'kind':'runtime_acceptance','target':ident})
        legacy=self.legacy_links()
        for native_root in self.roots:
            if not native_root.resolve().is_relative_to(self.home):conflicts.append('native_root_outside_home');continue
            for name,package in packages.items():
                path=native_root/name;key=str(path.relative_to(self.home));exists=path.exists() or path.is_symlink()
                actual=package_files(path) if path.is_symlink() else None
                tokens[key]={'link':os.readlink(path) if path.is_symlink() else None,'content':sha(json.dumps(actual,sort_keys=True).encode()) if actual is not None else None,'exists':exists}
                if actual==package['files']:
                    if key not in state['links'] and path.is_symlink() and legacy.get(str(path))==os.readlink(path):actions.append({'kind':'adopt_skill','path':key,'name':name})
                    continue
                old=state['links'].get(key)
                if exists and (not old or not path.is_symlink() or os.readlink(path)!=old['target'] or actual!=old['files']):
                    conflicts.append('foreign_or_modified_skill:'+name);continue
                actions.append({'kind':'skill','path':key,'name':name})
        desired={'command':str(self.runtime_root/'bin/choms-runtime'),'args':['run','playwright-mcp'],'enabled':True}
        for kind,path in self.configs.items():
            key=str(path.relative_to(self.home))
            if path.is_symlink():conflicts.append('config_symlink:'+kind);continue
            text=path.read_text() if path.is_file() else ''
            tokens[key]=sha(text.encode()) if path.exists() else None
            try:
                actual=config_entry(text,kind,self.home)
                if actual==desired:continue
                old=state['mcp'].get(kind)
                if actual is not None and (old is None or actual!=old):conflicts.append('foreign_or_modified_mcp:'+kind);continue
                config_render(text,kind,desired,self.home)
                actions.append({'kind':'mcp','client':kind})
            except Exception as error:conflicts.append('config_layout:'+kind+':'+type(error).__name__)
        if platform.system()!='Linux' or platform.machine()!='x86_64':conflicts.append('runtime_platform_unsupported')
        manifest_hash=sha(self.source.read(MANIFEST))
        preconditions={'source':self.source.commit,'manifest_sha256':manifest_hash,'runtime':current,'inputs':tokens,'state':sha(self.state_path.read_bytes()) if self.state_path.is_file() else None}
        return {'schema':1,'host':self.host,'profile':self.host if self.host in self.source.spec['hosts'] else 'default','source_commit':self.source.commit,'source_ref':self.source.ref,'manifest_sha256':manifest_hash,'runtime_target':ident,'runtime_current':current,'actions':actions,'conflicts':conflicts,'converged':not actions and not conflicts,'plan_sha256':sha(json.dumps(preconditions,sort_keys=True).encode()),'optional_capabilities':self.source.spec['optional'],'optional_selection':self.source.spec['hosts'].get(self.host,self.source.spec['hosts']['default'])['optional'],'read_only':True}

    def apply(self, expected_plan):
        plan=self.plan()
        if plan['conflicts']:raise ValueError('unresolved_plan_conflicts')
        if plan['plan_sha256']!=expected_plan:raise ValueError('plan_changed_replan_required')
        self.source.publication()
        for name,module in [('scripts/skills/workstation.py',Path(__file__)),('scripts/skills/runtime.py',Path(rt.__file__)),('scripts/skills/activate_native.py',Path(native.__file__))]:
            if module.read_bytes()!=self.source.read(name):raise ValueError('controller_differs_from_published_source')
        if plan['converged']:return {'status':'PASS','changed':False,'converged':True}
        old=self.state();self.root.mkdir(parents=True,exist_ok=True)
        # Only apply creates a lock or materializes a source. No Git checkout is changed.
        with (self.root/'.lock').open('a') as handle:
            import fcntl
            fcntl.flock(handle,fcntl.LOCK_EX)
            if self.plan()['plan_sha256']!=expected_plan:raise ValueError('plan_changed_replan_required')
            snapshot=self.source.materialize(self.root)
            runtime=rt.Runtime(self.runtime_root,source_root=snapshot)
            old_runtime=runtime.current() if (self.runtime_root/'current').is_symlink() else None
            launcher=self.runtime_root/'bin/choms-runtime'
            old_launcher=os.readlink(launcher) if launcher.is_symlink() else None
            ident=runtime.prepare(snapshot/'tools/choms-skills/runtime/RUNTIME.lock.json')
            env=runtime.environment(runtime.release(ident))
            subprocess.run([sys.executable,str(snapshot/'scripts/skills/validate_profile.py'),'--root',str(snapshot/'tools/choms-skills')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
            receipt=self.runtime_root/'receipts'/f'{ident}.json'
            if not receipt.is_file() or json.loads(receipt.read_text()).get('status')!='PASS':runtime.test(ident)
            if self.plan()['plan_sha256']!=expected_plan:raise ValueError('plan_changed_during_preparation')
            transaction=self.root/'transactions'/uuid.uuid4().hex;transaction.mkdir(parents=True)
            journal={'schema':1,'status':'applying','old_state':old,'old_runtime':old_runtime,'source_root':str(snapshot),'old_activation':json.loads((self.runtime_root/'activation.json').read_text()) if (self.runtime_root/'activation.json').is_file() else None,'old_launcher':old_launcher,'old_previous':os.readlink(self.runtime_root/'previous') if (self.runtime_root/'previous').is_symlink() else None,'new_runtime':ident,'mcp':{},'native_receipt':str(transaction/'native-links.json')}
            rt.write_json(transaction/'journal.json',journal)
            changed_configs=[];native_applied=False;runtime_applied=False
            try:
                runtime_applied=True;runtime.activate(ident)
                packages=self.source.packages();legacy=self.legacy_links()
                receipts=[]
                for number,root in enumerate(self.roots):
                    targets={};previous={}
                    for name,package in packages.items():
                        path=root/name;key=str(path.relative_to(self.home))
                        owned=key in old['links'] or path.is_symlink() and legacy.get(str(path))==os.readlink(path)
                        targets[name]=path.resolve() if not owned and path.is_symlink() and package_files(path)==package['files'] else snapshot/package['path']
                        if key in old['links']:previous[str(path)]=old['links'][key]['target']
                        elif owned:previous[str(path)]=os.readlink(path)
                    record=transaction/f'links-{number}.json';native.activate([root],record,targets=targets,previous=previous);receipts.append(str(record))
                    journal['native_receipts']=list(receipts);rt.write_json(transaction/'journal.json',journal)
                journal['native_receipts']=receipts;native_applied=True
                desired={'command':str(self.runtime_root/'bin/choms-runtime'),'args':['run','playwright-mcp'],'enabled':True}
                for kind,path in self.configs.items():
                    text=path.read_text() if path.is_file() else '';before=config_entry(text,kind,self.home)
                    if before==desired:continue
                    after=config_render(text,kind,desired,self.home)
                    if before is not None and set(before)-{'command','args','enabled'}:raise ValueError('managed_entry_contains_unexpected_fields')
                    journal['mcp'][kind]={'before':before,'after':desired,'file_existed':path.exists()}
                    rt.write_json(transaction/'journal.json',journal)
                    self.write_config(path,text,after);changed_configs.append(kind)
                links=dict(old['links']);legacy=self.legacy_links()
                for root in self.roots:
                    for name,package in packages.items():
                        path=root/name;key=str(path.relative_to(self.home))
                        if key in links or any(a.get('path')==key for a in plan['actions']) or legacy.get(str(path))==os.readlink(path):
                            links[key]={'target':os.readlink(path),'files':package['files']}
                state={'schema':1,'source_commit':self.source.commit,'manifest_sha256':plan['manifest_sha256'],'links':links,'mcp':old['mcp']|{k:desired for k in changed_configs},'transaction':str(transaction)}
                journal['new_state']=state;journal['status']='applied';rt.write_json(transaction/'journal.json',journal);rt.write_json(self.state_path,state)
                final=self.plan()
                if not final['converged']:raise ValueError('post_apply_not_converged')
                return {'status':'PASS','changed':True,'converged':True,'transaction':transaction.name,'runtime_release':ident}
            except Exception:
                for kind in reversed(changed_configs):self.restore_config(kind,journal['mcp'][kind])
                for record in reversed(journal.get('native_receipts',[])):
                    if Path(record).exists():native.rollback(Path(record))
                if runtime_applied:self.restore_runtime(journal)
                if old.get('schema'):rt.write_json(self.state_path,old)
                else:self.state_path.unlink(missing_ok=True)
                journal['status']='rolled_back_after_failure';rt.write_json(transaction/'journal.json',journal)
                raise

    def legacy_links(self):
        path=self.home/('.local/share/choms-skills/activation-'+self.host+'.json')
        if not path.is_file():return {}
        return {e['path']:e['target'] for e in json.loads(path.read_text()).get('created',[])}

    def write_config(self,path,before,after):
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.is_symlink() or (path.read_text() if path.is_file() else '')!=before:raise ValueError('configuration_changed_during_apply')
        temporary=path.with_name('.choms-'+uuid.uuid4().hex)
        try:
            with temporary.open('x') as out:
                temporary.chmod(0o600);out.write(after);out.flush();os.fsync(out.fileno())
            temporary.replace(path)
        finally:temporary.unlink(missing_ok=True)

    def restore_config(self,kind,entry):
        path=self.configs[kind];text=path.read_text()
        if config_entry(text,kind,self.home)!=entry['after']:raise ValueError('managed_config_modified_since_apply:'+kind)
        after=config_render(text,kind,entry['before'],self.home)
        if not entry['file_existed']:
            doc=(__import__('tomllib').loads(after) if kind=='codex' else yaml_module(self.home).safe_load(after)) or {}
            if doc in ({},{'mcp_servers':None},{'mcp_servers':{}}) and not any(line.lstrip().startswith('#') for line in after.splitlines()):
                path.unlink();return
        self.write_config(path,text,after)

    def restore_runtime(self,journal):
        runtime=rt.Runtime(self.runtime_root,source_root=Path(journal['source_root']))
        actual=runtime.current() if (self.runtime_root/'current').is_symlink() else None
        if actual not in (journal['new_runtime'],journal['old_runtime']):raise ValueError('runtime_changed_since_apply')
        if actual!=journal['old_runtime']:
            if journal['old_runtime']:runtime.activate(journal['old_runtime'])
            else:(self.runtime_root/'current').unlink()
        previous=self.runtime_root/'previous'
        if journal.get('old_previous'):rt.atomic_link(previous,journal['old_previous'])
        else:previous.unlink(missing_ok=True)
        if journal.get('old_activation') is not None:rt.write_json(self.runtime_root/'activation.json',journal['old_activation'])
        else:(self.runtime_root/'activation.json').unlink(missing_ok=True)
        launcher=self.runtime_root/'bin/choms-runtime'
        if journal['old_launcher'] is None:launcher.unlink(missing_ok=True)
        else:rt.atomic_link(launcher,journal['old_launcher'])

    def rollback(self):
        state=self.state();transaction=Path(state['transaction']);journal=json.loads((transaction/'journal.json').read_text())
        if journal['status']!='applied':raise ValueError('transaction_not_active')
        for kind,entry in journal['mcp'].items():
            if config_entry(self.configs[kind].read_text(),kind,self.home)!=entry['after']:raise ValueError('managed_config_modified_since_apply:'+kind)
        for record in journal['native_receipts']:
            for entry in json.loads(Path(record).read_text())['created']:
                p=Path(entry['path'])
                if not p.is_symlink() or p.resolve()!=Path(entry['target']):raise ValueError('managed_skill_modified_since_apply')
                key=str(p.relative_to(self.home))
                if key in state['links'] and package_files(p)!=state['links'][key]['files']:raise ValueError('managed_skill_content_modified_since_apply')
        runtime=rt.Runtime(self.runtime_root,create=False)
        if runtime.current()!=journal['new_runtime']:raise ValueError('runtime_changed_since_apply')
        runtime.verify(journal['new_runtime'])
        if journal['old_runtime']:runtime.verify(journal['old_runtime'])
        launcher=self.runtime_root/'bin/choms-runtime'
        if not launcher.is_symlink() or launcher.resolve()!=Path(journal['source_root'])/'scripts/skills/runtime.py':raise ValueError('runtime_launcher_changed_since_apply')
        for kind,entry in reversed(list(journal['mcp'].items())):self.restore_config(kind,entry)
        for record in reversed(journal['native_receipts']):native.rollback(Path(record))
        self.restore_runtime(journal)
        if journal['old_state'].get('schema'):rt.write_json(self.state_path,journal['old_state'])
        else:self.state_path.unlink(missing_ok=True)
        journal['status']='rolled_back';rt.write_json(transaction/'journal.json',journal)
        return {'status':'PASS','rolled_back':True,'transaction':transaction.name}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['check','plan','apply','rollback'])
    parser.add_argument('--source',type=Path,default=rt.REPO)
    parser.add_argument('--ref',default='origin/feat/dev-workstation-sync')
    parser.add_argument('--revision')
    parser.add_argument('--expect-plan')
    args=parser.parse_args()
    source=Source(args.source,args.ref,args.revision);workstation=Workstation(source)
    if os.geteuid()==0:raise ValueError('user_only_no_sudo')
    if args.operation in ('check','plan'):
        result=workstation.plan();result['operation']=args.operation
    elif args.operation=='apply':
        if not args.expect_plan:parser.error('--expect-plan from a reviewed plan is required')
        result=workstation.apply(args.expect_plan)
    else:result=workstation.rollback()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 1 if result.get('conflicts') or args.operation=='check' and not result.get('converged') else 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:
        # Never serialize parser errors, native configuration or credential values.
        safe=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[a-zA-Z0-9_:./-]{1,160}',str(error)) else type(error).__name__
        print(json.dumps({'status':'FAIL','reason':safe}),file=sys.stderr);sys.exit(1)
