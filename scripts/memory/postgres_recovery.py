"""Pure restore contracts for the accepted isolated PostgreSQL recovery.

No embedded endpoints/credentials or orchestration. Callers must
validate snapshot membership, use isolated resources, and validate copied files.
"""
import hashlib
import json
import subprocess
import time
import os
from pathlib import Path
import re
import stat

class RecoveryError(Exception):
    pass

def require(ok, reason):
    if not ok:
        raise RecoveryError(reason)

def vector_restore_list(raw, require_comment=False):
    require(isinstance(raw, bytes) and len(raw) <= 1024 ** 2, 'toc_size_contract')
    text = raw.decode('utf-8', 'strict')
    kept = []
    ids = set()
    removed = []
    extensions = []
    entries = 0
    for line in text.splitlines(keepends=True):
        if not line.strip() or line.startswith(';'):
            kept.append(line)
            continue
        entry = re.fullmatch('(\\d+);\\s+\\d+\\s+\\d+\\s+([^\\r\\n]+)\\r?\\n?', line)
        require(entry is not None, 'invalid_toc_record')
        number = int(entry[1])
        require(number not in ids, 'duplicate_toc_id')
        ids.add(number)
        entries += 1
        item = entry[2].strip()
        if re.fullmatch('COMMENT\\s+-\\s+EXTENSION\\s+vector(?:\\s+(?:postgres|cognee))?', item):
            removed.append({'toc_id': number, 'kind': 'COMMENT', 'object': 'EXTENSION vector'})
            continue
        if re.fullmatch('EXTENSION\\s+-\\s+vector(?:\\s+(?:postgres|cognee))?', item):
            extensions.append(number)
        kept.append(line)
    require(entries > 0 and len(removed) <= 1 and (len(extensions) <= 1), 'toc_vector_contract')
    if require_comment:
        require(len(removed) == 1, 'relational_vector_comment_not_found')
    return (''.join(kept).encode(), {'entries': entries, 'omitted': removed, 'vector_extension_entries_retained': extensions})
VECTOR_OWNER_SQL = "\nWITH RECURSIVE members(classid,objid) AS (\n SELECT classid,objid FROM pg_depend WHERE refclassid='pg_extension'::regclass\n AND refobjid IN (SELECT oid FROM pg_extension WHERE extname='vector') AND deptype='e'\n UNION\n SELECT d.classid,d.objid FROM pg_depend d JOIN members m ON d.refclassid=m.classid AND d.refobjid=m.objid\n WHERE d.deptype IN ('i','a')\n), owned AS (\n SELECT 'pg_class'::regclass AS classid,c.oid,c.relowner AS owner FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace\n WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'\n UNION ALL\n SELECT 'pg_proc'::regclass,p.oid,p.proowner FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace\n WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'\n UNION ALL\n SELECT 'pg_type'::regclass,t.oid,t.typowner FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace\n WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'\n UNION ALL\n SELECT 'pg_namespace'::regclass,n.oid,n.nspowner FROM pg_namespace n\n WHERE n.nspname !~ '^pg_' AND n.nspname NOT IN ('information_schema','public')\n), checked AS (\n SELECT o.* FROM owned o WHERE NOT EXISTS (SELECT 1 FROM members m WHERE m.classid=o.classid AND m.objid=o.oid)\n)\nSELECT json_build_object('vector_version',(SELECT extversion FROM pg_extension WHERE extname='vector'),\n 'vector_owner',(SELECT pg_get_userbyid(extowner) FROM pg_extension WHERE extname='vector'),\n 'checked_objects',(SELECT count(*) FROM checked),\n 'wrong_owners',(SELECT count(*) FROM checked WHERE owner<>(SELECT oid FROM pg_roles WHERE rolname='cognee')));\n"

