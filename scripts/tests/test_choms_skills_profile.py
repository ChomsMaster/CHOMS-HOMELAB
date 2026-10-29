"""Profile failure-path checks against disposable copies, never active skills."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('profile_validator',ROOT/'scripts/skills/validate_profile.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='choms-profile-test-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'profile';shutil.copytree(ROOT/'tools/choms-skills',self.root)

    def test_valid_profile(self):
        self.assertEqual(v.validate(self.root)['selected'],9)

    def test_module_tamper_rejected(self):
        p=next((self.root/'modules').glob('*/*/SKILL.md'));p.write_text(p.read_text()+'synthetic tamper')
        with self.assertRaises(AssertionError):v.validate(self.root)

    def test_duplicate_module_name_rejected(self):
        import json
        p=self.root/'PROFILE.json';profile=json.loads(p.read_text())
        profile['modular_profiles']['frontend']['name']='choms-design-system'
        p.write_text(json.dumps(profile))
        with self.assertRaises(AssertionError):v.validate(self.root)

    def test_modified_script_rejected(self):
        p=self.root/'skills/choms-memory-governance/scripts/governance.py';p.write_text(p.read_text()+'\n# synthetic tamper\n')
        with self.assertRaises(AssertionError):v.validate(self.root)

    def test_unhashed_file_rejected(self):
        (self.root/'synthetic-unlisted.txt').write_text('synthetic')
        with self.assertRaises(AssertionError):v.validate(self.root)

    def test_hash_symlink_rejected(self):
        p=self.root/'LICENSE';data=p.read_text();p.unlink();target=Path(self.temp.name)/'synthetic-license';target.write_text(data);p.symlink_to(target)
        with self.assertRaises(AssertionError):v.validate(self.root)

if __name__=='__main__':unittest.main()
