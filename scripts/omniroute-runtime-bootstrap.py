#!/usr/bin/env python3
"""Explicit creation of new runtime Secrets over SSH stdin; never prints values."""
import argparse
import json
import os
import re
import secrets
import subprocess

SSH = ['ssh', '-F', '/dev/null', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=6',
       '-o', 'ConnectionAttempts=1', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no',
       '-o', 'ForwardAgent=no', '-o', 'IdentityAgent=none', ]


def remote(command, data=None, timeout=60):
    target = os.environ.get('OMNIROUTE_SSH_TARGET', '')
    if not re.fullmatch(r'([a-zA-Z_][a-zA-Z0-9_.-]*@)?[a-zA-Z0-9][a-zA-Z0-9.-]*', target):
        raise RuntimeError('An explicit valid OMNIROUTE_SSH_TARGET is required.')
    result = subprocess.run(SSH + [target, command], input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Runtime operation failed; sensitive diagnostics withheld.')
    return result.stdout


def create_runtime_secrets():
    # Never replace/re-generate an existing runtime identity, even on a retry.
    namespace = json.loads(remote('kubectl get namespace omniroute -o json --request-timeout=10s'))
    if namespace.get('metadata', {}).get('labels', {}).get('app.kubernetes.io/part-of') != 'choms-platforms':
        raise RuntimeError('Namespace ownership mismatch.')
    for name in ['omniroute-runtime', 'omniroute-redis-auth']:
        result = remote('kubectl -n omniroute get secret ' + name + ' -o name --ignore-not-found --request-timeout=10s')
        if result.strip():
            raise RuntimeError('Runtime Secret already exists; preserve it and review adoption.')
    own_key = 'omni_' + secrets.token_urlsafe(48)
    redis_password = secrets.token_urlsafe(48)
    values = {
        'OMNIROUTE_API_KEY': own_key,
        'JWT_SECRET': secrets.token_hex(64),
        'API_KEY_SECRET': secrets.token_hex(32),
        'STORAGE_ENCRYPTION_KEY': secrets.token_hex(32),
        'INITIAL_PASSWORD': secrets.token_urlsafe(48),
        'REDIS_URL': 'redis://:' + redis_password + '@omniroute-redis:6379/0',
    }
    redis_config = ('bind 0.0.0.0\nprotected-mode yes\nport 6379\ndir /data\n'
                    'appendonly yes\nappendfsync everysec\nmaxmemory 256mb\n'
                    'maxmemory-policy noeviction\nrequirepass ' + redis_password + '\n')
    # Construct in memory only. Do not write objects, subprocess input or errors to disk/logs.
    for name, entries in [('omniroute-redis-auth', {'password': redis_password, 'redis.conf': redis_config}),
                          ('omniroute-runtime', values)]:
        body = {'apiVersion': 'v1', 'kind': 'Secret', 'type': 'Opaque',
                'metadata': {'name': name, 'namespace': 'omniroute',
                             'labels': {'app.kubernetes.io/part-of': 'choms-platforms'}},
                'stringData': entries}
        remote('kubectl create -f - -o name --field-manager=choms-omniroute --request-timeout=15s', json.dumps(body).encode())
    return own_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create-runtime-secrets', action='store_true', required=True)
    parser.parse_args()
    try:
        create_runtime_secrets()
    except Exception:
        print('Runtime bootstrap stopped; no values rendered; preserve any existing Secrets.')
        return 1
    print('New runtime Secrets created. No provider configured; no values rendered.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
