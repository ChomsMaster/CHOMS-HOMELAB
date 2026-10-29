"""Local stdio MCP fixture: validates a brief in memory, no filesystem or network tools."""
import json
import sys
from local_tools import FIELDS, LISTS, validate_brief

SCHEMA = {'type': 'object', 'additionalProperties': False,
          'required': list(FIELDS + LISTS), 'properties': {
              **{key: {'type': 'string', 'minLength': 1} for key in FIELDS},
              **{key: {'type': 'array', 'minItems': 1, 'items': {'type': 'string', 'minLength': 1}} for key in LISTS}}}
TOOL = {'name': 'validate_design_brief', 'description': 'Validate an in-memory design brief without side effects.',
        'inputSchema': SCHEMA, 'annotations': {'readOnlyHint': True, 'destructiveHint': False,
        'idempotentHint': True, 'openWorldHint': False}}


def dispatch(request):
    ident = request.get('id')
    if ident is None:
        return None
    method = request.get('method')
    if method == 'initialize':
        result = {'protocolVersion': '2025-11-25', 'capabilities': {'tools': {}},
                  'serverInfo': {'name': 'choms-design-fixture', 'version': '1.0.0'}}
    elif method == 'tools/list':
        result = {'tools': [TOOL]}
    elif method == 'tools/call':
        params = request.get('params', {})
        if not isinstance(params, dict):
            return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32602, 'message': 'Object params required'}}
        if params.get('name') != TOOL['name']:
            return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32602, 'message': 'Unknown tool'}}
        try:
            value = validate_brief(params.get('arguments'))
            result = {'content': [{'type': 'text', 'text': json.dumps(value)}], 'isError': False}
        except ValueError as exc:
            result = {'content': [{'type': 'text', 'text': str(exc)}], 'isError': True}
    elif method == 'ping':
        result = {}
    else:
        return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32601, 'message': 'Method not found'}}
    return {'jsonrpc': '2.0', 'id': ident, 'result': result}


if __name__ == '__main__':
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError()
            reply = dispatch(request)
        except (ValueError, TypeError):
            reply = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Invalid JSON request'}}
        if reply is not None:
            print(json.dumps(reply), flush=True)
