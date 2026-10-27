"""Authenticated internal MCP JSON-RPC endpoint; stdio bridge is the client transport."""
import collections
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time
import traceback
import warnings

logging.disable(logging.CRITICAL)
warnings.filterwarnings('ignore', category=UserWarning)
from contract import Fault, TOOLS, OPERATIONS
import network_guard

COUNTERS=collections.Counter()
DURATION=collections.Counter()
BACKEND=None
TOKENS={}
MAX_REQUEST=16384


def authenticated(header):
    return any(hmac.compare_digest(header.encode(),('Bearer '+token).encode()) for token in TOKENS.values())


def rpc(request):
    if not isinstance(request,dict) or request.get('jsonrpc')!='2.0':
        return {'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'invalid_request'}}
    method=request.get('method'); identifier=request.get('id')
    if not isinstance(request.get('params',{}),dict):
        return {'jsonrpc':'2.0','id':identifier,'error':{'code':-32602,'message':'invalid_params'}}
    if method=='notifications/initialized' or (isinstance(method,str) and method.startswith('notifications/')):
        return None
    if method=='initialize':
        version=request.get('params',{}).get('protocolVersion','2024-11-05')
        supported=('2024-11-05','2025-03-26','2025-06-18','2025-11-25')
        return {'jsonrpc':'2.0','id':identifier,'result':{'protocolVersion':version if version in supported else supported[-1],
            'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'choms-memory','version':'1.0.0'}}}
    if method=='ping':return {'jsonrpc':'2.0','id':identifier,'result':{}}
    if method=='tools/list':return {'jsonrpc':'2.0','id':identifier,'result':{'tools':TOOLS}}
    if method!='tools/call':return {'jsonrpc':'2.0','id':identifier,'error':{'code':-32601,'message':'method_not_found'}}
    params=request.get('params',{}); name=params.get('name'); start=time.monotonic()
    if name not in OPERATIONS:
        return {'jsonrpc':'2.0','id':identifier,'error':{'code':-32602,'message':'unknown_tool'}}
    try:
        data=BACKEND.call(name,params.get('arguments',{}))
        if name=='health':data['blocked_automatic_outbound_attempts']=network_guard.BLOCKED
        result={'ok':True,'data':data}; outcome='success'
    except Fault as e:
        result={'ok':False,'error':{'code':e.code,'retryable':e.retryable}};outcome='rejected'
    except Exception as error:
        print(json.dumps({'event':'backend_error','operation':name,'class':type(error).__name__,
            'sqlstate':getattr(error,'pgcode',None),'errno':getattr(error,'errno',None),
            'frames':[{'module':Path(f.filename).name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)[-4:]]}),file=sys.stderr)
        result={'ok':False,'error':{'code':'backend_unavailable','retryable':True}};outcome='error'
    COUNTERS[name,outcome]+=1;DURATION[name]+=time.monotonic()-start
    return {'jsonrpc':'2.0','id':identifier,'result':{'content':[{'type':'text','text':json.dumps(result)}],
            'structuredContent':result,'isError':not result['ok']}}


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup();self.connection.settimeout(20)
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/ready':
            try:
                BACKEND.call('health',{});status=200
            except Exception:status=503
            self.send_response(status);self.end_headers();return
        if self.path!='/metrics' or not authenticated(self.headers.get('Authorization','')):
            self.send_response(401);self.end_headers();return
        lines=[f'choms_memory_blocked_outbound_attempts_total {network_guard.BLOCKED}']
        for (operation,outcome),value in sorted(COUNTERS.items()):
            lines.append(f'choms_memory_operations_total{{operation="{operation}",outcome="{outcome}"}} {value}')
        for operation,value in sorted(DURATION.items()):
            lines.append(f'choms_memory_operation_seconds_sum{{operation="{operation}"}} {value:.6f}')
        self.send_response(200);self.end_headers();self.wfile.write(('\n'.join(lines)+'\n').encode())
    def do_POST(self):
        if self.path!='/mcp' or not authenticated(self.headers.get('Authorization','')):
            self.send_response(401);self.end_headers();return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=MAX_REQUEST:raise ValueError
            request=json.loads(self.rfile.read(length))
            result=rpc(request)
            if result is None:self.send_response(202);self.end_headers();return
            raw=json.dumps(result).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(raw)
        except (ValueError,TypeError,KeyError):
            self.send_response(400);self.end_headers()


def main():
    global BACKEND,TOKENS
    try:
        TOKENS={client:Path('/auth/'+client).read_text().strip() for client in ('codex','hermes')}
        if len(set(TOKENS.values()))!=2 or any(len(token)<32 for token in TOKENS.values()):raise Fault('authentication_config_invalid')
        network_guard.install()
        from backend import Backend
        BACKEND=Backend();BACKEND.initialize()
        def terminate(signum,frame):raise SystemExit(0)
        signal.signal(signal.SIGTERM,terminate)
        HTTPServer(('0.0.0.0',8080),Handler).serve_forever()
    except (KeyboardInterrupt,SystemExit):pass
    except Exception as error:
        print(json.dumps({'event':'startup_failed','class':type(error).__name__,'code':error.code if isinstance(error,Fault) else 'backend_unavailable'}),file=sys.stderr)
        raise SystemExit(1)

if __name__=='__main__':main()
