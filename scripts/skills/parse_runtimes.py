"""Parse CHOMS skills with native Codex discovery and upstream Hermes parser; no turns."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2] / 'tools/choms-skills'


def run(hermes_source):
    paths = sorted((ROOT / 'skills').glob('*/SKILL.md')) + sorted((ROOT / 'modules').glob('*/*/SKILL.md'))
    names = {p.parent.name for p in paths}
    sys.path.insert(0, str(hermes_source))
    spec = importlib.util.spec_from_file_location('choms_upstream_hermes_skill_utils', hermes_source / 'agent/skill_utils.py')
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
    parsed = 0
    # Calling the actual YAML loader first prevents accepting Hermes fallback parsing.
    native.yaml_load('name: parser-preflight')
    for path in paths:
        meta, body = native.parse_frontmatter(path.read_text())
        assert meta['name'] == path.parent.name and meta['description'] and body.strip(), 'Hermes metadata'
        parsed += 1
    with tempfile.TemporaryDirectory(prefix='choms-native-parse-') as tmp:
        work = Path(tmp); skills = work / '.agents/skills'; skills.mkdir(parents=True)
        home = work / 'codex-config'; home.mkdir()
        for path in paths:
            (skills / path.parent.name).symlink_to(path.parent, target_is_directory=True)
        (home / 'config.toml').write_text('[analytics]\nenabled = false\n')
        proc = subprocess.Popen(['codex', 'app-server', '--listen', 'stdio://'],
            cwd=work, env=os.environ | {'CODEX_HOME': str(home)}, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        selector = selectors.DefaultSelector(); selector.register(proc.stdout, selectors.EVENT_READ)

        def request(ident, method, params):
            proc.stdin.write(json.dumps({'id': ident, 'method': method, 'params': params}) + '\n'); proc.stdin.flush()
            while True:
                if not selector.select(30):
                    raise RuntimeError('Codex parser timeout')
                line = proc.stdout.readline()
                if not line:
                    raise RuntimeError('Codex parser closed')
                reply = json.loads(line)
                if reply.get('id') == ident:
                    if 'error' in reply:
                        raise RuntimeError('Codex parser request rejected')
                    return reply['result']
        try:
            request(1, 'initialize', {'clientInfo': {'name': 'choms-parser', 'version': '1.0.0'}})
            proc.stdin.write('{"method":"initialized","params":{}}\n'); proc.stdin.flush()
            result = request(2, 'skills/list', {'cwds': [str(work)], 'forceReload': True})
            entries = [s for item in result['data'] for s in item['skills'] if s['name'] in names]
            errors = [e for item in result['data'] for e in item.get('errors', []) if str(ROOT) in str(e)]
            expected = {p.parent.name: p.resolve() for p in paths}
            assert all(Path(s['path']).resolve() == expected[s['name']] for s in entries), 'Codex source paths'
            assert not errors, 'Codex parse errors'
            assert {s['name'] for s in entries if s.get('enabled', True)} == names, 'Codex discovery'
        finally:
            selector.close(); proc.stdin.close(); proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=5)
            proc.stdout.close()
    return {'status': 'PASS', 'scope': 'temporary project discovery; no native activation',
            'codex': {'version': subprocess.check_output(['codex', '--version'], text=True).strip(),
                      'discovered': len(names), 'errors': len(errors), 'inferences': 0},
            'hermes': {'parsed': parsed, 'parser_sha256': hashlib.sha256((hermes_source / 'agent/skill_utils.py').read_bytes()).hexdigest(),
                       'scope': 'upstream native parse_frontmatter and yaml_load; not full Hermes catalog/slash', 'inferences': 0}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--hermes-source', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(run(args.hermes_source), sort_keys=True))
