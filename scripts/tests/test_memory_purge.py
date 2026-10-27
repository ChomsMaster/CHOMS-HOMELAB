"""Synthetic filesystem regression tests; no network, Cognee data or credentials."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

MODULE = Path(__file__).resolve().parents[2] / 'tools/choms-memory/purge.py'
spec = importlib.util.spec_from_file_location('memory_purge', MODULE)
purge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = purge
spec.loader.exec_module(purge)


class PurgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='choms-purge-synthetic-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.entry = purge.RegistryEntry(str(uuid.uuid4()), str(uuid.uuid4()), True)
        self.directory = self.root / self.entry.owner_id
        self.directory.mkdir(mode=0o700)
        self.calls = 0

    def populate(self, suffixes=purge.SUFFIXES):
        for suffix in suffixes:
            (self.directory / (self.entry.dataset_id + '.pkl' + suffix)).write_bytes(b'synthetic')

    async def official(self):
        self.calls += 1
        # Exact relevant behavior of installed handler: shadow and other sidecars
        # are omitted. Actual installed-handler reproduction is a separate gate.
        for suffix in ('', '.lock', '.wal'):
            (self.directory / (self.entry.dataset_id + '.pkl' + suffix)).unlink(missing_ok=True)

    def run_purge(self, **kwargs):
        return asyncio.run(purge.purge(self.root, self.entry, self.official, **kwargs))

    def test_versioned_contract_matches_allowlist(self):
        lock = json.loads((MODULE.parent / 'purge-contract.json').read_text())
        self.assertEqual(lock['contract'], purge.CONTRACT)
        self.assertEqual(tuple(lock['suffixes']), purge.SUFFIXES)
        self.assertFalse(lock['physical_secure_erasure'])
        self.assertEqual((lock['cognee'], lock['ladybug']), ('1.6.5', '0.19.0'))

    def test_all_demonstrated_companions(self):
        self.populate()
        self.run_purge()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_each_companion_individually(self):
        for suffix in purge.SUFFIXES:
            with self.subTest(suffix=suffix):
                self.populate((suffix,))
                self.run_purge()
                self.assertEqual(list(self.directory.iterdir()), [])

    def test_directory_replacement_after_official(self):
        old = self.root / 'original'
        outside = self.root / 'outside'
        outside.mkdir(mode=0o700)
        (outside / 'sentinel').write_bytes(b'synthetic')
        async def replace():
            self.directory.rename(old)
            self.directory.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(purge.PurgePending):
            asyncio.run(purge.purge(self.root, self.entry, replace))
        self.assertEqual((outside / 'sentinel').read_bytes(), b'synthetic')

    def test_official_leaves_shadow_wrapper_removes(self):
        self.populate(('', '.wal', '.shadow', '.lock'))
        asyncio.run(self.official())
        self.assertEqual([p.suffix for p in self.directory.iterdir()], ['.shadow'])
        self.run_purge()
        self.run_purge()
        self.assertFalse(list(self.directory.iterdir()))

    def test_partial_absence(self):
        self.populate(('.shadow', '.wal.checkpoint'))
        self.run_purge()

    def test_empty_directory(self):
        self.run_purge()

    def test_missing_directory(self):
        self.directory.rmdir()
        self.run_purge()
        self.assertEqual(self.calls, 1)

    def test_absent_directory_callback_cannot_skip_postcondition(self):
        self.directory.rmdir()
        async def unexpected_creation():
            (self.directory / (self.entry.dataset_id + '.pkl.shadow')).touch()
        with self.assertRaises(purge.PurgePending):
            asyncio.run(purge.purge(self.root, self.entry, unexpected_creation))

    def test_interrupt_after_official_reconcile(self):
        self.populate()
        def interrupt(stage):
            if stage == 'after_official':
                raise InterruptedError
        with self.assertRaises(purge.PurgePending):
            self.run_purge(checkpoint=interrupt)
        self.assertTrue(list(self.directory.iterdir()))
        self.run_purge()
        self.assertFalse(list(self.directory.iterdir()))

    def test_interrupt_during_compensation_reconcile(self):
        self.populate()
        def interrupt(stage):
            if stage == 'after_unlink':
                raise InterruptedError
        with self.assertRaises(purge.PurgePending):
            self.run_purge(checkpoint=interrupt)
        self.run_purge()
        self.assertFalse(list(self.directory.iterdir()))

    def test_shadow_symlink_rejected_before_handler(self):
        self.populate(('',))
        target = self.root / 'outside'
        target.write_bytes(b'synthetic')
        (self.directory / (self.entry.dataset_id + '.pkl.shadow')).symlink_to(target)
        with self.assertRaises(purge.PurgePending):
            self.run_purge()
        self.assertEqual(self.calls, 0)
        self.assertEqual(target.read_bytes(), b'synthetic')

    def test_traversal(self):
        self.entry = purge.RegistryEntry('../escape', self.entry.dataset_id, True)
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_absolute_dataset(self):
        self.entry = purge.RegistryEntry(self.entry.owner_id, '/outside', True)
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_owner_symlink(self):
        self.directory.rmdir()
        self.directory.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_unexpected_file(self):
        (self.directory / 'unregistered').write_bytes(b'synthetic')
        with self.assertRaises(purge.PurgePending):
            self.run_purge()
        self.assertEqual(self.calls, 0)

    def test_subgraph_rejected(self):
        (self.directory / (self.entry.dataset_id + '.additional.pkl')).touch()
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_fifo(self):
        os.mkfifo(self.directory / (self.entry.dataset_id + '.pkl.shadow'))
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_hardlink(self):
        self.populate(('',))
        os.link(self.directory / (self.entry.dataset_id + '.pkl'), self.root / 'linked')
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_permission_failure(self):
        self.populate(('.shadow',))
        with patch.object(purge.os, 'unlink', side_effect=PermissionError):
            with self.assertRaises(purge.PurgePending):
                self.run_purge()
        self.assertTrue(list(self.directory.iterdir()))

    def test_shared_rejected(self):
        self.entry = purge.RegistryEntry(self.entry.owner_id, self.entry.dataset_id, False)
        with self.assertRaises(purge.PurgePending):
            self.run_purge()
        self.assertEqual(self.calls, 0)

    def test_root_symlink(self):
        link = self.root / 'linked_root'
        link.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(purge.PurgePending):
            asyncio.run(purge.purge(link, self.entry, self.official))

    def test_wrong_permissions(self):
        self.directory.chmod(0o755)
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_version_mismatch(self):
        self.entry = purge.RegistryEntry(self.entry.owner_id, self.entry.dataset_id, True, 'other')
        with self.assertRaises(purge.PurgePending):
            self.run_purge()

    def test_artifact_changed(self):
        self.populate(('.shadow',))
        async def mutate():
            (self.directory / (self.entry.dataset_id + '.pkl.shadow')).write_bytes(b'changed')
        with self.assertRaises(purge.PurgePending):
            asyncio.run(purge.purge(self.root, self.entry, mutate))

    def test_postcondition(self):
        self.populate(('.shadow',))
        def recreate(stage):
            if stage == 'after_unlink':
                (self.directory / 'unexpected').touch()
        with self.assertRaises(purge.PurgePending):
            self.run_purge(checkpoint=recreate)

    def test_official_failure_not_hidden(self):
        async def failure():
            raise RuntimeError('synthetic')
        with self.assertRaises(RuntimeError):
            asyncio.run(purge.purge(self.root, self.entry, failure))


if __name__ == '__main__':
    unittest.main()
