"""CHOMS governance reference mechanics. Synthetic temporary queues ONLY; no network."""
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import unicodedata
import uuid

VERSION = 'choms-memory-v1'
OPERATIONS = {'propose', 'remember', 'supersede', 'forget', 'review', 'search', 'checkpoint', 'health'}
TYPES = {'requirement', 'decision', 'objective', 'preference', 'constraint', 'correction', 'checkpoint'}
STATES = {'candidate', 'active', 'superseded', 'forgotten', 'expired'}
IMPORTANCE = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
SOURCES = {'user_explicit', 'agent_inferred', 'repository', 'web', 'tool'}
REQUIRED = {'id','type','scope','project_id','importance','summary','state','source_kind',
            'source_reference','created_at','updated_at','sensitivity','content_hash','schema_version',
            'revision','topic'}
OPTIONAL = {'details','expires_at','supersedes','trigger'}
SECRET = re.compile(
    r'(?i)(?:AGE-SECRET-KEY|-----BEGIN [\w ]*PRIVATE KEY|\bBearer\s+\S+|'
    r'\b(?:password|passwd|contrase[nñ]a|token|cookie|api[_ -]?key|client_secret|authorization)\s*[=:]\s*\S+|'
    r'\b(?:sk|ghp|github_pat)[_-][A-Za-z0-9_-]{12,}|\bauth\.json\s*[:=]\s*\{|'
    r'["\'](?:access_token|refresh_token|id_token)["\']\s*:|\bkind\s*:\s*Secret\b)')

class Rejected(ValueError):
    """Safe reason codes only; never include submitted text."""

class Conflict(Rejected):
    pass

class BackendUnavailable(Rejected):
    pass

def normalized(text):
    return ' '.join(re.findall(r'\w+', ''.join(c for c in unicodedata.normalize('NFKD', text).casefold() if not unicodedata.combining(c))))

def safe(value):
    if isinstance(value,dict):
        if any(str(k).casefold() in {'password','passwd','access_token','refresh_token','id_token','cookie','authorization','private_key','client_secret'} for k in value):raise Rejected('sensitive_input')
        for v in value.values():safe(v)
    elif isinstance(value,list):
        for v in value:safe(v)
    if isinstance(value,dict) and str(value.get('kind','')).casefold()=='secret':raise Rejected('sensitive_input')
    text=json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value
    if re.search(r'(?i)\b[A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)\s*[=:]\s*\S+',text):raise Rejected('sensitive_environment_assignment')
    if len(text)>12000 or SECRET.search(text) or '```' in text or text.count('\n')>25:
        raise Rejected('sensitive_or_unbounded_input')
    return value

def utc(value):
    if not isinstance(value,str) or not value.endswith('Z'):
        raise Rejected('utc_required')
    try: return dt.datetime.fromisoformat(value[:-1]+'+00:00')
    except ValueError: raise Rejected('utc_invalid') from None

def content_hash(record):
    data={k:normalized(record.get(k) or '') for k in ('type','scope','project_id','summary','details','importance','sensitivity','trigger','expires_at')}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def interpret(text):
    """Conservative bilingual routing hint; the runtime must resolve meaning and ambiguity."""
    safe(text)
    n=normalized(text)
    continuity=bool(re.search(r'\b(cuando|when)\b.*\b(diga|say|digo)\b.*\b(continu|retom|resume|continue)',n))
    if continuity:return {'operation':'remember','type':'requirement','importance':'high','continuity':True}
    if re.search(r'\b(no olvides|don t forget|do not forget|keep this)\b',n):return {'operation':'remember','type':'requirement','importance':'high'}
    for operation,pattern in [
        ('forget',r'\b(olvida|borra|elimina|forget|delete|erase)\b'),
        ('supersede',r'\b(corrige|sustituye|reemplaza|replace|supersede|correct)\b'),
        ('checkpoint',r'\b(checkpoint|punto de control)\b'),
        ('search',r'\b(retomemos|seguimos skill|resume|what did we decide|que hab[ií]amos decidido)\b')]:
        if re.search(pattern,n): return {'operation':operation}
    continuity=bool(re.search(r'\b(cuando|when)\b.*\b(diga|say|digo)\b.*\b(continu|retom|resume|continue)',n))
    explicit=continuity or bool(re.search(r'\b(recuerda|guarda|tenlo presente|no se pierda|importante|a partir de ahora|requisito|minimo|remember|save|keep in mind|from now on|requirement|minimum|important)\b',n))
    if not explicit and not re.search(r'\b(architecture|arquitectura|objective|objetivo|constraint|restriction|prefer|reusable|reutilizable|decision|deberia|should)\b',n):return {'operation':'review','actionable':False}
    return {'operation':'remember' if explicit else 'propose',
            'type':'requirement' if continuity else 'decision',
            'importance':'high' if explicit else 'medium', 'continuity':continuity}

