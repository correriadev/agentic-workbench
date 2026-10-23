import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("environment", pathlib.Path(__file__).resolve().parents[1] / "scripts/environment.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai env test ")
        self.home = pathlib.Path(self.temp.name)
        self.env = m.Environment(self.home, "windows-amd64")

    def tearDown(self):
        self.temp.cleanup()

    def test_plan_is_offline_and_read_only(self):
        with patch.object(m.urllib.request, "urlopen", side_effect=AssertionError("network")):
            files, missing = self.env.desired(["codex"])
            self.assertTrue(files)
            self.assertTrue(missing)
            self.env.assess(files)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_apply_twice_and_restore_existing_bytes(self):
        p = self.home / ".codex/AGENTS.md"
        p.parent.mkdir()
        p.write_bytes(b"personal\r\n")
        with m.exclusive(self.env.state):
            with self.assertRaisesRegex(ValueError, "preserved"):
                self.env.apply({p: b"new"})
            self.assertEqual(p.read_bytes(), b"personal\r\n")
            tx = self.env.apply({p: b"new"}, replace=True)
            self.assertIsNone(self.env.apply({p: b"new"}))
            self.env.rollback(tx)
            self.assertEqual(p.read_bytes(), b"personal\r\n")
            self.env.rollback(tx)

    def test_rollback_removes_only_created_files(self):
        p = self.home / "config/new.json"
        other = self.home / "other.txt"
        other.write_text("untouched")
        with m.exclusive(self.env.state):
            tx = self.env.apply({p: b"{}"})
            self.env.rollback(tx)
        self.assertFalse(p.exists())
        self.assertEqual(other.read_text(), "untouched")

    def test_rollback_preflights_post_install_edits(self):
        a, b = self.home / "a", self.home / "b"
        with m.exclusive(self.env.state):
            tx = self.env.apply({a: b"installed", b: b"installed"})
            a.write_bytes(b"human")
            with self.assertRaisesRegex(ValueError, "post-install edit"):
                self.env.rollback(tx)
            self.assertEqual(b.read_bytes(), b"installed")

    def test_rollback_rejects_corrupt_backup(self):
        p = self.home / "original"
        p.write_bytes(b"old")
        with m.exclusive(self.env.state):
            tx = self.env.apply({p: b"new"}, replace=True)
            (self.env.state / "transactions" / tx / "0").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "Backup checksum"):
                self.env.rollback(tx)
        self.assertEqual(p.read_bytes(), b"new")

    def test_failure_recovers_written_files(self):
        p, q = self.home / "a", self.home / "b"
        original = m.atomic
        def broken(path, data):
            if path == q:
                raise OSError("simulated full disk")
            original(path, data)
        with m.exclusive(self.env.state), patch.object(m, "atomic", side_effect=broken):
            with self.assertRaisesRegex(OSError, "full disk"):
                self.env.apply({p: b"a", q: b"b"})
        self.assertFalse(p.exists())
        self.assertFalse(q.exists())

    def test_paths_and_transaction_ids_cannot_escape(self):
        with self.assertRaises(ValueError):
            m.contained(self.home, self.home / "../escape")
        with self.assertRaises(ValueError):
            self.env.rollback("../../escape")

    def test_zip_slip_rejected_before_extraction(self):
        p = self.home / "bad.zip"
        with zipfile.ZipFile(p, "w") as archive:
            archive.writestr("../escape", "bad")
            archive.writestr("fine", "okay")
        with self.assertRaises(ValueError):
            m.unpack(p, self.home / "extract")
        self.assertFalse((self.home / "extract/fine").exists())

    def test_download_requires_correct_hash_and_https(self):
        spec = {"url": "https://nodejs.org/example", "algorithm": "sha256", "digest": "0" * 64}
        class Response(io.BytesIO):
            url = spec["url"]
        with patch.object(m.urllib.request, "urlopen", return_value=Response(b"corrupt")):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                m.download(spec, self.home / "artifact")
        self.assertFalse((self.home / "artifact").exists())
        spec["url"] = "http://nodejs.org/example"
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            m.download(spec, self.home / "artifact")

    def test_existing_hooks_preserved_and_conflict_reported(self):
        p = self.home / ".codex/hooks.json"
        p.parent.mkdir()
        original = {"hooks": {"SessionStart": [{"hooks": [{"command": "node old-caveman.js"}]}]}}
        p.write_bytes(m.dump(original))
        files, missing = self.env.desired(["codex"])
        rendered = json.loads(files[p])
        self.assertEqual(rendered["hooks"]["SessionStart"], original["hooks"]["SessionStart"])
        self.assertTrue(any("migration" in x for x in missing))

    def test_commented_jsonc_is_preserved(self):
        p = self.home / ".config/opencode/opencode.jsonc"
        p.parent.mkdir(parents=True)
        p.write_text('{ // personal comment\n"plugin": []}')
        with self.assertRaises(json.JSONDecodeError):
            self.env.desired(["opencode"])
        self.assertIn("personal comment", p.read_text())

    def test_operation_lock_excludes_concurrent_writer(self):
        with m.exclusive(self.env.state):
            with self.assertRaises(FileExistsError):
                with m.exclusive(self.env.state):
                    pass

    def test_platform_artifacts_and_space_paths(self):
        for system in ["windows-amd64", "darwin-amd64", "darwin-arm64", "linux-amd64", "linux-arm64"]:
            env = m.Environment(self.home, system)
            for name in ["node", "rtk", "antigravity", "codebase-memory-upstream"]:
                self.assertTrue(env.binary(name).is_relative_to(self.home))
        self.assertTrue(self.env.node_command(self.home / "with space.js").startswith('"'))

    def test_isolated_child_process_home_overrides_inherited_agent_paths(self):
        with patch.dict(m.os.environ, {"CODEX_HOME": "real-home", "OPENCODE_CONFIG": "real-config"}):
            env = self.env.process_env()
        self.assertEqual(env["CODEX_HOME"], str(self.home / ".codex"))
        self.assertNotIn("OPENCODE_CONFIG", env)
        self.assertEqual(env["XDG_CONFIG_HOME"], str(self.home / ".config"))

    def test_mcp_adapters_use_distinct_native_schemas(self):
        files, missing = self.env.desired(["codex", "antigravity", "opencode"], upstream_cbm=True)
        toml = m.tomllib.loads(files[self.home / ".codex/config.toml"].decode())
        agy = json.loads(files[self.home / ".gemini/config/mcp_config.json"])
        oc = json.loads(files[self.home / ".config/opencode/opencode.jsonc"])
        expected = str(self.env.binary("codebase-memory-upstream"))
        self.assertEqual(toml["mcp_servers"]["codebase-memory-mcp"]["command"], expected)
        self.assertEqual(agy["mcpServers"]["codebase-memory-mcp"]["args"], [])
        self.assertEqual(oc["mcp"]["codebase-memory-mcp"]["command"], [expected])

    def test_symlinked_managed_directory_rejected(self):
        original = self.home / "original"
        original.mkdir()
        link = self.home / "link"
        try:
            link.symlink_to(original, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable for this account")
        with self.assertRaisesRegex(ValueError, "Link/junction"):
            m.contained(self.home, link / "file")

    def test_existing_preferences_win_and_missing_preferences_render_before_tables(self):
        p = self.home / ".codex/config.toml"
        p.parent.mkdir()
        p.write_text('model = "my-model"\n[other]\nkey = "untouched"\n')
        files, _ = self.env.desired(["codex"], upstream_cbm=True)
        data = m.tomllib.loads(files[p].decode())
        self.assertEqual(data["model"], "my-model")
        self.assertEqual(data["other"]["key"], "untouched")
        self.assertIn("model_reasoning_effort", data)
        self.assertIn("codebase-memory-mcp", data["mcp_servers"])


if __name__ == "__main__":
    unittest.main()
