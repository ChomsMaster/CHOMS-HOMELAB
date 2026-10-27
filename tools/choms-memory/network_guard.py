"""Defense in depth for Python-origin automatic egress; NetworkPolicy covers native code."""
import os
import socket
import sys

BLOCKED=0


def install():
    host=os.environ['DB_HOST']
    ips={entry[4][0] for entry in socket.getaddrinfo(host,int(os.environ['DB_PORT']),type=socket.SOCK_STREAM)}
    def audit(event,args):
        global BLOCKED
        denied=False
        if event=='socket.getaddrinfo':
            denied=args[0] not in ({host}|ips)
        elif event=='socket.connect':
            address=args[1]
            denied=not isinstance(address,tuple) or address[0] not in ips or address[1]!=int(os.environ['DB_PORT'])
        if denied:
            BLOCKED+=1
            raise PermissionError('unauthorized_outbound_blocked')
    sys.addaudithook(audit)
