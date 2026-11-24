"""Offline CLI tests using a hypothetical scheduled boleto cancellation plan."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / "contract.py"
UNIT = "python -m unittest tests.test_cancel"
RACE = "python -m unittest tests.test_cancel_race"


def node(key, kind, content, state="planned", origin="inference", **details):
    return dict(id=key, kind=kind, title=key, content=content, state=state,
                origin=origin, details=details)


def edge(src, relation, dst):
    return dict(src=src, relation=relation, dst=dst,
                rationale=f"{src} {relation} {dst} in the hypothetical feature.")


def cancellation(root):
    runner = root / "tests" / "test_existing.py"
    runner.parent.mkdir()
    runner.write_text("import unittest\n", encoding="utf-8")
    return dict(
        request_id="initial-plan", reason="Model scheduled boleto cancellation",
        nodes=[
            node("I1", "intent", "Allow owners to cancel a scheduled boleto.", "confirmed", "human"),
            node("A1", "acceptance", "When cancellation wins the race, dispatch cannot occur."),
            node("B1", "behavior", "Cancel atomically before the scheduler claims the boleto.",
                 method_required=True),
            node("R1", "risk", "Cancellation and execution may race.", "applicable", "catalog"),
            node("M1", "method", "Atomically cancel a schedule if it has not been claimed."),
            node("API1", "api_contract", "POST /scheduled-boletos/{id}/cancel"),
            node("F1", "request_field", "Schedule ID is required in the path."),
            node("F2", "response_field", "Return the persisted cancellation state."),
            node("E1", "error_contract", "Reject missing ownership and already claimed schedules."),
            node("T1", "task", "Implement the compare-and-set cancellation path."),
            node("T2", "task", "Exercise the scheduler and cancellation interleaving."),
            node("S1", "test_scenario", "Test cancellation after a schedule is claimed."),
            node("S2", "test_scenario", "Cancellation wins while the worker is paused."),
            node("AS1", "assertion", "Repository rejects a claimed schedule.",
                 observables=["claim-conflict"]),
            node("AS2", "assertion", "API returns HTTP 200.", observables=["http-status"]),
            node("O-NO-DISPATCH", "verification_obligation",
                 "When cancellation wins, the worker cannot dispatch.",
                 observables=["http-status", "dispatch-count"], artifacts=["worker-event-log"]),
        ],
        sources=[dict(id="SRC1", project_root=str(root), path="tests/test_existing.py",
                      line_start=1, line_end=1, symbol="unittest",
                      sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
                      excerpt="import unittest")],
        node_sources=[dict(node_id="S1", source_id="SRC1")],
        edges=[edge(*link) for link in (
            ("A1", "requires", "B1"), ("B1", "requires", "M1"),
            ("B1", "requires", "API1"), ("B1", "verified_by", "S1"),
            ("R1", "threatens", "B1"), ("R1", "requires", "O-NO-DISPATCH"),
            ("O-NO-DISPATCH", "verified_by", "S2"),
            ("API1", "has_request", "F1"), ("API1", "has_response", "F2"),
            ("API1", "has_error", "E1"),
            ("T1", "implements", "A1"), ("T1", "implements", "B1"),
            ("T1", "implements", "M1"), ("T1", "verified_by", "S1"),
            ("T2", "depends_on", "T1"), ("T2", "requires", "O-NO-DISPATCH"),
            ("S1", "has_assertion", "AS1"), ("S2", "has_assertion", "AS2"),
        )],
        task_details=[
            dict(task_id="T1", project_root=str(root), kind="implementation", unit_command=UNIT,
                 runner_source="SRC1", red="Claimed schedule can be cancelled.",
                 green="Claimed schedule is rejected by the domain service."),
            dict(task_id="T2", project_root=str(root), kind="evidence"),
        ],
        task_files=[
            dict(task_id="T1", path="tests/test_cancel.py", origin="new", role="unit"),
            dict(task_id="T1", path="domain/cancel.py", origin="new", role="production"),
            dict(task_id="T2", path="tests/test_cancel_race.py", origin="new", role="support"),
        ],
        verification_cases=[
            dict(scenario_id="S1", level="unit", conditions="The schedule is claimed.",
                 steps="Call the domain method.", expected="Report a conflict.", command=UNIT),
            dict(scenario_id="S2", level="integration", conditions="Pause the worker before claim.",
                 steps="Cancel then release the worker.", expected="HTTP 200 and zero dispatches.",
                 command=RACE),
        ],
    )


class GraphTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.folder = self.root / "docs/specs/cancel-boleto"
        self.run_cli("init")
        self.plan = cancellation(self.root)

    def run_cli(self, *args, payload=None, status=0):
        result = subprocess.run([sys.executable, str(CLI), str(self.folder), *args],
                                input=json.dumps(payload) if payload is not None else None,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, status, result.stderr or result.stdout)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def apply(self, payload=None, expected=0, status=0):
        return self.run_cli("apply", "--expect", str(expected),
                            payload=self.plan if payload is None else payload, status=status)

    def update(self, expected=1, status=0, **changes):
        return self.apply(dict(request_id="update", reason="Reconcile observed plan gaps", **changes),
                          expected, status)

    def gap_codes(self):
        return {item["code"] for item in self.run_cli("gaps")["gaps"]}

    def test_source_ref_grounds_docs_before_init_without_a_graph(self):
        self.folder = self.folder.with_name("docs-fallback")
        target = self.root / "dependency"
        (target / "docs").mkdir(parents=True)
        (target / "docs/README.md").write_text("# Test policy\n\nUse the focused runner.\n", encoding="utf-8")
        record = self.run_cli("source-ref", "DOC1", "--project-root", str(target),
                              "--path", "docs/README.md", "--lines", "3", "3", "--excerpt")
        self.assertFalse(self.folder.exists())
        self.assertEqual(record["project_root"], str(target))
        self.assertEqual(record["excerpt"], "Use the focused runner.")
        self.assertNotIn("version", record)
        self.run_cli("init")
        self.apply(dict(request_id="documentation", reason="Ground the runner policy",
                        nodes=[node("C1", "constraint", "Use a focused runner.", "observed", "repository")],
                        sources=[record], node_sources=[dict(node_id="C1", source_id="DOC1")]))
        self.assertEqual(self.run_cli("get", "C1")["sources"][0]["sha256"], record["sha256"])

    def test_source_ref_hashes_and_reads_the_same_bytes_and_apply_rechecks(self):
        path = "tests/test_existing.py"
        file = self.root / path
        data = "# validação\r\nimport unittest\r\n".encode()
        file.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        for content_id in (f"sha256:{digest}", "git:" + hashlib.sha1(blob).hexdigest(),
                           "git:" + hashlib.sha256(blob).hexdigest()):
            with self.subTest(content_id=content_id):
                record = self.run_cli("source-ref", "SRC2", "--path", path, "--symbol", "unittest",
                                      "--lines", "1", "1", "--excerpt", "--expect-content-id", content_id)
                self.assertEqual(record["sha256"], digest)
                self.assertEqual(record["version"], content_id)
                self.assertEqual(record["symbol"], "unittest")
                self.assertEqual(record["excerpt"], "# validação")
        self.assertIn("line range", self.run_cli("source-ref", "SRC2", "--path", path,
                                                 "--lines", "1", "9", status=1))
        self.assertIn("project-relative path", self.run_cli("source-ref", "SRC2", "--path", "../source.py", status=1))
        file.write_bytes(data + b"# Changed after inspection.\r\n")
        self.assertIn("Source content changed", self.apply(
            dict(request_id="changed-source", reason="Record initial evidence", sources=[record]), status=1))
        self.assertEqual(self.run_cli("inspect")["revision"], 0)

    def test_artifacts_and_regeneration(self):
        self.apply()
        self.run_cli("render-scope")
        scope = self.folder / "SCOPE.md"
        canonical = scope.read_text()
        self.assertEqual({f.name for f in self.folder.iterdir()}, {"SCOPE.md", "context.sqlite"})
        self.assertIn("Database revision: 1", canonical)
        scope.write_text("Edited by hand")
        self.assertFalse(self.run_cli("inspect")["scope_current"])
        self.run_cli("render-scope")
        self.assertEqual(scope.read_text(), canonical)
        self.assertTrue(self.run_cli("inspect")["scope_current"])

    def test_scope_regeneration_is_independent_of_live_files(self):
        unit = self.root / "tests/test_cancel.py"
        unit.touch()
        self.plan["task_files"][0]["origin"] = "existing"
        self.apply()
        self.run_cli("render-scope")
        canonical = (self.folder / "SCOPE.md").read_bytes()
        unit.unlink()
        self.assertIn("ungrounded_task_path", self.gap_codes())
        self.run_cli("render-scope")
        self.assertEqual((self.folder / "SCOPE.md").read_bytes(), canonical)

    def test_full_nodes_and_source_survive_restart(self):
        self.apply()
        self.assertEqual(self.run_cli("init")["revision"], 1)
        scenario = self.run_cli("get", "S1")
        expected = next(item for item in self.plan["nodes"] if item["id"] == "S1")
        self.assertEqual(scenario["content"], expected["content"])
        self.assertEqual(scenario["sources"][0]["excerpt"], "import unittest")
        self.assertEqual(scenario["verification"][0]["conditions"], "The schedule is claimed.")
        self.assertTrue(all(link["rationale"] for link in scenario["edges"]))

    def test_trace_requirement_and_dependencies(self):
        self.apply()
        traced = self.run_cli("trace", "A1")
        self.assertTrue({"T1", "T2", "M1", "AS2", "O-NO-DISPATCH"} <=
                        {link["node"]["id"] for link in traced["links"]})
        self.assertTrue(self.run_cli("trace", "A1", "--limit", "1")["truncated"])

    def test_bad_id_orphan_and_cycle_roll_back(self):
        self.apply()
        self.assertIn("Invalid identifier", self.update(status=1, nodes=[
            node("bad id", "gap", "Invalid ID.")]))
        self.assertIn("FOREIGN KEY", self.update(status=1, edges=[
            edge("T1", "depends_on", "UNKNOWN")]))
        self.assertIn("cycle", self.update(status=1, edges=[
            edge("T1", "depends_on", "T2")]).lower())
        self.assertEqual(self.run_cli("inspect")["revision"], 1)

    def test_missing_unit_mapping_blocks_dependents(self):
        self.plan["task_details"][0].pop("unit_command")
        obligation = next(item for item in self.plan["nodes"] if item["id"] == "O-NO-DISPATCH")
        obligation["details"]["observables"] = ["http-status"]
        self.apply()
        report = self.run_cli("validate", status=1)
        self.assertEqual(report["blocked_tasks"], ["T1", "T2"])
        self.assertIn("invalid_unit_mapping", self.gap_codes())
        self.assertIn("blocked_dependency", self.gap_codes())

    def test_unplanned_acceptance(self):
        self.plan["nodes"].append(node("A2", "acceptance", "Record an audit event."))
        self.apply()
        self.assertIn(("A2", "missing_implementation"),
                      {(gap["node"], gap["code"]) for gap in self.run_cli("gaps")["gaps"]})

    def test_applicable_risk_without_obligation(self):
        self.plan["edges"].remove(edge("R1", "requires", "O-NO-DISPATCH"))
        self.apply()
        self.assertIn("uncovered_risk", self.gap_codes())
        self.assertEqual(self.run_cli("gaps")["blocked_tasks"], ["T1", "T2"])

    def test_evidence_task_needs_command_for_automated_scenario(self):
        self.plan["verification_cases"][1].pop("command")
        self.apply()
        report = self.run_cli("gaps")
        self.assertIn("missing_scenario_command", {item["code"] for item in report["gaps"]})
        self.assertEqual(report["blocked_tasks"], ["T2"])

    def test_incomplete_api(self):
        self.plan["edges"].remove(edge("T1", "implements", "B1"))
        self.plan["edges"].remove(edge("API1", "has_request", "F1"))
        self.plan["edges"].remove(edge("API1", "has_response", "F2"))
        self.apply()
        self.assertTrue({"api_missing_request", "api_missing_response"} <= self.gap_codes())
        self.assertEqual(self.run_cli("gaps")["blocked_tasks"], ["T1", "T2"])

    def test_requirement_revision_preserves_history_and_identifies_impact(self):
        self.apply()
        revised = node("A1", "acceptance", "When cancellation wins, no boleto dispatch is emitted.")
        self.update(nodes=[revised])
        self.assertEqual(self.run_cli("get", "A1")["content"], revised["content"])
        affected = {item["node"]["id"] for item in self.run_cli("impact", "A1")["links"]}
        self.assertTrue({"T1", "T2", "S1", "S2"} <= affected)
        with sqlite3.connect(self.folder / "context.sqlite") as db:
            change, = json.loads(db.execute("SELECT changes FROM history WHERE revision=2").fetchone()[0])
            self.assertEqual(change["before"]["content"], self.plan["nodes"][1]["content"])

    def test_optimistic_concurrency_and_idempotency(self):
        self.apply()
        self.assertEqual(self.apply()["applied_revision"], 1)
        self.assertIn("Stale revision", self.update(expected=0, status=1, nodes=[
            node("G1", "gap", "A new blocker.")]))
        self.plan["reason"] = "Different payload"
        self.assertIn("already used", self.apply(status=1))

    def test_concurrent_writers_cannot_both_commit(self):
        self.apply()
        command = [sys.executable, str(CLI), str(self.folder), "apply", "--expect", "1"]
        processes = [subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) for _ in range(2)]
        for i, process in enumerate(processes):
            payload = dict(request_id=f"writer-{i}", reason="Add a planning note",
                           nodes=[node(f"G{i}", "gap", "Investigate this behavior.")])
            process.stdin.write(json.dumps(payload))
            process.stdin.close()
            process.stdin = None
        outcomes = [process.communicate(timeout=10) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 1])
        self.assertIn("Stale revision", "".join(error for _, error in outcomes))
        self.assertEqual(self.run_cli("inspect")["revision"], 2)

    def test_decision_replacement_preserves_prior_decision(self):
        original = node("D1", "decision", "Cancel before the claim.", "confirmed", "human")
        self.plan["nodes"].append(original)
        self.apply()
        revised = {**original, "content": "Cancel after the claim."}
        self.assertIn("Immutable record", self.update(status=1, nodes=[revised]))
        inferred = node("D2", "decision", revised["content"], "proposed", "inference")
        self.assertIn("human-confirmed replacement", self.update(
            status=1, nodes=[inferred], edges=[edge("D2", "supersedes", "D1")]))
        self.update(nodes=[{**revised, "id": "D2"}],
                    edges=[edge("D2", "supersedes", "D1")])
        self.assertEqual(self.run_cli("get", "D1")["content"], original["content"])
        self.run_cli("render-scope")
        self.assertIn(revised["content"], (self.folder / "SCOPE.md").read_text())
        self.assertNotIn(original["content"], (self.folder / "SCOPE.md").read_text())

    def test_evidence_requires_a_distinct_observation_record(self):
        self.apply()
        self.assertEqual(self.run_cli("gaps")["recorded_evidence_count"], 0)
        observation = node("EV1", "evidence", "Capture from a synthetic fixture run.",
                           "observed", "execution")
        self.assertIn("requires an execution record", self.update(status=1, nodes=[observation]))
        self.update(nodes=[observation], evidence=[
            dict(id="EV1", scenario_id="S2", plan_revision=1, candidate="fixture-1",
                 environment="synthetic test", observed_at="2026-11-19T00:00:00Z",
                 command=RACE, exit_code=0, observations={"http-status": 200},
                 artifact="results.xml")])
        report = self.run_cli("gaps")
        self.assertEqual(report["recorded_evidence_count"], 1)
        self.assertEqual(report["delivery"], "unassessed")
        self.assertIn("inadequate_verification", self.gap_codes())

    def test_end_to_end_detects_http_only_cancellation_then_accepts_effect_assertion(self):
        self.apply()
        report = self.run_cli("validate", status=1)
        self.assertEqual(report["gaps"], [
            {"node": "O-NO-DISPATCH", "code": "inadequate_verification",
             "message": "Planned assertions do not observe: dispatch-count."},
            {"node": "T2", "code": "blocked_by_plan_gap",
             "message": "Resolve related findings: O-NO-DISPATCH."},
        ])
        self.assertEqual(report["ready_tasks"], ["T1"])
        self.update(nodes=[node("AS3", "assertion", "Inspect the worker dispatch log after release.",
                                observables=["dispatch-count"])],
                    edges=[edge("S2", "has_assertion", "AS3")])
        self.assertTrue(self.run_cli("validate")["ready"])
        coverage, = self.run_cli("coverage", "O-NO-DISPATCH")
        self.assertEqual(coverage["scenarios"][0]["assertions"], ["AS2", "AS3"])
        self.assertEqual(coverage["scenarios"][0]["recorded_evidence"], [])
        self.run_cli("render-scope")
        self.assertTrue(self.run_cli("inspect")["scope_current"])


if __name__ == "__main__":
    unittest.main()
