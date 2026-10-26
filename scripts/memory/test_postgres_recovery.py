"""Synthetic contracts only: no database, Kubernetes, Restic or real data."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('postgres_recovery', Path(__file__).with_name('postgres_recovery.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class RecoveryTests(unittest.TestCase):
    def test_only_vector_comment_omitted(self):
        raw = b'; synthetic\n1; 3079 20 EXTENSION - vector \n2; 0 0 COMMENT - EXTENSION vector \n3; 1 2 TABLE public fixture cognee\n4; 1 2 TABLE DATA public fixture cognee\n'
        filtered, report = r.vector_restore_list(raw, True)
        self.assertEqual(filtered, raw.replace(b'2; 0 0 COMMENT - EXTENSION vector \n', b''))
        self.assertEqual(report['omitted'][0]['toc_id'], 2)
        self.assertEqual(report['vector_extension_entries_retained'], [1])

    def test_other_comments_unchanged(self):
        raw = b'1; 0 0 COMMENT - EXTENSION pgcrypto\n2; 0 0 COMMENT public fixture cognee\n'
        self.assertEqual(r.vector_restore_list(raw)[0], raw)

    def test_vectors_without_comment_unchanged(self):
        raw = b'1; 1 2 TABLE public fixture cognee\n'
        self.assertEqual(r.vector_restore_list(raw)[0], raw)

    def test_required_comment_missing(self):
        with self.assertRaises(r.RecoveryError):
            r.vector_restore_list(b'1; 1 2 TABLE public fixture cognee\n', True)

    def test_duplicate_entry_rejected(self):
        with self.assertRaises(r.RecoveryError):
            r.vector_restore_list(b'1; 1 2 TABLE public a cognee\n1; 1 2 TABLE public b cognee\n')

    def test_duplicate_vector_comment_rejected(self):
        with self.assertRaises(r.RecoveryError):
            r.vector_restore_list(b'1; 0 0 COMMENT - EXTENSION vector\n2; 0 0 COMMENT - EXTENSION vector\n')

    def test_lookalike_extension_preserved(self):
        raw = b'1; 0 0 COMMENT - EXTENSION vector_extra\n'
        self.assertEqual(r.vector_restore_list(raw)[0], raw)

    def test_invalid_toc_rejected(self):
        with self.assertRaises(r.RecoveryError):
            r.vector_restore_list(b'not a TOC\n')

    def fixture(self, data=b'PGDMP artificial custom-header fixture'):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / 'fixture.dump'
        path.write_bytes(data)
        path.chmod(0o600)
        return path, data

    def test_valid_file(self):
        path, data = self.fixture()
        value = r.verify_dump_file(path, len(data), hashlib.sha256(data).hexdigest())
        self.assertEqual(value['bytes'], len(data))

    def test_corruption_rejected(self):
        path, data = self.fixture()
        with self.assertRaises(r.RecoveryError):
            r.verify_dump_file(path, len(data), '0' * 64)

    def test_truncation_rejected(self):
        path, data = self.fixture()
        with self.assertRaises(r.RecoveryError):
            r.verify_dump_file(path, len(data) + 1, hashlib.sha256(data).hexdigest())

    def test_invalid_format_rejected(self):
        path, data = self.fixture(b'not a dump, only artificial bytes')
        with self.assertRaises(r.RecoveryError):
            r.verify_dump_file(path, len(data), hashlib.sha256(data).hexdigest())

    def test_symlink_rejected(self):
        path, data = self.fixture()
        link = path.with_name('link'); link.symlink_to(path)
        with self.assertRaises(OSError):
            r.verify_dump_file(link, len(data), hashlib.sha256(data).hexdigest())

    def test_unsafe_permissions_rejected(self):
        path, data = self.fixture(); path.chmod(0o644)
        with self.assertRaises(r.RecoveryError):
            r.verify_dump_file(path, len(data), hashlib.sha256(data).hexdigest())

    def test_separate_databases_and_strict_role(self):
        relational = r.restore_argv('cognee', '/tmp/rel.dump', '/tmp/rel.list')
        vectors = r.restore_argv('synthetic-dataset', '/tmp/vec.dump', '/tmp/vec.list')
        self.assertEqual(relational[relational.index('--dbname') + 1], 'cognee')
        self.assertEqual(vectors[vectors.index('--dbname') + 1], 'synthetic-dataset')
        for args in (relational, vectors):
            self.assertIn('--exit-on-error', args)
            self.assertIn('--role=cognee', args)
            self.assertIn('--use-list', args)
            self.assertNotIn('-', args)
            self.assertNotIn('--clean', args)

    def test_path_traversal_rejected(self):
        with self.assertRaises(r.RecoveryError):
            r.restore_argv('cognee', '/tmp/../fixture', '/tmp/list')

    def test_ownership_and_version(self):
        r.verify_ownership({'vector_version':'0.8.2','vector_owner':'postgres','checked_objects':10,'wrong_owners':0})
        for bad in ({'vector_version':'0.8.1'}, {'vector_owner':'cognee'}, {'wrong_owners':1}):
            value={'vector_version':'0.8.2','vector_owner':'postgres','checked_objects':10,'wrong_owners':0}; value.update(bad)
            with self.assertRaises(r.RecoveryError): r.verify_ownership(value)

    def test_stderr_preserved_and_sanitized(self):
        code='import sys;sys.stderr.write("pg_restore: error: could not execute query: ERROR: must be owner of extension vector\\n");sys.exit(1)'
        result=r.capture_restore_output([sys.executable,'-I','-c',code],2)
        self.assertEqual(result['exit_code'],1)
        self.assertIn('must be owner of extension vector',result['stderr'][0]['message'])

    def test_sql_payload_redacted(self):
        value=r.restore_sanitize_pg_line(b'Command was: INSERT synthetic PRIVATE_FIXTURE')
        self.assertNotIn('PRIVATE_FIXTURE',str(value))

    def test_capture_timeout(self):
        result=r.capture_restore_output([sys.executable,'-I','-c','import time;time.sleep(2)'],.05)
        self.assertTrue(result['timeout']); self.assertEqual(result['exit_code'],-9)

if __name__ == '__main__':
    unittest.main()