def make_record(text, summary, *, project='fixture-project', topic='fixture-topic',
                source='user_explicit', importance=None, kind=None, now='2026-10-27T00:00:00Z',
                details=None, trigger=None, expires_at=None, scope='project'):
    # Raw conversation text is used only for routing; it is never stored.
    safe(text);safe(summary)
    hint=interpret(text)
    record={'schema_version':VERSION,'id':str(uuid.uuid4()),'type':kind or hint.get('type','decision'),
            'scope':scope,'project_id':project if scope=='project' else None,
            'importance':importance or hint.get('importance','medium'),'summary':summary,
            'state':'candidate','source_kind':source,'source_reference':'fixture:synthetic-turn',
            'created_at':now,'updated_at':now,'sensitivity':'internal','revision':1,'topic':topic}
    for k,v in [('details',details),('trigger',trigger),('expires_at',expires_at)]:
        if v is not None:record[k]=v
    record['content_hash']=content_hash(record)
    validate(record)
    return record

def validate(r):
    safe(r)
    if not isinstance(r,dict) or set(r)-REQUIRED-OPTIONAL or REQUIRED-set(r):raise Rejected('record_schema')
    if r['schema_version']!=VERSION or r['type'] not in TYPES or r['state'] not in STATES:raise Rejected('record_enum')
    if r['scope'] not in {'global','personal','project'} or (r['scope']=='project')!=bool(r['project_id']):raise Rejected('scope_invalid')
    if r['importance'] not in IMPORTANCE or r['source_kind'] not in SOURCES or r['sensitivity'] not in {'public','internal','personal'}:raise Rejected('record_enum')
    for k,maxlen in [('summary',500),('details',1500),('source_reference',160),('topic',100),('trigger',160),('project_id',100)]:
        if k in r and r[k] is not None and (not isinstance(r[k],str) or not 0<len(r[k])<=maxlen):raise Rejected('field_bound')
    try:uuid.UUID(r['id'])
    except (ValueError,TypeError,AttributeError):raise Rejected('id_invalid') from None
    if type(r['revision']) is not int or r['revision']<1:raise Rejected('revision_invalid')
    if utc(r['updated_at'])<utc(r['created_at']):raise Rejected('time_order')
    if r.get('expires_at') and utc(r['expires_at'])<=utc(r['created_at']):raise Rejected('expiry_invalid')
    if r['content_hash']!=content_hash(r):raise Rejected('content_hash_invalid')
    return r

class DisabledBridge:
    """No implicit MCP dispatch, fallback, queue flush or network access."""
    def health(self):
        return {'central_persistence':False,'reason':'record_crud_cas_and_purge_not_verified'}
    def call(self, operation, payload=None):
        if operation not in OPERATIONS:raise Rejected('operation_invalid')
        if operation=='health':return self.health()
        raise BackendUnavailable('central_memory_disabled_no_write_or_read_claim')

