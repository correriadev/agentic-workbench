#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "tdd-orchestrator" / "scripts"))
from triad_state import TriadStateManager


class TestTriadState(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="triad-test-"))
        self.spec_dir = self.temp_dir / "docs" / "specs" / "test-change"
        self.spec_dir.mkdir(parents=True)

        self.initial_tasks = {
            "change_id": "test-change",
            "scope_hash": "abc123",
            "tasks": [
                {"id": "T1", "title": "Task 1", "description": "Do 1", "status": "pending"},
                {"id": "T2", "title": "Task 2", "description": "Do 2", "status": "pending"}
            ]
        }
        self.initial_qa = {
            "change_id": "test-change",
            "scope_hash": "abc123",
            "snapshot_ref": "base1",
            "invariants": [{"id": "QA-I-01", "eval_command": "true"}],
            "metrics": [{"name": "cov", "eval_command": "true"}]
        }

        with open(self.spec_dir / "tasks.json", "w", encoding="utf-8") as f:
            json.dump(self.initial_tasks, f)
        with open(self.spec_dir / "qa.json", "w", encoding="utf-8") as f:
            json.dump(self.initial_qa, f)

        self.mgr = TriadStateManager(self.spec_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_execution(self):
        exec_block = self.mgr.init_execution("main", "base1")
        self.assertEqual(exec_block["phase"], "planning")
        self.assertEqual(exec_block["accepted_oid"], "base1")
        self.assertTrue((self.spec_dir / "runs").is_dir())

    def test_lifecycle_success_path(self):
        self.mgr.init_execution("main", "base1")
        
        # 1. Start batch
        batch = self.mgr.start_batch("B1", ["T1"], "base1")
        self.assertEqual(batch["phase"], "making")
        self.assertEqual(batch["task_ids"], ["T1"])

        # 2. Record candidate
        cand = self.mgr.record_candidate("cand1")
        self.assertEqual(cand["phase"], "checking")
        self.assertEqual(cand["candidate_oid"], "cand1")

        # 3. Record QA verdict PASS
        qa_result = {
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand1",
            "status": "PASS",
            "scope": "batch",
            "blocking_failures": 0,
            "advisory_findings": 0,
            "rework_queue": [
                {
                    "id": "RW-001",
                    "status": "resolved",
                    "severity": "advisory",
                    "finding": "minor note"
                }
            ]
        }
        res = self.mgr.record_verdict(qa_result)
        self.assertEqual(res["phase"], "reconciled")
        self.assertEqual(res["run_id"], 1)

        # Check run file was partitioned
        run_file = self.spec_dir / "runs" / "run-1.json"
        self.assertTrue(run_file.is_file())
        with open(run_file, "r", encoding="utf-8") as f:
            rdata = json.load(f)
            self.assertEqual(rdata["snapshot_ref"], "cand1")

        # Check qa.json verdicts is compact
        with open(self.spec_dir / "qa.json", "r", encoding="utf-8") as f:
            qdata = json.load(f)
            self.assertEqual(len(qdata["verdicts"]), 1)
            self.assertEqual(qdata["verdicts"][0]["run_file"], "runs/run-1.json")
            self.assertEqual(len(qdata["rework_queue"]), 1)

        # 4. Integrate batch
        integ = self.mgr.integrate_batch("cand1")
        self.assertEqual(integ["phase"], "integrated")
        self.assertEqual(integ["accepted_oid"], "cand1")

        # Check T1 is marked completed in tasks.json
        with open(self.spec_dir / "tasks.json", "r", encoding="utf-8") as f:
            tdata = json.load(f)
            self.assertEqual(tdata["tasks"][0]["status"], "completed")
            self.assertEqual(len(tdata["completed_batches"]), 1)

    def test_failure_retry_limit_and_operator_override(self):
        self.mgr.init_execution("main", "base1")
        self.mgr.start_batch("B1", ["T1"], "base1")
        self.mgr.record_candidate("cand1")

        qa_fail = {
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand1",
            "status": "FAIL",
            "scope": "batch",
            "blocking_failures": 1,
            "rework_queue": [
                {
                    "id": "RW-001",
                    "status": "open",
                    "severity": "blocking",
                    "finding": "broken invariant"
                }
            ]
        }

        # 1st fail -> rework
        res1 = self.mgr.record_verdict(qa_fail)
        self.assertEqual(res1["phase"], "rework")
        self.assertEqual(res1["retries_used"], 1)

        # 2nd attempt
        self.mgr.record_candidate("cand2")
        qa_fail["snapshot_ref"] = "cand2"
        res2 = self.mgr.record_verdict(qa_fail)
        # retry_limit is 2 -> reaches 2 -> blocked!
        self.assertEqual(res2["phase"], "blocked")
        self.assertEqual(res2["retries_used"], 2)

        # Cannot integrate while blocked
        with self.assertRaises(ValueError):
            self.mgr.integrate_batch("cand2")

        # Operator override to grant 2 more retries
        over = self.mgr.operator_override(2, "Human authorized additional repair cycle")
        self.assertEqual(over["phase"], "rework")
        self.assertEqual(over["retry_limit"], 4)
        self.assertEqual(len(over["operator_grants"]), 1)

        # 3rd attempt
        self.mgr.record_candidate("cand3")
        qa_pass = {
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand3",
            "status": "PASS",
            "scope": "batch",
            "blocking_failures": 0,
            "rework_queue": [
                {
                    "id": "RW-001",
                    "status": "resolved",
                    "severity": "blocking",
                    "finding": "now fixed"
                }
            ]
        }
        res3 = self.mgr.record_verdict(qa_pass)
        self.assertEqual(res3["phase"], "reconciled")

        # Now integration succeeds
        integ = self.mgr.integrate_batch("cand3")
        self.assertEqual(integ["phase"], "integrated")
        self.assertEqual(integ["accepted_oid"], "cand3")


    def test_reopen_tracking_and_loop_breaker(self):
        self.mgr.init_execution("main", "base1")
        self.mgr.start_batch("B1", ["T1"], "base1")
        self.mgr.record_candidate("cand1")

        # Run 1: resolve RW-001 in B1
        self.mgr.record_verdict({
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand1",
            "status": "PASS",
            "scope": "batch",
            "rework_queue": [{"id": "RW-001", "status": "resolved", "severity": "blocking"}]
        })
        self.mgr.integrate_batch("cand1")

        # Start B2: attempt 1 - regression! RW-001 reopens -> reopen count 1
        self.mgr.start_batch("B2", ["T2"], "cand1")
        self.mgr.record_candidate("cand2")
        res2 = self.mgr.record_verdict({
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand2",
            "status": "FAIL",
            "scope": "batch",
            "rework_queue": [{"id": "RW-001", "status": "open", "severity": "blocking"}]
        })
        self.assertEqual(res2["reopens_used"], 1)
        self.assertEqual(res2["phase"], "rework")

        # In B2 rework: attempt 2 fixes RW-001
        self.mgr.record_candidate("cand3")
        res3 = self.mgr.record_verdict({
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand3",
            "status": "PASS",
            "scope": "batch",
            "rework_queue": [{"id": "RW-001", "status": "resolved", "severity": "blocking"}]
        })
        self.assertEqual(res3["phase"], "reconciled")
        self.mgr.integrate_batch("cand3")

        # Now start B3 (let's say another batch or another task)
        # Add T3 to tasks.json first
        with open(self.spec_dir / "tasks.json", "r+", encoding="utf-8") as f:
            tdata = json.load(f)
            tdata["tasks"].append({"id": "T3", "title": "T3", "description": "D3", "status": "pending"})
            f.seek(0)
            json.dump(tdata, f, indent=2)
            f.truncate()

        self.mgr.start_batch("B3", ["T3"], "cand3")
        self.mgr.record_candidate("cand4")
        res4 = self.mgr.record_verdict({
            "protocol": "triad.qa.result.v1",
            "snapshot_ref": "cand4",
            "status": "FAIL",
            "scope": "batch",
            "rework_queue": [{"id": "RW-001", "status": "open", "severity": "blocking"}]
        })
        # RW-001 reopened twice across history -> blocked by loop breaker!
        self.assertEqual(res4["phase"], "blocked")

    def test_suspend_batch_and_status(self):
        self.mgr.init_execution("main", "base1")
        self.mgr.start_batch("B1", ["T1"], "base1")
        susp = self.mgr.suspend_batch("B1", "containment_unavailable")
        self.assertEqual(susp["phase"], "blocked")

        status = self.mgr.get_status()
        self.assertEqual(status["phase"], "blocked")
        self.assertEqual(status["batch_id"], "B1")


    def test_cli_execution(self):
        import subprocess
        cli_path = REPO_ROOT / "skills" / "tdd-orchestrator" / "scripts" / "triad_state.py"

        # init via CLI
        cmd = [sys.executable, str(cli_path), str(self.spec_dir), "init", "--target-branch", "main", "--accepted-oid", "base0"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["phase"], "planning")

        # start-batch via CLI
        cmd = [sys.executable, str(cli_path), str(self.spec_dir), "start-batch", "--batch", "B1", "--tasks", "T1", "--base", "base0"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["phase"], "making")

        # status via CLI
        cmd = [sys.executable, str(cli_path), str(self.spec_dir), "status"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["batch_id"], "B1")
        self.assertEqual(data["phase"], "making")


if __name__ == "__main__":
    unittest.main()
