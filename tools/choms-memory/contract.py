"""CHOMS Memory v1: bounded MCP contract and governance validation (stdlib)."""
from datetime import datetime, timezone
import json
import uuid
import governance

OPERATIONS = ('health', 'propose', 'remember', 'search', 'review', 'supersede', 'forget', 'checkpoint')


class Fault(Exception):
    def __init__(self, code, *, retryable=False):
        self.code, self.retryable = code, retryable
        super().__init__(code)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def identifier(value):
    try:
        parsed = uuid.UUID(value)
        if str(parsed) != value or parsed.version != 4:
            raise ValueError
        return value
    except (ValueError, TypeError, AttributeError):
        raise Fault('invalid_identifier') from None


def partition(args):
    scope, project = args.get('scope'), args.get('project_id')
    if scope not in ('global', 'personal', 'project') or (scope == 'project') != bool(project):
        raise Fault('invalid_scope')
    if project is not None and (not isinstance(project, str) or not 1 <= len(project) <= 100):
        raise Fault('invalid_project')
    return scope, project or ''


def record_input(payload, *, explicit, real_allowed=False, checkpoint=False):
    allowed = {'summary', 'details', 'type', 'importance', 'scope', 'project_id',
               'source_kind', 'source_reference', 'sensitivity', 'topic', 'trigger', 'expires_at'}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise Fault('invalid_record_fields')
    try:
        governance.safe(payload)
        scope, project = partition(payload)
        source = payload.get('source_kind')
        if source in ('repository', 'web', 'tool'):
            raise Fault('untrusted_source')
        if source != ('user_explicit' if explicit else 'agent_inferred'):
            raise Fault('consent_source_mismatch')
        ref = payload.get('source_reference', '')
        if not real_allowed and not ref.startswith('fixture:'):
            raise Fault('real_memory_backup_gate_closed')
        r = governance.make_record('remember this' if explicit else 'inferred context',
            payload['summary'], project=project, scope=scope, source=source,
            kind='checkpoint' if checkpoint else payload.get('type', 'decision'),
            importance=payload.get('importance', 'high' if explicit else 'medium'),
            topic=payload.get('topic', 'memory'), now=now(), details=payload.get('details'),
            trigger=payload.get('trigger'), expires_at=payload.get('expires_at'))
        r.update(source_reference=ref, sensitivity=payload.get('sensitivity', 'internal'),
                 state='active' if explicit else 'candidate')
        r['content_hash'] = governance.content_hash(r)
        governance.validate(r)
        return r
    except Fault:
        raise
    except (governance.Rejected, KeyError, TypeError, ValueError):
        raise Fault('record_rejected') from None


def bounded(rows, args):
    limit, budget = args.get('limit', 5), args.get('budget_chars', 2400)
    if type(limit) is not int or not 1 <= limit <= 10 or type(budget) is not int or not 256 <= budget <= 6000:
        raise Fault('invalid_context_budget')
    output = []
    for row in rows:
        if len(output) >= limit:
            break
        if len(json.dumps(output + [row], ensure_ascii=False)) <= budget:
            output.append(row)
    return {'records': output, 'omitted': len(rows)-len(output),
            'characters': len(json.dumps(output, ensure_ascii=False))}


SCOPE = {'scope': {'type': 'string', 'enum': ['global', 'personal', 'project']},
         'project_id': {'type': ['string', 'null'], 'maxLength': 100}}
RECORD = {'type': 'object', 'additionalProperties': False, 'properties': {
    **SCOPE, 'summary': {'type': 'string', 'minLength': 1, 'maxLength': 500},
    'details': {'type': 'string', 'maxLength': 1500},
    'type': {'type': 'string', 'enum': sorted(governance.TYPES)},
    'importance': {'type': 'string', 'enum': ['critical', 'high', 'medium', 'low']},
    'source_kind': {'type': 'string', 'enum': ['user_explicit', 'agent_inferred']},
    'source_reference': {'type': 'string', 'minLength': 1, 'maxLength': 160},
    'sensitivity': {'type': 'string', 'enum': ['public', 'internal', 'personal']},
    'topic': {'type': 'string', 'minLength': 1, 'maxLength': 100},
    'trigger': {'type': 'string', 'maxLength': 160},
    'expires_at': {'type': 'string', 'format': 'date-time'}},
    'required': ['summary', 'scope', 'source_kind', 'source_reference', 'topic']}
UUID = {'type': 'string', 'format': 'uuid'}
BUDGET = {'limit': {'type': 'integer', 'minimum': 1, 'maximum': 10},
          'budget_chars': {'type': 'integer', 'minimum': 256, 'maximum': 6000}}
