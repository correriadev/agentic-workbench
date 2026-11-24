import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from init_suite import git, prepare


class SuiteLocation(unittest.TestCase):
    def bundle_command(self, bundle, suite):
        script = Path(__file__).resolve().parents[1] / "scripts/init_suite.py"
        return subprocess.run(
            [sys.executable, str(script), "--bundle", str(bundle), str(suite)],
            text=True, capture_output=True,
        )

    def test_bundle_mode_without_target_checkout_is_repeatable(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "handoff.json"
            payload = b'{"revision": "fixture", "records": []}\n'
            bundle.write_bytes(payload)
            suite = root / "suite"
            command = self.bundle_command(bundle, suite)
            self.assertEqual(command.returncode, 0, command.stderr)
            expected = {
                "bundle": str(bundle.resolve()),
                "bundle_sha256": hashlib.sha256(payload).hexdigest(),
                "suite": str(suite.resolve()),
            }
            self.assertEqual(json.loads(command.stdout), expected)
            self.assertEqual(json.loads(self.bundle_command(bundle, suite).stdout), expected)
            self.assertEqual(bundle.read_bytes(), payload)
            self.assertEqual([path.name for path in suite.iterdir()], [".git"])

    def test_bundle_mode_validates_input_and_worktree_before_creating_output(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "handoff.json"
            suite = root / "suite"
            for unavailable in (bundle, root):
                self.assertNotEqual(self.bundle_command(unavailable, suite).returncode, 0)
                self.assertFalse(suite.exists())

            bundle.write_text("fixture", encoding="utf-8")
            git(root, "init", "--quiet")
            command = self.bundle_command(bundle, suite)
            self.assertNotEqual(command.returncode, 0)
            self.assertIn("outside other working trees", command.stderr)
            self.assertFalse(suite.exists())

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
