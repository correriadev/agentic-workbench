"""Exercise execution preflight on real files and published task contracts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "contract.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Preflight(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.folder = self.root / "docs/specs/verify"
        self.folder.mkdir(parents=True)
        self.scope = b"# Verify\n\nA1 Observe the result.\nR1 Missed failure.\n"
        (self.folder / "SCOPE.md").write_bytes(self.scope)
        (self.root / "tests").mkdir()
        (self.root / "tests/check_case.py").write_text("import unittest\n", encoding="utf-8")
        self.task = dict(
            id="T1", kind="implementation", project_path=str(self.root),
            status="pending", phase="red_pending", depends_on=[],
            files_allowed=["tests/check_case.py", "src/behavior.py"],
            unit_tests=dict(files=["tests/check_case.py"], command="python -m unittest tests.check_case"),
        )
        self.plan = dict(change_id=self.folder.name, scope_revision=sha(self.scope), tasks=[self.task])

    def cli(self, *args, payload=None, status=0):
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), str(self.folder), *args],
            input=json.dumps(payload) if payload is not None else None,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, status, result.stderr)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def test_preflight_is_read_only_and_reports_the_selected_paths(self):
        other = dict(self.task, id="T2", files_allowed=["tests/check_case.py", "../outside.py"])
        self.plan["tasks"].append(other)
        plan_path = self.folder / "tasks.json"
        data = json.dumps(self.plan).encode()
        plan_path.write_bytes(data)
        found = self.cli("preflight", "T1")
        self.assertEqual(found["task"], self.task)
        self.assertEqual(found["missing_paths"], ["src/behavior.py"])
        self.assertEqual(found["tasks_digest"], sha(data))
        self.assertIn("Invalid task write path", self.cli("preflight", "T2", status=1))
        self.assertEqual(plan_path.read_bytes(), data)
        self.assertEqual({item.name for item in self.folder.iterdir()}, {"tasks.json", "SCOPE.md"})

    def test_plan_rejects_ambiguous_or_escaping_write_paths(self):
        for path in ("../outside.py", "src/../../outside.py", "/outside.py", "C:\\outside.py", "src/*.py"):
            with self.subTest(path=path):
                self.task["files_allowed"][-1] = path
                self.assertIn("Invalid task write path",
                              self.cli("plan", "--expect", "absent", payload=self.plan, status=1))
                self.assertFalse((self.folder / "tasks.json").exists())

    def test_preflight_and_build_reject_a_link_added_after_planning(self):
        self.cli("plan", "--expect", "absent", payload=self.plan)
        plan_path = self.folder / "tasks.json"
        data = plan_path.read_bytes()
        outside = self.root / "other"
        outside.mkdir()
        try:
            (self.root / "src").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Cannot create directory links here: {error}")
        self.assertIn("traverses a symlink", self.cli("preflight", "T1", status=1))
        self.task["status"] = "in_progress"
        self.assertIn("traverses a symlink",
                      self.cli("build", "--expect", sha(data), payload=self.plan, status=1))
        self.assertEqual(plan_path.read_bytes(), data)

    def test_preflight_rejects_unmet_dependencies_and_changed_scope(self):
        self.plan["tasks"].append(dict(self.task, id="T2", depends_on=[dict(task="T1")]))
        self.cli("plan", "--expect", "absent", payload=self.plan)
        self.assertIn("dependencies are incomplete", self.cli("preflight", "T2", status=1))
        (self.folder / "SCOPE.md").write_bytes(self.scope + b"\nNew scope.\n")
        self.assertIn("Task plan revision mismatch", self.cli("preflight", "T1", status=1))

    def test_preflight_projects_only_mapped_obligations_and_unfinished_attempts(self):
        qa = dict(change_id=self.folder.name, scope_revision=sha(self.scope),
                  risk_coverage=[dict(risk_id="R1", obligation_ids=["QA-1", "QA-2"])],
                  obligations=[dict(id=key, acceptance_ids=["A1"], risk_ids=["R1"], status="ready", blocking=True)
                               for key in ("QA-1", "QA-2")])
        (self.folder / "qa.json").write_text(json.dumps(dict(contract=qa)), encoding="utf-8")
        revision = sha(json.dumps(qa, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode())
        unfinished = dict(id="open", event="started", task_id="T1", operation_key="fixture")
        self.task["qa_ids"] = ["QA-1"]
        self.plan.update(qa_revision=revision, evidence=[
            unfinished, dict(id="other", event="started", task_id="T2"),
            dict(id="closed", event="started", task_id="T1"),
            dict(id="result", event="result", attempt_id="closed"),
        ])
        (self.folder / "tasks.json").write_text(json.dumps(self.plan), encoding="utf-8")
        found = self.cli("preflight", "T1")
        self.assertEqual(found["qa_obligations"], [qa["obligations"][0]])
        self.assertEqual(found["unfinished_attempts"], [unfinished])


if __name__ == "__main__":
    unittest.main()
