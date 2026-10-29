"""Runtime integrity, archive safety and transactional promotion failure paths."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile

SOURCE=Path(__file__).resolve().parents[1]/'skills/runtime.py'
spec=importlib.util.spec_from_file_location('skills_runtime',SOURCE)
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='choms-runtime-test-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.runtime=r.Runtime(self.root/'managed')

    def release(self,revision=1,accepted=True):
        raw=json.dumps({'revision':revision}).encode();ident=hashlib.sha256(raw).hexdigest()[:32]
        path=self.runtime.release(ident);path.mkdir();(path/'LOCK.json').write_bytes(raw)
        (path/'tool').write_text('synthetic executable fixture');(path/'tool').chmod(0o755)
        r.write_json(path/'MANIFEST.json',r.manifest(path))
        r.write_json(self.runtime.root/'seals'/f'{ident}.json',{'manifest_sha256':r.digest(path/'MANIFEST.json'),'lock_sha256':hashlib.sha256(raw).hexdigest()})
        if accepted:r.write_json(self.runtime.root/'receipts'/f'{ident}.json',{'status':'PASS','manifest_sha256':r.digest(path/'MANIFEST.json')})
        return ident,path

    def test_content_tamper_rejected(self):
        ident,path=self.release();(path/'tool').write_text('tamper')
        with self.assertRaises(ValueError):self.runtime.verify(ident)

    def test_unlisted_file_rejected(self):
        ident,path=self.release();(path/'extra').write_text('unlisted')
        with self.assertRaises(ValueError):self.runtime.verify(ident)

    def test_execute_permission_change_rejected(self):
        ident,path=self.release();(path/'tool').chmod(0o644)
        with self.assertRaises(ValueError):self.runtime.verify(ident)

    def test_manifest_rewrite_rejected_by_seal(self):
        ident,path=self.release();(path/'tool').write_text('tamper');r.write_json(path/'MANIFEST.json',r.manifest(path))
        with self.assertRaisesRegex(ValueError,'seal'):self.runtime.verify(ident)

    def test_external_link_rejected(self):
        ident,path=self.release();(path/'outside').symlink_to(self.root/'outside')
        with self.assertRaisesRegex(ValueError,'external_symlink'):self.runtime.verify(ident)

    def test_archive_traversal_rejected(self):
        archive=self.root/'unsafe.zip'
        with zipfile.ZipFile(archive,'w') as out:out.writestr('../escaped','synthetic')
        with self.assertRaises(ValueError):self.runtime.unpack(archive,self.root/'unpack','zip')
        self.assertFalse((self.root/'escaped').exists())

    def test_offline_missing_and_corrupt_cache_fail_closed(self):
        sha=hashlib.sha256(b'valid').hexdigest()
        with self.assertRaisesRegex(ValueError,'offline_artifact_missing'):
            self.runtime.fetch('https://example.invalid/artifact',sha,'sha256',True)
        (self.runtime.root/'downloads'/sha).write_text('corrupt')
        with self.assertRaisesRegex(ValueError,'corrupt_cached_artifact'):
            self.runtime.fetch('https://example.invalid/artifact',sha,'sha256',True)

    def test_untested_release_does_not_replace_current(self):
        first,_=self.release();self.runtime.activate(first);second,_=self.release(2,accepted=False)
        with self.assertRaises(FileNotFoundError):self.runtime.activate(second)
        self.assertEqual(self.runtime.current(),first)

    def test_incomplete_retest_invalidates_previous_acceptance(self):
        ident,_=self.release()
        with self.assertRaises(KeyError):self.runtime.test(ident)
        with self.assertRaisesRegex(ValueError,'acceptance_receipt_required'):self.runtime.activate(ident)

    def test_promotion_and_rollback(self):
        first,_=self.release();second,_=self.release(2)
        self.runtime.activate(first);self.runtime.activate(second)
        self.assertEqual(self.runtime.current('previous'),first)
        self.runtime.activate(self.runtime.current('previous'))
        self.assertEqual(self.runtime.current(),first);self.assertEqual(self.runtime.current('previous'),second)

    def test_launcher_collision_preserves_both_pointers(self):
        first,_=self.release();second,_=self.release(2);third,_=self.release(3)
        self.runtime.activate(first);self.runtime.activate(second)
        launcher=self.runtime.root/'bin/choms-runtime';launcher.unlink();launcher.write_text('preexisting')
        with self.assertRaisesRegex(ValueError,'collision'):self.runtime.activate(third)
        self.assertEqual(self.runtime.current(),second);self.assertEqual(self.runtime.current('previous'),first)

if __name__=='__main__':unittest.main()
