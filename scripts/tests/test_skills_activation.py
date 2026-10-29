"""Activation collision/rollback checks in disposable native roots."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/skills'))
import activate_native as activation


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='choms-link-test-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.roots=[self.root/'codex',self.root/'hermes'];self.receipt=self.root/'activation.json'

    def test_collision_fails_before_any_mutation(self):
        self.roots[1].mkdir();(self.roots[1]/'choms-video-social').write_text('synthetic existing file')
        with self.assertRaises(ValueError):activation.activate(self.roots,self.receipt)
        self.assertFalse(self.roots[0].exists());self.assertFalse(self.receipt.exists())

    def test_rollback_preserves_preexisting_correct_link(self):
        self.roots[0].mkdir();name,target=next(iter(activation.entries().items()))
        preserved=self.roots[0]/name;preserved.symlink_to(target,target_is_directory=True)
        self.assertEqual(activation.activate(self.roots,self.receipt)['created_links'],25)
        self.assertEqual(activation.rollback(self.receipt)['removed_links'],25)
        self.assertTrue(preserved.is_symlink())

    def test_changed_link_prevents_partial_rollback(self):
        activation.activate(self.roots,self.receipt)
        path=self.roots[1]/'choms-video-social';path.unlink();path.write_text('synthetic replacement')
        with self.assertRaises(ValueError):activation.rollback(self.receipt)
        self.assertTrue((self.roots[0]/'choms-video-social').is_symlink())

if __name__=='__main__':unittest.main()
