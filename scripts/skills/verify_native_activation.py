"""Native installed-root discovery and payload loading; no model turns or gateway."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
from activate_native import ROOT, entries


def verify(hermes_source):
    expected = entries()
    sys.path.insert(0, str(hermes_source))
    from hermes_constants import get_skills_dir
    from tools.skills_tool import skills_list, skill_view
    from agent.skill_commands import build_skill_invocation_message, get_interactive_skill_commands
    hermes_root = get_skills_dir()
    codex_root = Path.home() / '.agents/skills'
    for root in (codex_root, hermes_root):
        for name, target in expected.items():
            path = root / name
            assert path.is_symlink() and path.resolve() == target.resolve(), 'native_link:' + name
    catalog = json.loads(skills_list())
    assert catalog.get('success'), 'Hermes catalog failed'
    listed = {s['name'] for s in catalog['skills']}
    assert set(expected) <= listed, 'Hermes missing skill'
    commands = get_interactive_skill_commands()
    for name, target in expected.items():
        payload = json.loads(skill_view(name, preprocess=False))
        assert payload.get('success'), 'Hermes view:' + name
        assert payload['content'] == (target / 'SKILL.md').read_text(), 'Hermes full content:' + name
        key = '/' + name
        assert key in commands, 'Hermes slash missing:' + name
        message = build_skill_invocation_message(key, 'Validar carga local sin inferencia.')
        assert message and name in message, 'Hermes slash load:' + name
        # Body must be present in the native rendered payload, not only the name.
        body = (target / 'SKILL.md').read_text().split('---', 2)[2].strip()
        assert body in message, 'Hermes slash content:' + name
    with tempfile.TemporaryDirectory(prefix='choms-installed-codex-') as temp:
        config = Path(temp) / 'config'; config.mkdir()
        (config / 'config.toml').write_text('[analytics]\nenabled = false\n')
        # Isolated config avoids initializing existing MCP connections. User-root
        # discovery uses the real home, with no temporary skill links or HOME override.
        proc = subprocess.Popen(['codex', 'app-server', '--listen', 'stdio://'], cwd=temp,
            env=os.environ | {'CODEX_HOME': str(config)}, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        selector = selectors.DefaultSelector(); selector.register(proc.stdout, selectors.EVENT_READ)
        def request(ident, method, params):
            proc.stdin.write(json.dumps({'id': ident, 'method': method, 'params': params})+'\n'); proc.stdin.flush()
            while True:
                if not selector.select(30):
                    raise RuntimeError('native Codex timeout')
                line = proc.stdout.readline()
                if not line:
                    raise RuntimeError('native Codex closed')
                reply = json.loads(line)
                if reply.get('id') == ident:
                    assert 'error' not in reply, 'native Codex request error'
                    return reply['result']
        try:
            request(1, 'initialize', {'clientInfo': {'name': 'choms-native-activation', 'version': '1.0.0'}})
            proc.stdin.write('{"method":"initialized","params":{}}\n');proc.stdin.flush()
            data = request(2, 'skills/list', {'cwds': [temp], 'forceReload': True})['data']
            discovered = [s for item in data for s in item['skills'] if s['name'] in expected]
            assert {s['name'] for s in discovered if s.get('enabled', True)} == set(expected), 'Codex discovery'
            assert all(Path(s['path']).resolve() == expected[s['name']]/'SKILL.md' for s in discovered), 'Codex path'
            assert not [e for item in data for e in item.get('errors', []) if str(ROOT) in str(e)], 'Codex errors'
            for skill in discovered:
                assert Path(skill['path']).read_bytes() == (expected[skill['name']]/'SKILL.md').read_bytes(), 'Codex load'
        finally:
            selector.close();proc.stdin.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
            proc.stdout.close()
    return {'status':'PASS','host':os.uname().nodename,'codex':{'native_user_discovery':len(expected),'full_content_reads':len(expected),'parse_errors':0,'inferences':0},
            'hermes':{'native_catalog':len(expected),'skill_view_full_content':len(expected),'slash_payloads':len(expected),'inferences':0,'source_commit':'a938f00f0f3cdf00fdb93d9a82a9ae447e9b857f','scope':'actual upstream skills subsystem; no chat/model/gateway'},
            'baseline_skills':9,'new_modules':4,'optional_activated':False,'publication':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--hermes-source',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(verify(args.hermes_source.resolve()),sort_keys=True))
