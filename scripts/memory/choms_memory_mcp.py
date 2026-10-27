"""User-level native stdio launcher; no local credentials, OAuth or background service."""
import argparse
import os
import re
import sys


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ssh-target',required=True)
    p.add_argument('--client',choices=('codex','hermes'),required=True)
    a=p.parse_args()
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*@[a-zA-Z0-9.-]+',a.ssh_target):p.error('invalid_ssh_target')
    # Every command word after the destination is fixed except the enumerated client.
    command='kubectl --request-timeout=15s -n choms-memory exec -i deployment/choms-memory -- /src/.venv/bin/python /app/stdio_bridge.py --client '+a.client
    argv=['ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','ConnectTimeout=6',
          '-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','ForwardAgent=no',
          '-o','IdentityAgent=none','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',a.ssh_target,command]
    os.execvp('ssh',argv)

if __name__=='__main__':main()
