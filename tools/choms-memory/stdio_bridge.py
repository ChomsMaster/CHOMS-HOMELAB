"""Runs INSIDE the adapter Pod. Credentials never traverse SSH or agent config."""
import argparse
import json
from pathlib import Path
import sys
import urllib.request
import urllib.error


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--client',choices=('codex','hermes'),required=True)
    args=parser.parse_args()
    token=Path('/auth/'+args.client).read_text().strip()
    while True:
        line=sys.stdin.buffer.readline(16385)
        if not line:return
        if len(line)>16384 or not line.strip():raise SystemExit('invalid_mcp_frame')
        try:
            payload=json.loads(line)
            request=urllib.request.Request('http://127.0.0.1:8080/mcp',data=json.dumps(payload).encode(),
                headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
            with urllib.request.urlopen(request,timeout=90) as response:
                raw=response.read(65537)
                if len(raw)>65536:raise ValueError
                if raw:print(json.dumps(json.loads(raw)),flush=True)
        except Exception:
            print(json.dumps({'event':'mcp_transport_failed'}),file=sys.stderr)
            raise SystemExit(1)

if __name__=='__main__':main()
