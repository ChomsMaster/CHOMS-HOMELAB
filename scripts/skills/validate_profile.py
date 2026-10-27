"""Read-only CHOMS profile validation; no runtime/configuration or network changes."""
import hashlib
import json
from pathlib import Path
import sys
import yaml


def validate(root):
    profile=json.loads((root/'PROFILE.json').read_text())
    assert profile['version']=='1.3.0','profile_version'
    names=profile['activation']['selected']
    assert len(names)==len(set(names))==9,'selected_count'
    assert profile['governance']['central_persistence']=='synthetic-only' and profile['governance']['real_memories'] is False,'real_memory_gate'
    assert profile['activation']['optional']==['choms-verification-loop'],'optional_unchanged'
    indexed={e['name']:e for e in profile['skills']}
    for name in names:
        e=indexed[name];path=root/e['path'];text=path.read_text()
        assert path.resolve().is_relative_to(root.resolve()),'skill_scope'
        assert text.startswith('---\n'),'frontmatter_missing'
        meta=yaml.safe_load(text.split('---',2)[1]);assert meta['name']==name and meta['description'],'metadata'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==e['sha256'],'entry_hash'
    expected={}
    for row in (root/'SHA256SUMS').read_text().splitlines():
        sha,name=row.split('  ',1);assert name not in expected,'duplicate_hash_entry'
        p=root/name;assert p.resolve().is_relative_to(root.resolve()) and not p.is_symlink(),'hash_scope'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,'file_hash'
        expected[name]=sha
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
    assert actual==set(expected),'hash_coverage'
    return {'profile_version':profile['version'],'selected':len(names),'files_hashed':len(expected),'status':'PASS'}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]/'tools/choms-skills'
    print(json.dumps(validate(root),sort_keys=True))
