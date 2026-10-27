"""Authenticated synthetic-only deployment gate for the narrow purge adapter.

This is NOT the production memory MCP. It cannot accept real memories. The gate
uses the installed official handlers, local embeddings and the shared PostgreSQL
backend, with a dedicated role/schema/root. No Cognee global handler is patched.
"""
import asyncio
from contextlib import contextmanager
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.metadata
import json
import os
from pathlib import Path
import re
import threading
import traceback
from types import SimpleNamespace
import uuid

import psycopg2
from psycopg2 import sql
import ladybug
import cognee  # Initialize installed package's normal import order, not an AST copy.
from cognee.infrastructure.databases.dataset_database_handler import supported_dataset_database_handlers  # noqa: F401
from cognee.infrastructure.databases.graph.ladybug.LadybugDatasetDatabaseHandler import (
    LadybugDatasetDatabaseHandler as GraphHandler,
)
from cognee.infrastructure.databases.vector.pgvector.PGVectorSharedDatasetDatabaseHandler import (
    PGVectorSharedDatasetDatabaseHandler as VectorHandler,
)
from fastembed import TextEmbedding
from purge import RegistryEntry, SUFFIXES, purge

SCHEMA = os.environ['MEMORY_SCHEMA']
if not re.fullmatch(r'choms_memory_e2e_[a-f0-9]{12}', SCHEMA):
    raise RuntimeError('invalid_isolation_schema')
ROOT = Path(os.environ['SYSTEM_ROOT_DIRECTORY']) / 'databases'
ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
ROOT.chmod(0o700)
TOKEN = Path('/auth/access').read_text().strip()
if len(TOKEN) < 32:
    raise RuntimeError('invalid_authentication_configuration')
PROJECT = 'choms-memory-e2e-test'
CACHE = {}
LOCK = threading.RLock()
EMBED = TextEmbedding(model_name='BAAI/bge-small-en-v1.5', threads=1,
                      specific_model_path=os.environ['MEMORY_EMBEDDING_PATH'],
                      local_files_only=True)


def connect():
    c = psycopg2.connect(host=os.environ['DB_HOST'], port=5432,
                         dbname=os.environ['DB_NAME'], user=os.environ['DB_USERNAME'],
                         password=os.environ['DB_PASSWORD'], connect_timeout=10)
    c.autocommit = True
    return c


@contextmanager
def session():
    # Session lock spans the durable purge_pending commit and external cleanup.
    with LOCK:
        conn = connect()
        try:
            with conn.cursor() as c:
                c.execute('SELECT pg_advisory_lock(hashtext(%s))', (SCHEMA,))
                try:
                    yield c
                finally:
                    c.execute('SELECT pg_advisory_unlock(hashtext(%s))', (SCHEMA,))
        finally:
            conn.close()


def table(name):
    return sql.Identifier(SCHEMA, name)


def initialize():
    if importlib.metadata.version('cognee') != '1.6.5' or ladybug.Database.get_version() != '0.19.0':
        raise RuntimeError('installed_version_mismatch')
    with session() as c:
        c.execute(sql.SQL('CREATE TABLE IF NOT EXISTS {} (id uuid PRIMARY KEY, body jsonb, '
                          'state text NOT NULL, revision int NOT NULL, owner_id uuid NOT NULL, '
                          'vector_info jsonb NOT NULL, content_hash text)').format(table('registry')))
        c.execute(sql.SQL('CREATE TABLE IF NOT EXISTS {} (id uuid PRIMARY KEY, state text NOT NULL '
                          "CHECK (state='forgotten'))").format(table('tombstones')))
        c.execute(sql.SQL('SELECT id FROM {} WHERE state=%s').format(table('registry')), ('purge_pending',))
        pending = [str(r[0]) for r in c.fetchall()]
    for memory_id in pending:
        forget(memory_id)


def embedding(text):
    return '[' + ','.join(str(float(x)) for x in next(iter(EMBED.embed([text])))) + ']'


def descriptor(row):
    memory_id, body, state, revision, owner_id, info, _ = row
    return SimpleNamespace(owner_id=owner_id, graph_database_name=str(memory_id)+'.pkl',
                           vector_database_provider='pgvector', vector_database_url='',
                           vector_database_name=os.environ['DB_NAME'], vector_database_key='',
                           vector_database_connection_info=info,
                           vector_dataset_database_handler='pgvector_shared')


