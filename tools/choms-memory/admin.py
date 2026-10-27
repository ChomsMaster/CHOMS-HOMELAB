"""Explicit operator-only cleanup of already-forgotten SYNTHETIC acceptance IDs.

Not an MCP tool. Refuses real mode, surviving records/jobs/receipts or unknown IDs.
Never removes a file, schema, backup, PVC or Secret; only empty UUID directories
and content-free test tombstones. Production tombstones are retained.
"""
import argparse
import json
import os
import sys
from backend import Backend
from contract import identifier, Fault
from purge import open_trusted_root


def main():
    p=argparse.ArgumentParser();p.add_argument('--cleanup-forgotten-synthetic',action='store_true',required=True)
    p.parse_args()
    ids=json.load(sys.stdin)
    if not isinstance(ids,list) or not ids or len(ids)>100:raise Fault('invalid_fixture_ids')
    ids=list({identifier(v) for v in ids})
    b=Backend()
    if b.real or os.environ.get('MEMORY_ALLOW_REAL')!='false':raise Fault('real_mode_cleanup_forbidden')
    with b.session() as c:
        for table in ('records','receipts','purge_jobs'):
            c.execute('SELECT count(*) AS n FROM choms_memory.'+table)
            if c.fetchone()['n']:raise Fault('synthetic_cleanup_not_quiescent')
        c.execute('SELECT id FROM choms_memory.tombstones')
        stored={str(row['id']) for row in c.fetchall()}
        if stored!=set(ids):raise Fault('unknown_or_missing_tombstone')
        audit=[row for start in range(0,len(ids),20) for row in b._audit(c,ids[start:start+20])]
        if any(any(row[k] for k in ('canonical_rows','graph_artifacts','vector_schemas','cache_entries','content_receipts')) for row in audit):
            raise Fault('purge_not_complete')
        fd=open_trusted_root(b.root)
        try:
            for memory_id in stored:
                os.rmdir(memory_id,dir_fd=fd)  # Only empty private directories; never recursive deletion.
            os.fsync(fd)
        finally:os.close(fd)
        c.execute('DELETE FROM choms_memory.tombstones WHERE id=ANY(%s::uuid[])',(ids,))
        c.execute('SELECT count(*) AS n FROM choms_memory.tombstones')
        if c.fetchone()['n']:raise Fault('cleanup_incomplete')
    print(json.dumps({'synthetic_cleanup':'PASS','remaining_records':0,'remaining_receipts':0,'remaining_tombstones':0}))

if __name__=='__main__':main()
