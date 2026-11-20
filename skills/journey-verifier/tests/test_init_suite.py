from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from init_suite import git, prepare


class SuiteLocation(unittest.TestCase):
    def test_create_resume_and_reject_nested_output(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            git(target, "init", "--quiet")
            git(target, "-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "--allow-empty", "-m", "fixture")
            suite = root / "suite"
            created = prepare(target, suite)
            self.assertEqual(created["source_revision"], git(target, "rev-parse", "HEAD").stdout.strip())
            self.assertFalse(created["source_dirty"])
            self.assertTrue((suite / ".git").is_dir())
            self.assertEqual(prepare(target, suite), created)
            with self.assertRaises(ValueError):
                prepare(target, target / "suite")
            self.assertFalse((target / "suite").exists())
