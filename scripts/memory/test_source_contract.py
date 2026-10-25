#!/usr/bin/env python3
"""Synthetic admission/restore tests. No production data or model execution."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from source_contract import allowed_content, allowed_path

class SourceContractTests(unittest.TestCase):
    def test_public_sources(self):
        for path in ('README.md', 'docs/context/WORKLOG.md', 'stacks/kubernetes/omniroute/routes.yaml', 'scripts/example.py'):
            self.assertTrue(allowed_path(path))
    def test_private_paths(self):
        paths=('.git/config','.cache/result.json','node_modules/example.js','docs/archive/old.md',
               '.env','.env.local','fixture.env','terraform.tfstate','terraform.tfstate.backup',
               'kubeconfig.yaml','fixture.key','identity.pem','backup.tar','backups/sample.txt',
               'personal/note.md','private/note.md','transcripts/session.md','sessions/session.json',
               'movie.mp4','data.db','/tmp/example.py','../example.py')
        for path in paths:
            with self.subTest(path=path):self.assertFalse(allowed_path(path))
    def test_binary_and_invalid_text(self):
        for data in (b'\0fiction',b'\xff\xfe'):
            self.assertFalse(allowed_content(data))
    def test_synthetic_private_key(self):
        value=b'AGE-'+b'SECRET-KEY-'+b'A'*50
        self.assertFalse(allowed_content(value))
        self.assertFalse(allowed_content(b'-----BEGIN '+b'PRIVATE KEY-----\nsynthetic'))
    def test_synthetic_headers(self):
        for name in (b'Authorization',b'Cookie',b'Set-Cookie'):
            self.assertFalse(allowed_content(name+b': synthetic-only'))
    def test_synthetic_secret_documents(self):
        for value in (b'kind: Secret\nstringData:\n  fixture: synthetic-only\n',
                      b'kind: "Secret" # synthetic\n',
                      json.dumps({'kind':'Secret','data':{'fixture':'artificial'}}).encode(),
                      json.dumps({'kind':'List','items':[{'kind':'Secret','stringData':{}}]}).encode()):
            self.assertFalse(allowed_content(value))
    def test_state_and_credential_documents(self):
        self.assertFalse(allowed_content(json.dumps({'terraform_version':'fixture','serial':1,'lineage':'fiction'}).encode()))
        self.assertFalse(allowed_content(json.dumps({'access_token':'synthetic-only'}).encode()))
        self.assertFalse(allowed_content(b'client-key-data: synthetic-only'))
    def test_public_secret_reference_is_not_payload(self):
        self.assertTrue(allowed_content(b'kind: Deployment\nspec:\n  secretKeyRef:\n    name: runtime-reference\n'))
    def test_synthetic_sqlite_backup_restore_only(self):
        # Tests this mechanism on artificial rows, NOT Cognee/PG or a native CBM schema.
        with tempfile.TemporaryDirectory(prefix='choms-memory-restore-fixture-') as tmp:
            source=sqlite3.connect(':memory:')
            source.execute('create table fixture (id integer primary key, content text)')
            source.execute('insert into fixture values (1, ?)',('synthetic-only',));source.commit()
            backup=sqlite3.connect(Path(tmp)/'sample.db');source.backup(backup);backup.close()
            backup=sqlite3.connect(Path(tmp)/'sample.db');restored=sqlite3.connect(':memory:');backup.backup(restored)
            self.assertEqual(restored.execute('select * from fixture').fetchall(),[(1,'synthetic-only')])
            self.assertEqual(restored.execute('pragma integrity_check').fetchone()[0],'ok')
            backup.close();source.close();restored.close()

if __name__=='__main__':unittest.main()
