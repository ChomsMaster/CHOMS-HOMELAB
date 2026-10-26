#!/usr/bin/env python3
"""New integrity-unit fixtures only: no database, model, live data, or root override."""
import hashlib
import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('verify_recovery',
                                             Path(__file__).with_name('verify_recovery.py'))
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class IntegrityTests(unittest.TestCase):
    def fixture(self):
        # Counts describe a manifest fixture; they are NOT evidence of a real restore.
        blobs = {name: ('artificial fixture ' + name).encode() for name in v.ARTIFACTS}
        document = {'schema': 'choms-cognee-recovery-v1',
                    'captured_at': '2026-10-25T00:00:00+00:00',
                    'source_commit': '0' * 40,
                    'counts': {'documents': 36, 'nodes': 2226, 'edges': 6040},
                    'artifacts': {name: {'bytes': len(data),
                                        'sha256': hashlib.sha256(data).hexdigest()}
                                  for name, data in blobs.items()}}
        raw = json.dumps(document).encode()
        return raw, hashlib.sha256(raw).hexdigest(), blobs

    def verify(self, raw, digest, blobs):
        return v.verify_streams(raw, digest, {k: io.BytesIO(x) for k, x in blobs.items()})

    def test_valid_artificial_members(self):
        self.verify(*self.fixture())

    def test_corruption_same_size(self):
        raw, digest, blobs = self.fixture()
        name = sorted(blobs)[0]
        blobs[name] = b'X' + blobs[name][1:]
        with self.assertRaisesRegex(v.VerificationError, 'checksum_mismatch'):
            self.verify(raw, digest, blobs)

    def test_missing_member(self):
        raw, digest, blobs = self.fixture()
        blobs.pop(sorted(blobs)[0])
        with self.assertRaisesRegex(v.VerificationError, 'missing_or_unexpected'):
            self.verify(raw, digest, blobs)

    def test_unexpected_member(self):
        raw, digest, blobs = self.fixture()
        blobs['unexpected.txt'] = b'artificial'
        with self.assertRaisesRegex(v.VerificationError, 'missing_or_unexpected'):
            self.verify(raw, digest, blobs)

    def test_truncated_member(self):
        raw, digest, blobs = self.fixture()
        name = sorted(blobs)[0]
        blobs[name] = blobs[name][:-1]
        with self.assertRaisesRegex(v.VerificationError, 'size_mismatch'):
            self.verify(raw, digest, blobs)

    def test_untrusted_manifest(self):
        raw, digest, blobs = self.fixture()
        with self.assertRaisesRegex(v.VerificationError, 'manifest_hash_mismatch'):
            self.verify(raw + b' ', digest, blobs)

    def test_unknown_manifest_field(self):
        raw, _, blobs = self.fixture()
        obj = json.loads(raw)
        obj['unapproved'] = 'artificial'
        raw = json.dumps(obj).encode()
        with self.assertRaisesRegex(v.VerificationError, 'manifest_fields'):
            self.verify(raw, hashlib.sha256(raw).hexdigest(), blobs)

    def test_cli_refuses_nonroot_before_opening_files(self):
        if os.geteuid() == 0:
            self.skipTest('requires normal operator identity')
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('verify_recovery.py')),
                                 '--directory', '/run/choms-cognee-restore.artificial',
                                 '--manifest-sha256', '0' * 64], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('reason=root_required', result.stdout)


if __name__ == '__main__':
    unittest.main()