def fetch(c, memory_id):
    memory_id = str(uuid.UUID(memory_id))
    c.execute(sql.SQL('SELECT * FROM {} WHERE id=%s').format(table('registry')), (memory_id,))
    return c.fetchone()


def remember(text, *, candidate=False):
    # Gate deliberately only admits fixed synthetic fixture content; no user data.
    if text not in {'Synthetic violet satellite continuity requirement',
                    'Synthetic violet satellite replacement requirement'}:
        raise ValueError('synthetic_fixture_only')
    digest = hashlib.sha256(text.casefold().encode()).hexdigest()
    with session() as c:
        c.execute(sql.SQL('SELECT id FROM {} WHERE content_hash=%s').format(table('registry')), (digest,))
        if c.fetchone():
            raise ValueError('duplicate')
        memory_id, owner = uuid.uuid4(), uuid.uuid4()
        info = asyncio.run(VectorHandler.create_dataset(memory_id, None))['vector_database_connection_info']
        directory = ROOT / str(owner)
        directory.mkdir(mode=0o700)
        path = directory / (str(memory_id)+'.pkl')
        db = ladybug.Database(path, buffer_pool_size=67108864, max_num_threads=1)
        connection = ladybug.Connection(db)
        try:
            connection.execute('CREATE NODE TABLE Memory(id STRING, summary STRING, PRIMARY KEY(id))').close()
            connection.execute('CREATE (m:Memory {id: $id, summary: $summary})',
                               {'id':str(memory_id), 'summary':text}).close()
        finally:
            connection.close()
            db.close()
        c.execute(sql.SQL('CREATE TABLE {} (id uuid PRIMARY KEY, embedding public.vector(384))').format(
            sql.Identifier(info['schema'], 'embeddings')))
        c.execute(sql.SQL('INSERT INTO {} VALUES (%s,%s::public.vector)').format(
            sql.Identifier(info['schema'], 'embeddings')), (str(memory_id), embedding(text)))
        state = 'candidate' if candidate else 'active'
        body = {'id':str(memory_id), 'summary':text, 'project_id':PROJECT,
                'scope':'project', 'source_kind':'synthetic', 'source_reference':'fixture:purge-e2e'}
        c.execute(sql.SQL('INSERT INTO {} VALUES (%s,%s,%s,1,%s,%s,%s)').format(table('registry')),
                  (str(memory_id), json.dumps(body), state, str(owner), json.dumps(info), digest))
        CACHE[str(memory_id)] = dict(body)
        return {'id':str(memory_id), 'state':state, 'revision':1}


def review(memory_id):
    with session() as c:
        row = fetch(c, memory_id)
        if not row or row[2] != 'active':
            return None
        return {**row[1], 'revision':row[3]}


def search(text):
    if text != 'violet satellite':
        raise ValueError('synthetic_query_only')
    vector = embedding(text)
    results = []
    with session() as c:
        c.execute(sql.SQL("SELECT * FROM {} WHERE state='active'").format(table('registry')))
        for row in c.fetchall():
            c.execute(sql.SQL('SELECT id FROM {} ORDER BY embedding <=> %s::public.vector LIMIT 1').format(
                sql.Identifier(row[5]['schema'], 'embeddings')), (vector,))
            if c.fetchone():
                results.append(row[1])
    return results[:5]


def forget(memory_id):
    with session() as c:
        row = fetch(c, memory_id)
        if not row:
            c.execute(sql.SQL('SELECT state FROM {} WHERE id=%s').format(table('tombstones')), (memory_id,))
            if not c.fetchone():
                raise ValueError('not_found')
            return {'state':'forgotten'}
        entry = RegistryEntry(str(row[4]), str(row[0]), True)
        # Commit content erasure and reconciliation state BEFORE external effects.
        c.execute(sql.SQL("UPDATE {} SET body=NULL, content_hash=NULL, state='purge_pending' WHERE id=%s").format(
            table('registry')), (memory_id,))
        item = descriptor(row)
        async def official():
            directory = ROOT / entry.owner_id
            # Installed official handler calls remove_all when main is absent.
            # FileStorage local remove_all handles missing paths idempotently.
            await GraphHandler.delete_dataset(item)
        try:
            asyncio.run(purge(ROOT, entry, official))
            asyncio.run(VectorHandler.delete_dataset(item))
            CACHE.pop(memory_id, None)
            c.execute('SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s)',
                      (item.vector_database_connection_info['schema'],))
            if c.fetchone()[0] or any((ROOT/entry.owner_id/n).exists() for n in entry.names()) or memory_id in CACHE:
                raise RuntimeError('postcondition_incomplete')
            with c.connection:
                c.execute(sql.SQL("INSERT INTO {} VALUES (%s,'forgotten') ON CONFLICT DO NOTHING").format(
                    table('tombstones')), (memory_id,))
                c.execute(sql.SQL('DELETE FROM {} WHERE id=%s').format(table('registry')), (memory_id,))
            return {'state':'forgotten'}
        except Exception:
            # Never leak backend exception messages/content. Reconciliation metadata
            # contains only opaque internal IDs and schema, never retained content.
            return {'state':'purge_pending', 'error':'purge_incomplete'}


