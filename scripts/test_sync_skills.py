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
    def test_mapper_policy_renders_for_all_targets_without_changing_source(self):
        with temporary_directory() as root:
            source = pathlib.Path(root) / 'source'
            source.mkdir()
            token = b'{{PROJECT_MAPPER_SEMANTIC_WORKER_POLICY}}'
            (source / 'SKILL.md').write_bytes(token)
            expected = {'antigravity': b'flash', 'codex': b'gpt-6-luna',
                        'claude': b'haiku-5.5', 'opencode': b'haiku-5.5'}
            for target, model in expected.items():
                dest = pathlib.Path(root) / target
                sync_skills.sync_single_skill(source, dest, target_name=target)
                rendered = (dest / 'SKILL.md').read_bytes()
                self.assertIn(model, rendered)
                self.assertNotIn(token, rendered)
                self.assertIn(b'semantic', rendered.lower())
            self.assertEqual((source / 'SKILL.md').read_bytes(), token)

    def test_unknown_target_with_mapper_policy_fails_before_mutation(self):
        with temporary_directory() as root:
            source = pathlib.Path(root) / 'source'
            source.mkdir()
            (source / 'SKILL.md').write_bytes(b'{{PROJECT_MAPPER_SEMANTIC_WORKER_POLICY}}')
            dest = pathlib.Path(root) / 'dest'
            with self.assertRaises(ValueError):
                sync_skills.sync_single_skill(source, dest, target_name='unknown')
            self.assertFalse(dest.exists())

    def test_both_provider_policies_render_in_the_same_file(self):
        with temporary_directory() as root:
            source = pathlib.Path(root) / 'source'
            source.mkdir()
            (source / 'SKILL.md').write_bytes(sync_skills.FAST_CODE_POLICY_TOKEN + b'\n' +
                                               sync_skills.SEMANTIC_WORKER_POLICY_TOKEN)
            dest = pathlib.Path(root) / 'dest'
            sync_skills.sync_single_skill(source, dest, target_name='codex')
            content = (dest / 'SKILL.md').read_bytes()
            self.assertNotIn(sync_skills.FAST_CODE_POLICY_TOKEN, content)
            self.assertNotIn(sync_skills.SEMANTIC_WORKER_POLICY_TOKEN, content)
            self.assertIn(b'builder', content)
            self.assertIn(b'semantic investigation', content)

    def test_actual_mapper_documents_direct_use_and_precedence(self):
        content = (sync_skills.REPO_SKILLS / 'project-mapper' / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('User instructions and host capabilities take precedence', content)
        self.assertIn('canonical skill directly', content)
        self.assertIn('report the requested and actual configuration', content)
        self.assertIn(sync_skills.SEMANTIC_WORKER_POLICY_TOKEN.decode(), content)

    def test_discovery(self):
        self.assertIn("ask-claude", sync_skills.get_available_skills())

    def test_render_and_dry_run_for_every_provider(self):
        with temporary_directory() as root:
            root = pathlib.Path(root)
            source = root / "source"
            source.mkdir()
            original = b"before\r\n" + sync_skills.FAST_CODE_POLICY_TOKEN * 2 + b"\r\nafter"
            (source / "SKILL.md").write_bytes(original)
            (source / "asset.bin").write_bytes(b"\x00\xff\x80")
            for target, policy in sync_skills.FAST_CODE_PROVIDER_POLICIES.items():
                destination = root / target
                plan = sync_skills.sync_single_skill(source, destination, True, target)
                self.assertIn(target, plan)
                self.assertFalse(destination.exists())
                sync_skills.sync_single_skill(source, destination, target_name=target)
                self.assertEqual((destination / "SKILL.md").read_bytes(),
                                 original.replace(sync_skills.FAST_CODE_POLICY_TOKEN, policy.encode()))
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
            (source / "SKILL.md").write_bytes(sync_skills.FAST_CODE_POLICY_TOKEN)
            destination = pathlib.Path(root) / "destination"
            with self.assertRaises(ValueError):
                sync_skills.sync_single_skill(source, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
