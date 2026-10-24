"""All data and fault injection live solely in this temporary synthetic harness."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import unittest
import uuid
from unittest import mock

ROOT = Path(sys.argv.pop())
SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery_kit', SCRIPTS / 'recovery_kit.py')
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ephemeral = ROOT / 'ephemeral'
        subprocess.run(['age-keygen', '-o', str(cls.ephemeral)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.recipient = subprocess.check_output(['age-keygen', '-y', str(cls.ephemeral)],
                                               stderr=subprocess.DEVNULL).decode().strip()
        cls.key_bytes = cls.ephemeral.read_bytes()
        cls.ephemeral.unlink()

    def setUp(self):
        self.work = ROOT / uuid.uuid4().hex
        self.work.mkdir(mode=0o700)
        self.source = self.work / 'source'
        self.output = self.work / 'output'
        self.source.mkdir(mode=0o700)
        self.output.mkdir(mode=0o700)
        self.name = 'payload-' + uuid.uuid4().hex + '.bin'
        self.payload = self.source / self.name
        self.control = self.source / 'selection.json'
        self.data = b'synthetic-fixture\x00\n' * 20
        self.set_data(self.data)

    def set_data(self, data):
        self.data = data
        self.payload.write_bytes(data)
        self.payload.chmod(0o600)
        self.entry = {'file': self.name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        self.control.write_text(json.dumps({'version': 1, 'entries': [self.entry]}))
        self.control.chmod(0o600)

    def export(self, recipient=None):
        return kit.export(str(self.source), str(self.output), recipient or self.recipient)

    def reject(self, call=None):
        with self.assertRaises((kit.Rejected, OSError, ValueError, subprocess.SubprocessError)):
            (call or self.export)()
        self.assertEqual(list(self.output.iterdir()), [])

    def verify(self, target):
        fd = kit.directory(str(target))
        try:
            kit.validate_kit(fd, self.recipient)
        finally:
            os.close(fd)

    def test_valid_public_only_roundtrip_and_atomic(self):
        self.assertFalse(self.ephemeral.exists())
        original = kit.encrypt
        def observe(*args):
            self.assertTrue(all(p.name.startswith('.pending-') for p in self.output.iterdir()))
            return original(*args)
        with mock.patch.object(kit, 'encrypt', side_effect=observe):
            target = self.output / self.export()
        self.assertEqual(list(self.output.iterdir()), [target])
        self.assertRegex(target.name, r'^[a-f0-9]{32}$')
        self.verify(target)
        manifest = json.loads((target / 'manifest.sanitized.json').read_bytes())
        self.assertEqual(set(manifest), {'version', 'encryption', 'recipient_sha256', 'artifacts'})
        artifact = manifest['artifacts'][0]['file']
        self.assertRegex(artifact, r'^[a-f0-9]{32}\.age$')
        self.assertNotIn(self.name, (target / 'manifest.sanitized.json').read_text())
        self.assertNotIn(self.entry['sha256'], (target / 'manifest.sanitized.json').read_text())
        self.assertEqual(target.stat().st_mode & 0o777, 0o700)
        for path in target.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        # Decryption is a separate synthetic operation after export has completed.
        self.ephemeral.write_bytes(self.key_bytes)
        self.ephemeral.chmod(0o600)
        try:
            plain = subprocess.check_output(['age', '--decrypt', '-i', str(self.ephemeral),
                                             str(target / artifact)], stderr=subprocess.DEVNULL)
            self.assertEqual(plain, self.data)
        finally:
            self.ephemeral.unlink()

    def test_invalid_recipient(self):
        for value in ('invalid', self.recipient.upper(), self.recipient[:-1] + '!',
                      self.recipient[:-1] + ('q' if self.recipient[-1] != 'q' else 'p')):
            with self.subTest(value_type='synthetic-invalid'):
                self.reject(lambda: self.export(value))

    def test_missing_entry(self):
        self.payload.unlink()
        self.reject()

    def test_missing_selection(self):
        self.control.unlink()
        self.reject()

    def test_file_symlink(self):
        other = self.work / 'fixture'
        self.payload.rename(other)
        self.payload.symlink_to(other)
        self.reject()

    def test_directory_symlink(self):
        link = self.work / 'alias'
        link.symlink_to(self.source, target_is_directory=True)
        self.reject(lambda: kit.export(str(link), str(self.output), self.recipient))

    def test_hardlink(self):
        os.link(self.payload, self.work / 'hardlink')
        self.reject()

    def test_duplicate_and_ambiguous(self):
        self.control.write_text(json.dumps({'version': 1, 'entries': [self.entry, self.entry]}))
        self.reject()
        self.set_data(self.data)
        (self.source / 'extra').write_bytes(b'synthetic')
        self.reject()

    def test_duplicate_json_key(self):
        self.control.write_text('{"version":1,"version":1,"entries":[]}')
        self.reject()

    def test_invalid_selection_and_scope(self):
        for changed in ({'file': '../outside', 'size': 1, 'sha256': 'a' * 64},
                        dict(self.entry, size=True), dict(self.entry, sha256='b' * 64)):
            self.control.write_text(json.dumps({'version': 1, 'entries': [changed]}))
            self.reject()

    def test_permissions(self):
        for path, bad, good in [(self.payload, 0o640, 0o600), (self.control, 0o644, 0o600),
                                (self.source, 0o750, 0o700), (self.output, 0o755, 0o700)]:
            path.chmod(bad)
            self.reject()
            path.chmod(good)

    def test_change_during_read(self):
        self.set_data(b'synthetic' * 20000)
        original_encrypt, original_read = kit.encrypt, os.read
        changed = False
        def mutation(fd, size):
            nonlocal changed
            block = original_read(fd, size)
            if not changed:
                changed = True
                with self.payload.open('r+b') as stream:
                    stream.seek(100000)
                    stream.write(b'CHANGED')
            return block
        def instrument(*args):
            with mock.patch.object(kit.os, 'read', side_effect=mutation):
                return original_encrypt(*args)
        with mock.patch.object(kit, 'encrypt', side_effect=instrument):
            self.reject()
        self.assertTrue(changed)

    def test_replacement_after_read(self):
        original = kit.encrypt
        def replace(*args):
            original(*args)
            self.payload.unlink()
            self.payload.write_bytes(self.data)
            self.payload.chmod(0o600)
        with mock.patch.object(kit, 'encrypt', side_effect=replace):
            self.reject()

    def test_age_failure(self):
        original = subprocess.Popen
        def failing(_args, **kwargs):
            return original(['/bin/false'], **kwargs)
        with mock.patch.object(kit.subprocess, 'Popen', side_effect=failing):
            self.reject()

    def test_invalid_ciphertext(self):
        def bad_cipher(_fd, target, *_args):
            os.write(target, b'synthetic-invalid-ciphertext')
        with mock.patch.object(kit, 'encrypt', side_effect=bad_cipher):
            self.reject()

    def test_checksum_failure_prevents_publication(self):
        original = kit.validate_kit
        def corrupt(fd, recipient):
            target = os.open('checksums.sha256', os.O_WRONLY | os.O_TRUNC, dir_fd=fd)
            os.write(target, b'invalid\n')
            os.close(target)
            return original(fd, recipient)
        with mock.patch.object(kit, 'validate_kit', side_effect=corrupt):
            self.reject()

    def test_invalid_manifest_prevents_publication(self):
        original = kit.validate_kit
        def corrupt(fd, recipient):
            target = os.open('manifest.sanitized.json', os.O_WRONLY | os.O_TRUNC, dir_fd=fd)
            os.write(target, b'{}')
            os.close(target)
            return original(fd, recipient)
        with mock.patch.object(kit, 'validate_kit', side_effect=corrupt):
            self.reject()

    def test_verify_detects_tampering(self):
        target = self.output / self.export()
        cipher = next(target.glob('*.age'))
        with cipher.open('r+b') as stream:
            stream.seek(-1, 2)
            value = stream.read(1)
            stream.seek(-1, 2)
            stream.write(bytes([value[0] ^ 1]))
        with self.assertRaises(kit.Rejected):
            self.verify(target)

    def test_output_overlap(self):
        self.reject(lambda: kit.export(str(self.source), str(self.source), self.recipient))

    def test_optimized_python_still_rejects(self):
        self.payload.chmod(0o644)
        r = subprocess.run(['python3', '-I', '-O', '-B', str(SCRIPTS / 'recovery_kit.py'),
                            'export', '--recipient', self.recipient, '--input', str(self.source),
                            '--output', str(self.output)], capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertNotIn(self.recipient.encode(), r.stdout + r.stderr)

    def test_wrapper_cleanup_signals(self):
        self.set_data(b'synthetic-fixture' * (2 * 1024 * 1024))
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signal=sig):
                proc = subprocess.Popen(['bash', str(SCRIPTS / 'recovery-kit-export.sh'),
                                         '--recipient', self.recipient, '--input', str(self.source),
                                         '--output', str(self.output)], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, start_new_session=True)
                try:
                    deadline = time.monotonic() + 15
                    while not list(self.output.glob('.pending-*')):
                        self.assertIsNone(proc.poll(), 'export ended before signal injection')
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.001)
                    proc.send_signal(sig)
                    self.assertNotEqual(proc.wait(timeout=20), 0)
                    self.assertEqual(list(self.output.iterdir()), [])
                finally:
                    if proc.poll() is None:
                        proc.kill()
                        proc.wait()

    def test_no_runtime_overrides(self):
        # Export/verify expose no insecure flags. All injected faults above are mocks
        # confined to this harness; real entry points cannot disable validation.
        source = (SCRIPTS / 'recovery_kit.py').read_text()
        self.assertNotRegex(source, r'\bassert\b|os\.environ|--skip|--unsafe')
        r = subprocess.run(['python3', '-I', '-B', str(SCRIPTS / 'recovery_kit.py'),
                            'export', '--recipient', self.recipient, '--skip-validation'],
                           capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == '__main__':
    os.umask(0o077)
    unittest.main(verbosity=2)
