#!/usr/bin/env python3
"""Download only the pinned local-model files; no credentials or inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True)
    args = parser.parse_args()
    cache = Path(args.cache).expanduser()
    if cache.is_symlink() or ROOT == cache.resolve() or ROOT in cache.resolve().parents:
        raise SystemExit('Model cache must be a real directory outside Git')
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    cache.chmod(0o700)
    lock = json.loads((ROOT / 'docs/architecture/memory/models-lock.json').read_text())
    result = []
    for model in lock['models']:
        repo, revision = model['repository'], model['revision']
        base = cache / 'hub' / ('models--' + repo.replace('/', '--'))
        for spec in model['files']:
            file = base / 'snapshots' / revision / spec['path']
            if file.is_symlink():
                raise SystemExit('Model symlink rejected')
            file.parent.mkdir(parents=True, exist_ok=True)
            if not file.exists():
                tmp = file.with_name(file.name + '.partial')
                if tmp.exists():
                    raise SystemExit('Partial model file requires review')
                request = urllib.request.Request(
                    f'https://huggingface.co/{repo}/resolve/{revision}/{spec["path"]}',
                    headers={'User-Agent': 'CHOMS-pinned-local-models/1'})
                try:
                    with urllib.request.urlopen(request, timeout=120) as source, tmp.open('xb') as target:
                        os.chmod(tmp, 0o600)
                        while True:
                            block = source.read(1024 * 1024)
                            if not block:
                                break
                            target.write(block)
                        target.flush()
                        os.fsync(target.fileno())
                    if tmp.stat().st_size != spec['bytes']:
                        raise ValueError('Model size mismatch')
                    actual = digest(tmp)
                    if spec['expected_sha256'] and actual != spec['expected_sha256']:
                        raise ValueError('Model digest mismatch')
                    if spec['git_blob_sha1'] and not spec['expected_sha256']:
                        data = tmp.read_bytes()
                        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                        if blob != spec['git_blob_sha1']:
                            raise ValueError('Model config provenance mismatch')
                    tmp.replace(file)
                except Exception as error:
                    # Never render signed CDN URLs or request diagnostics.
                    raise SystemExit('Model preparation failed: ' + type(error).__name__) from None
            if file.stat().st_size != spec['bytes']:
                raise SystemExit('Existing model size mismatch')
            actual = digest(file)
            if spec['expected_sha256'] and actual != spec['expected_sha256']:
                raise SystemExit('Existing model digest mismatch')
            result.append({'repository': repo, 'revision': revision, 'path': spec['path'],
                           'sha256': actual, 'bytes': file.stat().st_size})
        refs = base / 'refs'
        refs.mkdir(exist_ok=True)
        (refs / 'main').write_text(revision)
        (refs / 'main').chmod(0o600)
    manifest = {'files': result, 'total_bytes': sum(f['bytes'] for f in result)}
    (cache / 'MODEL_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (cache / 'MODEL_MANIFEST.json').chmod(0o600)
    print('CHECK_PASS pinned_models_downloaded_once bytes=' + str(manifest['total_bytes']))

if __name__ == '__main__':
    main()