def verify_dump_file(path, expected_size, expected_sha256):
    """Verify a custom dump without loading its payload in memory.

    The operator separately enforces root ownership, tmpfs and 0700/0600.
    This pure helper also works with synthetic files under ordinary identities.
    """
    require(type(expected_size) is int and 0 < expected_size <= 64*1024**2, 'dump_size_contract')
    require(isinstance(expected_sha256,str) and re.fullmatch('[a-f0-9]{64}',expected_sha256), 'dump_hash_contract')
    path=Path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        before=os.fstat(f.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600,'dump_file_contract')
        fingerprint=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        require(f.read(5)==b'PGDMP','dump_format_not_custom')
        f.seek(0);size=0;h=hashlib.sha256()
        while block:=f.read(1024**2):
            size+=len(block);require(size<=expected_size,'dump_size_mismatch');h.update(block)
        require(size==expected_size and h.hexdigest()==expected_sha256,'dump_integrity_mismatch')
        require(fingerprint(before)==fingerprint(os.fstat(f.fileno()))==fingerprint(path.lstat()),'dump_changed')
    return {'bytes':size,'sha256':h.hexdigest()}

def restore_argv(database, dump_path, list_path):
    """A file-based command for an isolated target, never pg_restore stdin.

    The caller must pair each verified dump with its own database, verify the
    copied dump/list hashes, and pass these arguments as a list without a shell.
    """
    require(isinstance(database,str) and re.fullmatch('[A-Za-z0-9_-]{1,80}',database),'database_name_contract')
    for path in (dump_path,list_path):
        require(isinstance(path,str) and path.startswith('/tmp/') and '..' not in Path(path).parts and '\x00' not in path,'temporary_pod_file_contract')
    require(dump_path!=list_path,'distinct_restore_files_required')
    return ['pg_restore','-U','postgres','--no-owner','--no-privileges',
            '--exit-on-error','--role=cognee','--use-list',list_path,
            '--dbname',database,dump_path]

def verify_ownership(value):
    require(value['vector_version']=='0.8.2' and value['vector_owner']=='postgres','precreated_vector_contract')
    require(type(value['checked_objects']) is int and value['checked_objects']>0 and value['wrong_owners']==0,'restored_object_ownership')


def restore_sanitize_pg_line(raw):
    value = sanitize_pg_line(raw)
    if value['message'] != '<unclassified line redacted>':
        return value
    text = raw.decode('utf-8', 'replace').strip()
    forms = ['pg_restore: error: could not execute query: ERROR:\\s+(?:relation|schema|type|index|constraint|role|database|function|extension) "[^"\\r\\n]+" (?:already exists|does not exist)', 'pg_restore: error: could not execute query: ERROR:\\s+permission denied for (?:table|sequence|schema|relation|function) [^\\r\\n]+', 'pg_restore: error: could not execute query: ERROR:\\s+must be owner of (?:table|sequence|schema|relation|function|extension) [^\\r\\n]+']
    if re.fullmatch(forms[0], text):
        value['message'] = re.sub('"[^"\\r\\n]+"', '"<identifier>"', text)
    elif re.fullmatch(forms[1], text):
        value['message'] = re.sub('(permission denied for (?:table|sequence|schema|relation|function)) .+', '\\1 <identifier>', text)
    elif re.fullmatch(forms[2], text):
        value['message'] = re.sub('(must be owner of (?:table|sequence|schema|relation|function|extension)) .+', '\\1 <identifier>', text)
    return value