class SyntheticQueue:
    """Versioned JSON fixture, NOT a second production memory system."""
    def __init__(self, directory, *, synthetic=False):
        p=Path(directory)
        if not synthetic or p.is_symlink() or not p.is_dir() or p.resolve().parent!=Path(tempfile.gettempdir()).resolve() or not p.name.startswith('choms-memory-test-'):
            raise Rejected('synthetic_temporary_directory_required')
        s=p.stat()
        if s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:raise Rejected('private_directory_required')
        self.root=p
        self.path=p/'queue.json'
        self.lock=p/'queue.lock'

    def _read(self):
        if self.path.is_symlink():raise Rejected('unsafe_queue')
        if not self.path.exists():return {'schema_version':VERSION,'revision':0,'records':[],'audit':[]}
        if self.path.is_symlink() or stat.S_IMODE(self.path.stat().st_mode)!=0o600:raise Rejected('unsafe_queue')
        raw=self.path.read_bytes()
        if len(raw)>1024*1024:raise Rejected('queue_limit')
        value=json.loads(raw)
        if set(value)!={'schema_version','revision','records','audit'} or value['schema_version']!=VERSION:raise Rejected('queue_schema')
        return value

    def read(self):
        # A rename exposes only a complete old or new generation.
        return copy.deepcopy(self._read())

    def apply(self, operation, *, expected_revision, record=None, target=None, explicit=False,
              equivalent_to=None, now='2026-10-27T00:00:00Z'):
        if operation not in OPERATIONS-{'health','review','search'}:raise Rejected('mutation_invalid')
        utc(now)
        fd=os.open(self.lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            if os.fstat(fd).st_uid!=os.getuid() or not stat.S_ISREG(os.fstat(fd).st_mode) or stat.S_IMODE(os.fstat(fd).st_mode)!=0o600:raise Rejected('unsafe_lock')
            fcntl.flock(fd,fcntl.LOCK_EX)
            doc=self._read()
            if doc['revision']!=expected_revision:raise Conflict('stale_revision_reload_and_reconcile')
            rows=doc['records']
            if operation=='forget':
                if not explicit:raise Rejected('explicit_forget_required')
                found=[r for r in rows if r['id']==target]
                if not found:raise Rejected('target_missing')
                doc['records']=[r for r in rows if r['id']!=target]
                # Purge content, source, original hash and details; only opaque ID remains.
                doc['audit'].append({'operation':'forget','id':target,'state':'forgotten'})
                result={'id':target,'state':'forgotten','content_removed':True}
            else:
                validate(record)
                if not record['source_reference'].startswith('fixture:'):raise Rejected('synthetic_reference_required')
                if record['source_kind'] in {'web','tool','repository'}:raise Rejected('untrusted_source_not_user_instruction')
                if explicit and record['source_kind']!='user_explicit':raise Rejected('explicit_user_source_required')
                if operation in {'remember','supersede'} and not explicit:raise Rejected('explicit_consent_required')
                active=[r for r in rows if r['state']=='active' and (not r.get('expires_at') or utc(r['expires_at'])>utc(now))]
                matches=[r for r in rows if r['state'] in {'active','candidate'} and r['content_hash']==record['content_hash'] and (not r.get('expires_at') or utc(r['expires_at'])>utc(now))]
                if matches and matches[0]['state']=='candidate' and operation=='remember' and explicit:
                    prior=matches[0];rows.remove(prior);record=copy.deepcopy(record)
                    record.update(id=prior['id'],created_at=prior['created_at'],revision=prior['revision']+1)
                    matches=[]
                if equivalent_to:
                    match=next((r for r in active if r['id']==equivalent_to),None)
                    if not explicit or match is None or (match['scope'],match['project_id'])!=(record['scope'],record['project_id']):raise Rejected('semantic_equivalence_requires_explicit_scoped_review')
                    matches=[match]
                if matches:return {'duplicate_of':matches[0]['id'],'revision':doc['revision']}
                result=copy.deepcopy(record)
                result['state']='active' if explicit and operation in {'remember','supersede','checkpoint'} else 'candidate'
                conflicts=[r for r in active if (r['scope'],r['project_id'],r['topic'])==(result['scope'],result['project_id'],result['topic'])]
                if operation=='supersede':
                    prior=next((r for r in rows if r['id']==target and r['state']=='active'),None)
                    if prior is None or (prior['scope'],prior['project_id'])!=(result['scope'],result['project_id']):raise Rejected('correction_target_invalid')
                    if any(r['id']!=target for r in conflicts):raise Rejected('unresolved_conflicts')
                    prior.update(state='superseded',updated_at=now,revision=prior['revision']+1)
                    result['supersedes']=target
                elif conflicts:
                    result['state']='candidate' # A later timestamp never silently wins.
                result['updated_at']=now
                validate(result);rows.append(result)
            doc['revision']+=1
            data=json.dumps(doc,sort_keys=True,ensure_ascii=False).encode()
            if len(data)>1024*1024:raise Rejected('queue_limit')
            # No journal, backup copy or payload in error messages.
            tmpfd,name=tempfile.mkstemp(prefix='.queue-',dir=self.root)
            try:
                with os.fdopen(tmpfd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
                os.replace(name,self.path)
                dfd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(dfd)
                finally:os.close(dfd)
            finally:
                if os.path.exists(name):os.unlink(name)
            return {**result,'queue_revision':doc['revision'],'central_persisted':False}
        finally:os.close(fd)

    def search(self, query, *, project, now='2026-10-27T00:00:00Z', include_medium=False,
               explicit_low=False, limit=5, budget_chars=2400, include_personal=False):
        safe(query);utc(now)
        if not 1<=limit<=10 or not 128<=budget_chars<=6000:raise Rejected('context_budget_invalid')
        hits=[]
        for r in self.read()['records']:
            validate(r)
            if r['state']!='active' or r.get('expires_at') and utc(r['expires_at'])<=utc(now):continue
            if r['scope']=='project' and r['project_id']!=project:continue
            if r['scope']=='personal' and not include_personal:continue
            if r['importance']=='medium' and not include_medium:continue
            if r['importance']=='low' and not explicit_low:continue
            terms=set(normalized(query).split());hay=normalized(' '.join([r['summary'],r.get('details',''),r.get('trigger','')]))
            if not terms.intersection(hay.split()):continue
            hits.append(r)
        hits.sort(key=lambda r:(IMPORTANCE[r['importance']],r['created_at'],r['id']))
        selected=[]
        for r in hits:
            if len(selected)>=limit:break
            # Bound actual serialized context including provenance, not only summary length.
            if len(json.dumps(selected+[r],ensure_ascii=False))<=budget_chars:selected.append(r)
        return {'records':selected,'central_persisted':False,'used_chars':len(json.dumps(selected,ensure_ascii=False))}

    def review(self, *, project):
        return [validate(r) for r in self.read()['records'] if r['scope']=='project' and r['project_id']==project]

    def expire(self, *, expected_revision, now):
        # Expiry is derived on reads; no content is injected after expiry.
        if self.read()['revision']!=expected_revision:raise Conflict('stale_revision_reload_and_reconcile')
        return [{'id':r['id'],'state':'expired'} for r in self.read()['records'] if r.get('expires_at') and utc(r['expires_at'])<=utc(now)]

if __name__=='__main__':
    print(json.dumps(DisabledBridge().health(),sort_keys=True))
