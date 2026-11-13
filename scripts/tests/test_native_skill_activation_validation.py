"""Native skill-root validation accepts immutable snapshots with exact content."""
from pathlib import Path
from unittest.mock import patch
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/skills'))
import verify_native_activation as validator


class InstalledSkillValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='choms-skill-source-test-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.source_store = self.home / '.local/share/choms-workstation/sources'
        self.canonical = ROOT / 'tools/choms-skills/skills/choms-memory-governance'
        self.relative = Path('tools/choms-skills/skills/choms-memory-governance')
        self.snapshot = (self.source_store / ('a' * 40) / self.relative)
        self.snapshot.parent.mkdir(parents=True)
        shutil.copytree(self.canonical, self.snapshot,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        self.link_root = Path(self.temp.name) / 'hermes-skills'
        self.link_root.mkdir()
        self.link = self.link_root / 'choms-memory-governance'
        self.link.symlink_to(self.snapshot, target_is_directory=True)

    def test_content_addressed_snapshot_with_exact_files_is_accepted(self):
        with patch.object(Path, 'home', return_value=self.home):
            self.assertEqual(validator._installed_target(
                self.link, 'choms-memory-governance', self.canonical), self.snapshot)

    def test_changed_snapshot_content_is_rejected(self):
        (self.snapshot / 'SKILL.md').write_text(
            (self.snapshot / 'SKILL.md').read_text() + '\nlocal drift\n')
        with patch.object(Path, 'home', return_value=self.home), self.assertRaisesRegex(
                AssertionError, 'native_link_content_mismatch'):
            validator._installed_target(self.link, 'choms-memory-governance', self.canonical)

    def test_internal_symlink_is_rejected(self):
        (self.snapshot / 'linked-skill.md').symlink_to(self.snapshot / 'SKILL.md')
        with self.assertRaisesRegex(AssertionError, 'skill_internal_symlink'):
            validator._skill_files(self.snapshot)


if __name__ == '__main__':
    unittest.main()
