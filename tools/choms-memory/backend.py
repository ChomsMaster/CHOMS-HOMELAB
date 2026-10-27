"""Canonical PostgreSQL + isolated Cognee projections. No raw-content logging."""
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace
import uuid
import threading

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, register_uuid
register_uuid()
import ladybug
import cognee
from cognee.infrastructure.databases.dataset_database_handler import supported_dataset_database_handlers  # noqa: F401
from cognee.infrastructure.databases.graph.ladybug.LadybugDatasetDatabaseHandler import LadybugDatasetDatabaseHandler as GH
from cognee.infrastructure.databases.vector.pgvector.PGVectorSharedDatasetDatabaseHandler import PGVectorSharedDatasetDatabaseHandler as VH
from fastembed import TextEmbedding
import governance
from contract import Fault, arguments, partition, record_input, bounded, now, identifier
from purge import RegistryEntry, purge, SUFFIXES


class Backend:
    def __init__(self):
        self.root = Path(os.environ['SYSTEM_ROOT_DIRECTORY'])/'databases'
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.lock = threading.RLock()
        self.cache = {}  # No query/result cache; retained for explicit purge checks.
        self.backup_ack = os.environ.get('MEMORY_BACKUP_POLICY_ACKNOWLEDGED') == 'true'
        self.real = os.environ.get('MEMORY_ALLOW_REAL') == 'true' and self.backup_ack
        self.model = None

    def connect(self):
        c = psycopg2.connect(host=os.environ['DB_HOST'], port=int(os.environ['DB_PORT']),
            dbname=os.environ['DB_NAME'], user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD'], connect_timeout=10,
            options='-c statement_timeout=20000 -c lock_timeout=15000 -c idle_in_transaction_session_timeout=30000')
        c.autocommit = True
        return c

    @contextmanager
    def session(self):
        with self.lock:
            conn = self.connect()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as c:
                    c.execute("SELECT pg_advisory_lock(hashtext('choms-memory-v1'))")
                    try:
                        yield c
                    finally:
                        c.execute("SELECT pg_advisory_unlock(hashtext('choms-memory-v1'))")
            finally:
                conn.close()

    def initialize(self):
        lock = json.loads(Path('/app/purge-contract.json').read_text())
        if importlib.metadata.version('cognee') != lock['cognee'] or ladybug.Database.get_version() != lock['ladybug']:
            raise Fault('backend_version_mismatch')
        if hashlib.sha256(Path(inspect.getfile(GH)).read_bytes()).hexdigest() != lock['handler_sha256']:
            raise Fault('handler_contract_mismatch')
        with self.session() as c:
            with c.connection:
                c.execute(Path('/app/001.sql').read_text())
            c.execute('SELECT version FROM choms_memory.schema_version ORDER BY version')
            if [r['version'] for r in c.fetchall()] != [1]:
                raise Fault('migration_version_mismatch')
        self.model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5', threads=1,
            specific_model_path=os.environ['MEMORY_EMBEDDING_PATH'], local_files_only=True)
        with self.session() as c:
            c.execute('SELECT * FROM choms_memory.purge_jobs ORDER BY id')
            for job in c.fetchall():
                self._finish_forget(c,job)
            c.execute("SELECT * FROM choms_memory.records WHERE projection_state IN ('pending','purge_pending') ORDER BY id")
            for row in c.fetchall():
                if row['projection_state'] == 'purge_pending':
                    raise Fault('purge_registry_incomplete')
                else:
                    self._project(c, row)

    def _expire(self, c):
        c.execute("SELECT * FROM choms_memory.records WHERE state IN ('active','candidate') AND body->>'expires_at' IS NOT NULL")
        for row in c.fetchall():
            if datetime.fromisoformat(row['body']['expires_at'].replace('Z','+00:00')) <= datetime.now(timezone.utc):
                body = row['body']; body.update(state='expired', revision=row['revision']+1, updated_at=now())
                c.execute("UPDATE choms_memory.records SET state='expired',revision=%s,body=%s WHERE id=%s",
                          (body['revision'], json.dumps(body), str(row['id'])))

    def _get(self, c, memory_id, scope=None):
        c.execute('SELECT * FROM choms_memory.records WHERE id=%s', (identifier(str(memory_id)),))
        row = c.fetchone()
        if row and scope is not None and (row['scope'],row['project']) != scope:
            raise Fault('not_found')
        return row

    def _cas(self, row, revision):
        if row is None:
            raise Fault('not_found')
        if type(revision) is not int or row['revision'] != revision:
            raise Fault('cas_conflict')
        if row['state'] == 'purge_pending':
            raise Fault('purge_pending', retryable=True)

    def _receipt(self, row):
        return {'id':str(row['id']), 'state':row['state'], 'revision':row['revision']}

    def _vector(self, text):
        return '['+','.join(str(float(n)) for n in next(iter(self.model.embed([text]))))+']'

    def _descriptor(self, row):
        if row['vector_info']:
            from cognee.infrastructure.databases.postgres import dataset_schema_name
            info=row['vector_info']
            if info['schema']!=dataset_schema_name(uuid.UUID(str(row['id']))) or info['host']!=os.environ['DB_HOST'] or int(info['port'])!=int(os.environ['DB_PORT']):
                raise Fault('dataset_registry_mismatch')
        return SimpleNamespace(owner_id=row['id'], graph_database_name=str(row['id'])+'.pkl',
            vector_database_provider='pgvector', vector_database_url='', vector_database_name=os.environ['DB_NAME'],
            vector_database_key='', vector_database_connection_info=dict(row['vector_info'] or {}),
            vector_dataset_database_handler='pgvector_shared')

    def _official_graph(self, row):
        asyncio.run(GH.delete_dataset(self._descriptor(row)))

    def _owned_vector(self,c,row):
        c.execute('SELECT r.rolname FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner WHERE n.nspname=%s',
                  (row['vector_info']['schema'],))
        owner=c.fetchone()
        if owner and owner['rolname']!=os.environ['DB_USERNAME']:
            raise Fault('shared_dataset_rejected')

    def _clean_graph(self, row):
        async def official():
            await GH.delete_dataset(self._descriptor(row))
        asyncio.run(purge(self.root, RegistryEntry(str(row['id']),str(row['id']),True), official))

    def _project(self, c, row):
        # The canonical record is committed first. Pending projection repair uses
        # the same private UUID unit and official deletion before rebuilding.
        self._clean_graph(row)
        if row['vector_info']:
            self._owned_vector(c,row)
            asyncio.run(VH.delete_dataset(self._descriptor(row)))
        from cognee.infrastructure.databases.postgres import dataset_schema_name
        info={'schema':dataset_schema_name(uuid.UUID(str(row['id']))),
              'host':os.environ['DB_HOST'],'port':int(os.environ['DB_PORT'])}
        c.execute('UPDATE choms_memory.records SET vector_info=%s WHERE id=%s', (json.dumps(info),str(row['id'])))
        row['vector_info']=info
        self._owned_vector(c,row)
        info = asyncio.run(VH.create_dataset(uuid.UUID(str(row['id'])), None))['vector_database_connection_info']
        c.execute('UPDATE choms_memory.records SET vector_info=%s WHERE id=%s', (json.dumps(info),str(row['id'])))
        row['vector_info'] = info
        directory = self.root/str(row['id'])
        body = row['body']; text = body['summary']+' '+body.get('details','')
        db = ladybug.Database(directory/(str(row['id'])+'.pkl'), buffer_pool_size=67108864, max_num_threads=1)
        connection = ladybug.Connection(db)
        try:
            connection.execute('CREATE NODE TABLE Memory(id STRING, text STRING, PRIMARY KEY(id))').close()
            connection.execute('CREATE (m:Memory {id: $id, text: $text})', {'id':str(row['id']),'text':text}).close()
        finally:
            connection.close(); db.close()
        c.execute(sql.SQL('CREATE TABLE {} (id uuid PRIMARY KEY, embedding public.vector(384))').format(
            sql.Identifier(info['schema'],'embeddings')))
        c.execute(sql.SQL('INSERT INTO {} VALUES (%s,%s::public.vector)').format(
            sql.Identifier(info['schema'],'embeddings')), (str(row['id']),self._vector(text)))
        c.execute("UPDATE choms_memory.records SET projection_state='ready' WHERE id=%s",(str(row['id']),))
        row['projection_state']='ready'

    def _insert(self, c, body, lineage=None):
        c.execute('SELECT count(*) AS n FROM choms_memory.records WHERE scope=%s AND project=%s',(body['scope'],body.get('project_id') or ''))
        if c.fetchone()['n']>=200:raise Fault('partition_capacity_limit')
        c.execute('SELECT id FROM choms_memory.records WHERE scope=%s AND project=%s AND content_hash=%s AND state IN (%s,%s)',
                  (body['scope'],body.get('project_id') or '',body['content_hash'],'active','candidate'))
        if c.fetchone():
            raise Fault('duplicate')
        if body['state']=='active':
            c.execute("SELECT id FROM choms_memory.records WHERE scope=%s AND project=%s AND topic=%s AND state='active'",
                      (body['scope'],body.get('project_id') or '',body['topic']))
            if c.fetchone():
                raise Fault('ambiguous_contradiction_use_supersede')
        c.execute('INSERT INTO choms_memory.records VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s,%s)',
            (body['id'],lineage or body['id'],json.dumps(body),body['scope'],body.get('project_id') or '',
             body['topic'],body['state'],body['revision'],'pending' if body['state']=='active' else 'none',body['content_hash']))
        return self._get(c,body['id'])

    def _purge(self, c, row):
        memory_id=str(row['id'])
        # Clear canonical content/hash before effects, preserving only internal
        # UUID metadata needed for safe reconciliation. Never acknowledge early.
        c.execute("UPDATE choms_memory.records SET body=NULL,content_hash=NULL,state='purge_pending',projection_state='purge_pending' WHERE id=%s",(memory_id,))
        self._clean_graph(row)
        if row['vector_info']:
            self._owned_vector(c,row)
            asyncio.run(VH.delete_dataset(self._descriptor(row)))
            c.execute('SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s) AS remains',
                      (row['vector_info']['schema'],))
            if c.fetchone()['remains']:
                raise Fault('purge_pending',retryable=True)
        self.cache.pop(memory_id,None)
        if os.listdir(self.root/memory_id) or memory_id in self.cache:
            raise Fault('purge_pending',retryable=True)
        with c.connection:
            c.execute('SELECT request_id FROM choms_memory.receipts WHERE target_id=%s',(memory_id,))
            requests=[str(r['request_id']) for r in c.fetchall()]
            c.execute('DELETE FROM choms_memory.receipts WHERE target_id=%s',(memory_id,))
            c.execute("INSERT INTO choms_memory.tombstones VALUES(%s,'forgotten',%s,%s::uuid[]) ON CONFLICT(id) DO NOTHING",
                      (memory_id,row['revision']+1,requests))
            c.execute('DELETE FROM choms_memory.records WHERE id=%s',(memory_id,))

    def _finish_forget(self,c,job):
        try:
            for value in job['members']:
                row=self._get(c,str(value))
                if row:self._purge(c,row)
            c.execute('SELECT count(*) AS n FROM choms_memory.records WHERE id=ANY(%s::uuid[])',
                      ([str(v) for v in job['members']],))
            if c.fetchone()['n']:raise Fault('purge_pending',retryable=True)
            with c.connection:
                c.execute('UPDATE choms_memory.tombstones SET request_ids=request_ids||%s::uuid[] WHERE id=%s',
                          ([str(v) for v in job['request_ids']],str(job['id'])))
                c.execute('DELETE FROM choms_memory.purge_jobs WHERE id=%s',(str(job['id']),))
        except Exception:
            raise Fault('purge_pending',retryable=True) from None

    def _audit(self,c,ids):
        if self.real:
            raise Fault('synthetic_audit_disabled')
        if not isinstance(ids,list) or len(ids)>20:
            raise Fault('invalid_audit')
        result=[]
        for value in ids:
            value=identifier(value)
            row=self._get(c,value)
            c.execute('SELECT * FROM choms_memory.tombstones WHERE id=%s',(value,)); tomb=c.fetchone()
            if row is None and tomb is None:
                raise Fault('not_found')
            # Only internally registered opaque IDs can reach filesystem checks.
            trusted=str(row['id'] if row else tomb['id'])
            directory=self.root/trusted
            files=len(os.listdir(directory)) if directory.is_dir() else 0
            from cognee.infrastructure.databases.postgres import dataset_schema_name
            vector_schema=dataset_schema_name(uuid.UUID(trusted))
            c.execute('SELECT count(*) AS n FROM pg_namespace WHERE nspname=%s',(vector_schema,))
            vectors=c.fetchone()['n']
            c.execute('SELECT count(*) AS n FROM choms_memory.receipts WHERE target_id=%s',(trusted,))
            receipts=c.fetchone()['n']
            result.append({'id':trusted,'canonical_rows':int(row is not None), 'graph_artifacts':files,
                           'vector_schemas':vectors,'cache_entries':int(trusted in self.cache),
                           'content_receipts':receipts,'tombstone':bool(tomb),
                           'tombstone_fields':sorted(tomb) if tomb else []})
        return result

    def call(self, operation, args):
        arguments(operation,args)
        try:
            governance.safe(args)
        except governance.Rejected:
            raise Fault('sensitive_or_untrusted_input') from None
        with self.session() as c:
            self._expire(c)
            if operation=='health':
                c.execute('SELECT version FROM choms_memory.schema_version'); versions=[r['version'] for r in c.fetchall()]
                return {'status':'ready','schema_versions':versions,'automatic_capture':False,
                        'real_memory_allowed':self.real,'backup_policy_approved':self.backup_ack,
                        'audit':self._audit(c,args['audit_ids']) if 'audit_ids' in args else []}
            if operation in ('search','review'):
                scope=partition(args)
                if 'id' in args:
                    row=self._get(c,args['id'],scope)
                    rows=[row['body']] if row and row['body'] is not None else []
                else:
                    states=args.get('states',['active'] if operation=='search' else ['candidate','active'])
                    if not isinstance(states,list) or not states or set(states)-{'candidate','active','superseded','expired'}:
                        raise Fault('invalid_states')
                    c.execute('SELECT * FROM choms_memory.records WHERE scope=%s AND project=%s AND state=ANY(%s) ORDER BY id',(*scope,states))
                    found=c.fetchall(); rows=[]
                    query=args.get('query','')
                    if operation=='search':
                        if not isinstance(query,str) or not 0<len(query)<=500:
                            raise Fault('invalid_query')
                        vector=self._vector(query)
                        ranked=[]
                        for row in found:
                            body=row['body']
                            if body['importance']=='low' and not args.get('include_low'):continue
                            if body['importance']=='medium' and not args.get('include_medium'):continue
                            if row['projection_state']!='ready':raise Fault('projection_unavailable',retryable=True)
                            c.execute(sql.SQL('SELECT 1-(embedding <=> %s::public.vector) AS score FROM {}').format(
                                sql.Identifier(row['vector_info']['schema'],'embeddings')),(vector,))
                            score=c.fetchone()['score'];ranked.append((score,body))
                        rows=[r for _,r in sorted(ranked,key=lambda v:v[0],reverse=True)]
                    else:rows=[r['body'] for r in found if r['body'] is not None]
                return bounded(rows,args)
            request_id=args['request_id']
            if 'id' in args:
                c.execute('SELECT * FROM choms_memory.purge_jobs WHERE %s::uuid=ANY(members)',(args['id'],))
                job=c.fetchone()
                if job:
                    self._finish_forget(c,job)
                    return {'id':args['id'],'state':'forgotten'}
            # Content-free tombstones fence retries of requests already erased.
            c.execute('SELECT id,revision FROM choms_memory.tombstones WHERE %s::uuid=ANY(request_ids)',(request_id,))
            tomb=c.fetchone()
            if tomb:return {'id':str(tomb['id']),'state':'forgotten','revision':tomb['revision']}
            fingerprint=hashlib.sha256(json.dumps(args,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            c.execute('SELECT * FROM choms_memory.receipts WHERE request_id=%s',(request_id,))
            replay=c.fetchone()
            if replay:
                if replay['operation']!=operation or replay['fingerprint']!=fingerprint:
                    raise Fault('idempotency_conflict')
                row=self._get(c,str(replay['target_id']))
                if row and row['projection_state']=='pending':self._project(c,row)
                if row and row['state']=='purge_pending':raise Fault('purge_pending',retryable=True)
                return self._receipt(row) if row else {'state':'forgotten','id':str(replay['target_id'])}
            if operation=='forget':
                row=self._get(c,args['id'],partition(args))
                if row is None:
                    c.execute('SELECT id,revision FROM choms_memory.tombstones WHERE id=%s',(args['id'],))
                    tomb=c.fetchone()
                    if tomb:return {'id':str(tomb['id']),'state':'forgotten','revision':tomb['revision']}
                self._cas(row,args['expected_revision'])
                c.execute('SELECT id FROM choms_memory.records WHERE lineage_id=%s ORDER BY id',(str(row['lineage_id']),))
                members=[str(r['id']) for r in c.fetchall()]
                with c.connection:
                    c.execute('INSERT INTO choms_memory.purge_jobs VALUES(%s,%s::uuid[],%s::uuid[])',
                              (args['id'],members,[request_id]))
                    c.execute("UPDATE choms_memory.records SET body=NULL,content_hash=NULL,state='purge_pending',projection_state='purge_pending' WHERE id=ANY(%s::uuid[])",(members,))
                job={'id':args['id'],'members':members,'request_ids':[request_id]}
                self._finish_forget(c,job)
                return {'id':args['id'],'state':'forgotten','revision':row['revision']+1,'lineage_erased':len(members)}
            body=None
            if operation=='remember' and 'id' in args:
                row=self._get(c,args['id'],partition(args));self._cas(row,args['expected_revision'])
                if row['state']!='candidate':raise Fault('candidate_required')
                body=dict(row['body']);body.update(state='active',revision=row['revision']+1,updated_at=now(),source_kind='user_explicit')
                # Enforce one active topic and dedup before transitioning.
                c.execute("SELECT id FROM choms_memory.records WHERE scope=%s AND project=%s AND topic=%s AND state='active'",(row['scope'],row['project'],row['topic']))
                if c.fetchone():raise Fault('ambiguous_contradiction_use_supersede')
                with c.connection:
                    c.execute("UPDATE choms_memory.records SET body=%s,state='active',revision=%s,projection_state='pending' WHERE id=%s",(json.dumps(body),body['revision'],args['id']))
                    c.execute('INSERT INTO choms_memory.receipts VALUES(%s,%s,%s,%s)',(request_id,operation,args['id'],fingerprint))
                row=self._get(c,args['id'])
            else:
                body=record_input(args['record'],explicit=operation in ('remember','supersede') or args.get('explicit',False),
                                  real_allowed=self.real,checkpoint=operation=='checkpoint')
                with c.connection:
                    lineage=None
                    if operation=='supersede':
                        prior=self._get(c,args['id'],partition(args));self._cas(prior,args['expected_revision'])
                        if prior['state']!='active' or (body['scope'],body.get('project_id') or '')!=(prior['scope'],prior['project']):raise Fault('invalid_supersede_target')
                        old=dict(prior['body']);old.update(state='superseded',revision=prior['revision']+1,updated_at=now())
                        c.execute("UPDATE choms_memory.records SET body=%s,state='superseded',revision=%s WHERE id=%s",(json.dumps(old),old['revision'],str(prior['id'])))
                        body['supersedes']=str(prior['id']);lineage=str(prior['lineage_id'])
                    row=self._insert(c,body,lineage)
                    c.execute('INSERT INTO choms_memory.receipts VALUES(%s,%s,%s,%s)',(request_id,operation,body['id'],fingerprint))
            if row['projection_state']=='pending':self._project(c,row)
            return self._receipt(row)
