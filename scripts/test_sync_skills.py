import pathlib
import contextlib
import shutil
import uuid
import unittest

import sync_skills


@contextlib.contextmanager
def temporary_directory():
    # Default mkdir permissions remain accessible inside Windows managed sandboxes.
    root = sync_skills.ROOT_DIR / ("sync-test-" + uuid.uuid4().hex)
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root)


class SyncSkillsTests(unittest.TestCase):
    def test_discovery(self):
        self.assertIn("ask-claude", sync_skills.get_available_skills())

    def test_render_and_dry_run_for_every_provider(self):
        with temporary_directory() as root:
            root = pathlib.Path(root)
            source = root / "source"
            source.mkdir()
            original = b"before\r\n" + sync_skills.POLICY_TOKEN * 2 + b"\r\nafter"
            (source / "SKILL.md").write_bytes(original)
            (source / "asset.bin").write_bytes(b"\x00\xff\x80")
            for target, policy in sync_skills.PROVIDER_POLICIES.items():
                destination = root / target
                plan = sync_skills.sync_single_skill(source, destination, True, target)
                self.assertIn(policy, plan)
                self.assertFalse(destination.exists())
                sync_skills.sync_single_skill(source, destination, target_name=target)
                self.assertEqual((destination / "SKILL.md").read_bytes(),
                                 original.replace(sync_skills.POLICY_TOKEN, policy.encode()))
                self.assertEqual((destination / "asset.bin").read_bytes(), b"\x00\xff\x80")
                (destination / "stale").touch()
                before = (destination / "SKILL.md").read_bytes()
                sync_skills.sync_single_skill(source, destination, True, target)
                self.assertEqual((destination / "SKILL.md").read_bytes(), before)
                self.assertTrue((destination / "stale").exists())
                sync_skills.sync_single_skill(source, destination, target_name=target)
                self.assertFalse((destination / "stale").exists())
            self.assertEqual((source / "SKILL.md").read_bytes(), original)

    def test_unknown_provider_fails_before_mutation(self):
        with temporary_directory() as root:
            source = pathlib.Path(root) / "source"
            source.mkdir()
            (source / "SKILL.md").write_bytes(sync_skills.POLICY_TOKEN)
            destination = pathlib.Path(root) / "destination"
            with self.assertRaises(ValueError):
                sync_skills.sync_single_skill(source, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