def projection_stats(memory_id):
    with session() as c:
        row = fetch(c, memory_id)
        if not row:
            return {'nodes':0, 'embeddings':0}
        c.execute(sql.SQL('SELECT count(*) FROM {}').format(
            sql.Identifier(row[5]['schema'], 'embeddings')))
        vectors = c.fetchone()[0]
        db = ladybug.Database(ROOT / str(row[4]) / (str(row[0])+'.pkl'),
                              buffer_pool_size=67108864, max_num_threads=1, read_only=True)
        connection = ladybug.Connection(db)
        result = connection.execute('MATCH (m:Memory) RETURN count(m)')
        nodes = result.get_next()[0]
        result.close()
        connection.close()
        db.close()
        return {'nodes':nodes, 'embeddings':vectors}


def reproduce_installed_handler():
    entry = RegistryEntry(str(uuid.uuid4()), str(uuid.uuid4()), True)
    directory = ROOT / entry.owner_id
    directory.mkdir(mode=0o700)
    for suffix in ('', '.wal', '.lock', '.shadow'):
        (directory / (entry.dataset_id+'.pkl'+suffix)).write_bytes(b'synthetic-companion')
    item = SimpleNamespace(owner_id=entry.owner_id, graph_database_name=entry.dataset_id+'.pkl')
    async def official():
        await GraphHandler.delete_dataset(item)
    asyncio.run(official())
    observed = sorted(p.suffix for p in directory.iterdir())
    if observed != ['.shadow']:
        raise RuntimeError('original_defect_not_reproduced')
    asyncio.run(purge(ROOT, entry, official))
    asyncio.run(purge(ROOT, entry, official))
    return {'official_left_shadow':True, 'wrapper_remaining':len(list(directory.iterdir())),
            'second_execution':'pass'}


def audit(memory_id):
    with session() as c:
        row = fetch(c, memory_id)
        c.execute(sql.SQL('SELECT count(*) FROM {} WHERE id=%s').format(table('tombstones')), (memory_id,))
        tombstones = c.fetchone()[0]
        c.execute('SELECT count(*) FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner '
                  'WHERE r.rolname=current_user AND n.nspname<>%s', (SCHEMA,))
        vector_schemas = c.fetchone()[0]
    files = [p for d in ROOT.iterdir() for p in d.iterdir()]
    return {'canonical_rows':int(row is not None), 'tombstones':tombstones,
            'graph_artifacts':len(files), 'cache_entries':len(CACHE),
            'vector_schemas':vector_schemas}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/ready':
            self.send_response(200)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer '+TOKEN):
            self.send_response(401)
            self.end_headers()
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('request_size')
            request = json.loads(self.rfile.read(length))
            operation, args = request['operation'], request.get('args', {})
            if operation == 'health':
                result = {'status':'ready', 'synthetic_only':True}
            elif operation == 'remember':
                result = remember(**args)
            elif operation == 'review':
                result = review(**args)
            elif operation == 'search':
                result = search(**args)
            elif operation == 'forget':
                result = forget(**args)
            elif operation == 'projection_stats':
                result = projection_stats(**args)
            elif operation == 'regression':
                result = reproduce_installed_handler()
            elif operation == 'audit':
                result = audit(**args)
            else:
                raise ValueError('unsupported_gate_operation')
            output = json.dumps({'result':result}).encode()
            self.send_response(200)
        except Exception as error:
            output = json.dumps({'error':'gate_operation_failed',
                'exception_class':type(error).__name__, 'errno':getattr(error,'errno',None),
                'sqlstate':getattr(error,'pgcode',None),
                'frames':[{'module':Path(f.filename).name,'line':f.lineno}
                          for f in traceback.extract_tb(error.__traceback__)[-6:]]}).encode()
            self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(output)


if __name__ == '__main__':
    initialize()
    HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
