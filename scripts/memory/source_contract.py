#!/usr/bin/env python3
"""Fail-closed admission for the public CHOMS memory corpus. No secret values logged."""
import fnmatch
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path('/home/chomsmaster/projects/choms-homelab-public')
DENIED_PARTS = {'.git', '.cache', '__pycache__', 'node_modules', 'vendor', '.venv',
                'venv', 'dist', 'build', 'backups', 'backup', 'plaintext', 'decrypted',
                'unpacked', 'personal', 'private', 'transcripts', 'transcriptions', 'sessions', '.codebase-memory'}
DENIED_NAMES = ('*.env', '.env*', '*.tfstate*', '*kubeconfig*', '*.key', '*.pem',
                '*.p12', '*.pfx', '*.age', '*.db', '*.sqlite*', '*.tar*', '*.zip',
                '*.gz', '*.jpg', '*.png', '*.mp4', '*.mp3', '*.pdf', '*.bundle',
                'id_rsa*', 'id_ed25519*', '*age.key*', '*credentials*')
TEXT_SUFFIXES = {'.md', '.sh', '.py', '.yaml', '.yml', '.json', '.toml', '.tf',
                 '.txt', '.gitignore', '.gitattributes', '.cbmignore'}
SENSITIVE = re.compile(
    rb'AGE-SECRET-KEY-[A-Z0-9]{20,}|-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|'
    rb'(?im:^\s*(?:Authorization|Cookie|Set-Cookie)\s*:\s*\S+)|'
    rb'\b(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_]{15,}'
)

def allowed_path(relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or any(v in DENIED_PARTS for v in p.parts):
        return False
    if p.parts[:2] == ('docs', 'archive'):
        return False
    if any(fnmatch.fnmatch(p.name.lower(), pattern.lower()) for pattern in DENIED_NAMES):
        return False
    return p.suffix in TEXT_SUFFIXES or p.name in {'Dockerfile', '.gitignore', '.gitattributes', '.yamllint', '.cbmignore'}

def allowed_content(data):
    if b'\0' in data or SENSITIVE.search(data):
        return False
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return False
    # Exclude Kubernetes Secret documents entirely, including synthetic payloads.
    if re.search(r"(?m)^\s*kind:\s*['\"]?Secret['\"]?\s*(?:#.*)?$", text):
        return False
    if re.search(r'(?m)^\s*(?:client-key-data|client-certificate-data):', text):
        return False
    try:
        document = json.loads(text)
    except (ValueError, TypeError):
        document = None
    def forbidden_json(value):
        if isinstance(value, dict):
            if value.get('kind') == 'Secret' or {'terraform_version', 'serial', 'lineage'} <= value.keys():
                return True
            if any(k in value for k in ('private_key', 'client_secret', 'access_token', 'refresh_token')):
                return True
            return any(forbidden_json(v) for v in value.values())
        return isinstance(value, list) and any(forbidden_json(v) for v in value)
    return not forbidden_json(document)

def corpus(root=ROOT):
    root = root.resolve()
    if root != ROOT:
        raise ValueError('Only the authorized public checkout is admissible')
    raw = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z'])
    # Only public tracked files plus this explicitly authorized feature's files.
    names = {v for v in raw.decode().split('\0') if v}
    for prefix in ('scripts/memory', 'docs/incidents', 'stacks/kubernetes/choms-memory', 'stacks/kubernetes/openhands'):
        directory = root / prefix
        if directory.exists():
            names.update(str(p.relative_to(root)) for p in directory.rglob('*') if p.is_file() and not p.is_symlink())
    for name in ('docs/operations/MEMORY_PLATFORM.md', '.cbmignore'):
        if (root / name).is_file():
            names.add(name)
    admitted = []
    for name in sorted(names):
        if not allowed_path(name):
            continue
        path = root / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != (root / Path(name).parent).resolve():
            continue
        if root not in path.resolve().parents:
            continue
        data = path.read_bytes()
        if allowed_content(data):
            admitted.append(name)
    return admitted

def main():
    paths = corpus()
    # The native index's final allowlist is exact: no unknown untracked files.
    lines = ['# Generated public corpus allowlist; regenerate explicitly.', '**', '!*/']
    lines += ['!/' + name for name in paths]
    # Final exclusions cannot be undone by preceding allowlist entries.
    lines += ['.git/', '.cache/', 'node_modules/', 'docs/archive/', '.env*', '*.tfstate*',
              '*kubeconfig*', '*.key', '*.pem', '*.age', 'backups/', 'personal/']
    (ROOT / '.cbmignore').write_text('\n'.join(lines) + '\n')
    print('PUBLIC_CORPUS_FILES=' + str(len(paths)))

if __name__ == '__main__':
    main()