SCHEMAS = {
    'health': {'audit_ids': {'type': 'array', 'items': UUID, 'maxItems': 20}},
    'propose': {'request_id': UUID, 'record': RECORD},
    'remember': {**SCOPE, 'request_id': UUID, 'record': RECORD, 'id': UUID,
                 'expected_revision': {'type': 'integer', 'minimum': 1}, 'explicit': {'const': True}},
    'search': {**SCOPE, **BUDGET, 'query': {'type': 'string', 'minLength': 1, 'maxLength': 500},
               'include_medium': {'type': 'boolean'}, 'include_low': {'type': 'boolean'}},
    'review': {**SCOPE, **BUDGET, 'id': UUID, 'states': {'type': 'array', 'items': {
        'enum': ['candidate', 'active', 'superseded', 'expired']}, 'maxItems': 4}},
    'supersede': {**SCOPE, 'request_id': UUID, 'id': UUID, 'expected_revision': {'type': 'integer', 'minimum': 1},
                  'record': RECORD, 'explicit': {'const': True}},
    'forget': {**SCOPE, 'request_id': UUID, 'id': UUID, 'expected_revision': {'type': 'integer', 'minimum': 1},
               'explicit': {'const': True}},
    'checkpoint': {'request_id': UUID, 'record': RECORD, 'explicit': {'type': 'boolean'}},
}
REQUIRED = {'health': [], 'propose': ['request_id', 'record'],
    'remember': ['request_id', 'explicit'], 'search': ['scope', 'query'], 'review': ['scope'],
    'supersede': ['request_id', 'id', 'scope', 'expected_revision', 'record', 'explicit'],
    'forget': ['request_id', 'id', 'scope', 'expected_revision', 'explicit'],
    'checkpoint': ['request_id', 'record']}
TOOLS = [{'name': name, 'description': 'CHOMS governed memory: '+name+'; no automatic capture.',
          'inputSchema': {'type': 'object', 'properties': SCHEMAS[name],
                          'required': REQUIRED[name], 'additionalProperties': False},
          'annotations': {'readOnlyHint': name in ('health', 'search', 'review'),
                          'destructiveHint': name == 'forget', 'openWorldHint': False}}
         for name in OPERATIONS]


def schema_check(value, schema):
    types = schema.get('type')
    valid = {'object':type(value) is dict, 'array':type(value) is list,
             'string':type(value) is str, 'integer':type(value) is int,
             'boolean':type(value) is bool, 'null':value is None}
    if types and not any(valid.get(t,False) for t in ([types] if isinstance(types,str) else types)):
        raise Fault('invalid_argument_type')
    if 'const' in schema and (type(value) is not type(schema['const']) or value!=schema['const']):
        raise Fault('invalid_argument_value')
    if 'enum' in schema and value not in schema['enum']:raise Fault('invalid_argument_value')
    if type(value) is dict:
        if set(schema.get('required',[]))-set(value):raise Fault('missing_arguments')
        if schema.get('additionalProperties') is False and set(value)-set(schema.get('properties',{})):raise Fault('invalid_arguments')
        for key,item in value.items():
            if key in schema.get('properties',{}):schema_check(item,schema['properties'][key])
    if type(value) is list:
        if len(value)>schema.get('maxItems',100):raise Fault('argument_limit')
        for item in value:schema_check(item,schema.get('items',{}))
    if type(value) is str and not schema.get('minLength',0)<=len(value)<=schema.get('maxLength',10000):raise Fault('argument_limit')
    if type(value) is int and not schema.get('minimum',-10**10)<=value<=schema.get('maximum',10**10):raise Fault('argument_limit')


def arguments(operation, args):
    if operation in OPERATIONS:
        schema_check(args,next(t['inputSchema'] for t in TOOLS if t['name']==operation))
    if operation not in OPERATIONS or not isinstance(args, dict) or set(args)-set(SCHEMAS[operation]):
        raise Fault('invalid_arguments')
    if set(REQUIRED[operation])-set(args):
        raise Fault('missing_arguments')
    if 'request_id' in args:
        identifier(args['request_id'])
    if 'id' in args:
        identifier(args['id'])
    if operation in ('remember', 'supersede', 'forget') and args.get('explicit') is not True:
        raise Fault('explicit_consent_required')
    if operation == 'remember' and (('id' in args) == ('record' in args)):
        raise Fault('choose_candidate_or_record')
    if 'expected_revision' in args and (type(args['expected_revision']) is not int or args['expected_revision'] < 1):
        raise Fault('invalid_revision')
    if operation == 'remember' and 'id' in args and 'expected_revision' not in args:
        raise Fault('revision_required')
    return args