def sanitize_pg_line(raw):
    text = raw.decode('utf-8', 'replace').strip()
    digest_value = hashlib.sha256(raw).hexdigest()
    allowed = ['pg_restore: error: could not execute query: ERROR:\\s+must be owner of extension (?:vector|plpgsql|pgcrypto|"uuid-ossp")', 'pg_restore: error: could not execute query: ERROR:\\s+permission denied to create extension "(?:vector|plpgsql|pgcrypto|uuid-ossp)"', 'pg_restore: error: could not execute query: ERROR:\\s+extension "(?:vector|plpgsql|pgcrypto|uuid-ossp)" already exists', 'pg_restore: error: unsupported version \\([0-9.]+\\) in file header', 'pg_restore: error: input file does not appear to be a valid archive(?: \\(too short\\?\\))?', 'pg_restore: error: could not execute query: ERROR:\\s+role "(?:postgres|cognee)" does not exist', 'pg_restore: error: could not execute query: ERROR:\\s+must be superuser to create this extension', 'pg_restore: error: could not execute query: ERROR:\\s+permission denied for schema public', 'pg_restore: error: could not execute query: ERROR:\\s+schema "public" already exists', 'pg_restore: error: could not execute query: ERROR:\\s+must be owner of schema public', 'pg_restore: error: could not execute query: ERROR:\\s+permission denied to set role "cognee"', 'pg_restore \\(PostgreSQL\\) [0-9.]+(?: \\([a-zA-Z0-9.+~ -]+\\))?']
    if any((re.fullmatch(pattern, text) for pattern in allowed)):
        return {'message': text, 'sha256': digest_value}
    if text.startswith('Command was:'):
        return {'message': '<SQL command redacted>', 'sha256': digest_value}
    return {'message': '<unclassified line redacted>', 'sha256': digest_value}

def capture_restore_output(args, timeout=60, toc=False):
    import collections, selectors
    child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    sel = selectors.DefaultSelector()
    pending = {'stdout': bytearray(), 'stderr': bytearray()}
    result = {'exit_code': None, 'timeout': False, 'stdout': [], 'stderr': [], 'bytes': {'stdout': 0, 'stderr': 0}, 'toc': {'entries': 0, 'types': {}, 'versions': []}}
    tails = {k: collections.deque(maxlen=32) for k in pending}
    hashes = {k: hashlib.sha256() for k in pending}

    def line(role):
        raw = bytes(pending[role])
        pending[role].clear()
        if not raw:
            return
        if toc and role == 'stdout':
            text = raw.decode('utf-8', 'replace')
            version = re.fullmatch(';\\s+(Dumped from database version|Dumped by pg_dump version):?\\s+([0-9.]+)', text)
            if version:
                result['toc']['versions'].append({'kind': version[1], 'version': version[2]})
            if re.match('\\d+;\\s+\\d+\\s+\\d+\\s+', text):
                result['toc']['entries'] += 1
                kind = next((v for v in ('TABLE DATA', 'SEQUENCE SET', 'TABLE', 'SEQUENCE', 'EXTENSION', 'COMMENT', 'ACL', 'SCHEMA', 'INDEX', 'CONSTRAINT', 'FUNCTION', 'TYPE') if re.match('\\d+;\\s+\\d+\\s+\\d+\\s+' + v + '\\s', text)), 'other')
                result['toc']['types'][kind] = result['toc']['types'].get(kind, 0) + 1
            return
        tails[role].append(restore_sanitize_pg_line(raw))
    for stream, role in ((child.stdout, 'stdout'), (child.stderr, 'stderr')):
        os.set_blocking(stream.fileno(), False)
        sel.register(stream, selectors.EVENT_READ, role)
    deadline = time.monotonic() + timeout
    try:
        while sel.get_map():
            if time.monotonic() >= deadline:
                result['timeout'] = True
                child.kill()
                break
            for key, unused in sel.select(0.25):
                data = os.read(key.fd, 65536)
                role = key.data
                if not data:
                    sel.unregister(key.fileobj)
                    continue
                result['bytes'][role] += len(data)
                hashes[role].update(data)
                for i, part in enumerate(data.split(b'\n')):
                    pending[role].extend(part[:max(0, 4096 - len(pending[role]))])
                    if i < len(data.split(b'\n')) - 1:
                        line(role)
        child.wait(timeout=max(0.1, deadline - time.monotonic()) if not result['timeout'] else 10)
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        sel.close()
        for role in pending:
            line(role)
            result[role] = list(tails[role])
            result[role + '_sha256'] = hashes[role].hexdigest()
        child.stdout.close()
        child.stderr.close()
        result['exit_code'] = child.returncode
    return result
