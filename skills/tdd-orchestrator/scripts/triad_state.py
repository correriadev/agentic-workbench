#!/usr/bin/env python3
"""Canonical State Machine and JSON Ledger Tool for the TDD Triad.

Enforces single-writer mechanical governance, atomic disk writes, partitioned
execution runs (docs/specs/<change_id>/runs/run-<N>.json), and strict domain
transitions for tdd-orchestrator.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(file_path: Path, data: Any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(f".tmp.{os.getpid()}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, file_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        raise


def _load_json(file_path: Path) -> Dict[str, Any]:
    if not file_path.is_file():
        raise FileNotFoundError(f"Missing required file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TriadStateManager:
    def __init__(self, spec_dir: Path):
        self.spec_dir = spec_dir.resolve()
        self.tasks_path = self.spec_dir / "tasks.json"
        self.qa_path = self.spec_dir / "qa.json"
        self.runs_dir = self.spec_dir / "runs"

    def ensure_valid_spec(self) -> None:
        if not self.tasks_path.is_file() or not self.qa_path.is_file():
            raise FileNotFoundError(f"Invalid spec directory: {self.spec_dir} must contain tasks.json and qa.json")
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def init_execution(self, target_branch: str = "main", accepted_oid: str = "HEAD") -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        change_id = tasks_data.get("change_id")
        if not change_id:
            raise ValueError("tasks.json missing mandatory 'change_id'")

        execution = tasks_data.get("execution")
        if not execution:
            tasks_data["execution"] = {
                "target_branch": target_branch,
                "accepted_oid": accepted_oid,
                "batch_id": None,
                "batch_base_oid": accepted_oid,
                "dispatch_base_oid": accepted_oid,
                "task_ids": [],
                "candidate_oid": None,
                "candidate_ref": None,
                "phase": "planning",
                "retry_limit": 2,
                "retries_used": 0,
                "qa_reruns_used": 0,
                "reopens_used": 0,
                "operator_grants": []
            }
            if "completed_batches" not in tasks_data:
                tasks_data["completed_batches"] = []
            if "suspended_batches" not in tasks_data:
                tasks_data["suspended_batches"] = []
            _atomic_write_json(self.tasks_path, tasks_data)

        qa_data = _load_json(self.qa_path)
        if "verdicts" not in qa_data:
            qa_data["verdicts"] = []
        if "rework_queue" not in qa_data:
            qa_data["rework_queue"] = []
        _atomic_write_json(self.qa_path, qa_data)

        return tasks_data["execution"]

    def start_batch(self, batch_id: str, task_ids: List[str], base_oid: str) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        exec_block = tasks_data.setdefault("execution", {})

        current_phase = exec_block.get("phase", "planning")
        if current_phase not in ("planning", "integrated", "blocked", "rework"):
            raise ValueError(f"Cannot start batch from active phase: '{current_phase}'")

        # Validate task IDs exist in tasks.json
        defined_tasks = {t.get("id"): t for t in tasks_data.get("tasks", [])}
        for tid in task_ids:
            if tid not in defined_tasks:
                raise ValueError(f"Task '{tid}' not found in tasks.json")
            if defined_tasks[tid].get("status") == "completed":
                raise ValueError(f"Task '{tid}' is already completed")

        change_id = tasks_data.get("change_id", "unnamed")
        candidate_ref = f"refs/triad/candidates/{change_id}/{batch_id}-1"

        exec_block.update({
            "batch_id": batch_id,
            "batch_base_oid": base_oid,
            "dispatch_base_oid": base_oid,
            "task_ids": task_ids,
            "candidate_oid": None,
            "candidate_ref": candidate_ref,
            "phase": "making",
            "retry_limit": 2,
            "retries_used": 0,
            "qa_reruns_used": 0,
            "reopens_used": 0
        })

        _atomic_write_json(self.tasks_path, tasks_data)
        return exec_block

    def record_candidate(self, candidate_oid: str, candidate_ref: Optional[str] = None) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        exec_block = tasks_data.get("execution", {})

        if exec_block.get("phase") not in ("making", "evaluating", "rework"):
            raise ValueError(f"Cannot record candidate in phase: '{exec_block.get('phase')}'")

        exec_block["candidate_oid"] = candidate_oid
        if candidate_ref:
            exec_block["candidate_ref"] = candidate_ref
        exec_block["phase"] = "checking"

        _atomic_write_json(self.tasks_path, tasks_data)
        return exec_block

    def record_verdict(self, qa_result: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        qa_data = _load_json(self.qa_path)
        exec_block = tasks_data.get("execution", {})

        protocol = qa_result.get("protocol")
        if protocol != "triad.qa.result.v1":
            raise ValueError(f"Unsupported QA protocol: '{protocol}', expected 'triad.qa.result.v1'")

        candidate_oid = qa_result.get("snapshot_ref")
        if not candidate_oid:
            raise ValueError("qa_result missing snapshot_ref")

        status = qa_result.get("status")
        if status not in ("PASS", "FAIL"):
            raise ValueError(f"Invalid QA status: '{status}'")

        blocking_failures = qa_result.get("blocking_failures", 0)
        advisory_findings = qa_result.get("advisory_findings", 0)
        scope = qa_result.get("scope", "batch")
        batch_id = exec_block.get("batch_id", "unknown")

        # Determine next run_id
        existing_verdicts = qa_data.setdefault("verdicts", [])
        next_run_id = len(existing_verdicts) + 1

        # 1. Archive full run payload to runs/run-<N>.json
        run_record = {
            "run_id": next_run_id,
            "batch_id": batch_id,
            "snapshot_ref": candidate_oid,
            "scope": scope,
            "status": status,
            "blocking_failures": blocking_failures,
            "advisory_findings": advisory_findings,
            "recorded_at": _now_iso(),
            "raw_result": qa_result
        }
        run_file = self.runs_dir / f"run-{next_run_id}.json"
        _atomic_write_json(run_file, run_record)

        # 2. Reconcile active rework_queue in qa.json
        existing_rework = {item["id"]: item for item in qa_data.setdefault("rework_queue", []) if "id" in item}
        new_or_updated = qa_result.get("rework_queue", [])

        for item in new_or_updated:
            rw_id = item.get("id")
            if not rw_id:
                continue
            if rw_id in existing_rework:
                target = existing_rework[rw_id]
                prev_status = target.get("status")
                new_status = item.get("status", prev_status)
                if prev_status == "resolved" and new_status == "open":
                    target["reopen_count"] = target.get("reopen_count", 0) + 1
                    exec_block["reopens_used"] = exec_block.get("reopens_used", 0) + 1
                target["status"] = new_status
                target["last_run_id"] = next_run_id
                target["severity"] = item.get("severity", target.get("severity", "blocking"))
                target["file"] = item.get("file", target.get("file"))
                target["finding"] = item.get("finding", target.get("finding"))
                target["reproducer"] = item.get("reproducer", target.get("reproducer"))
            else:
                existing_rework[rw_id] = {
                    "id": rw_id,
                    "invariant_id": item.get("invariant_id", "UNSPECIFIED"),
                    "acceptance_ids": item.get("acceptance_ids", []),
                    "severity": item.get("severity", "blocking"),
                    "file": item.get("file"),
                    "reproducer": item.get("reproducer"),
                    "finding": item.get("finding"),
                    "status": item.get("status", "open"),
                    "batch_id": batch_id,
                    "reopen_count": 0,
                    "last_run_id": next_run_id
                }

        qa_data["rework_queue"] = list(existing_rework.values())

        # 3. Append compact summary to qa.json#.verdicts
        compact_verdict = {
            "run_id": next_run_id,
            "batch_id": batch_id,
            "snapshot_ref": candidate_oid,
            "scope": scope,
            "status": status,
            "blocking_failures": blocking_failures,
            "advisory_findings": advisory_findings,
            "run_file": f"runs/run-{next_run_id}.json"
        }
        existing_verdicts.append(compact_verdict)
        qa_data["snapshot_ref"] = candidate_oid

        _atomic_write_json(self.qa_path, qa_data)

        # 4. State transition
        if status == "PASS":
            exec_block["phase"] = "reconciled"
        else:
            retries = exec_block.get("retries_used", 0) + 1
            exec_block["retries_used"] = retries
            retry_limit = exec_block.get("retry_limit", 2)
            reopens = exec_block.get("reopens_used", 0)
            max_item_reopen = max([rw.get("reopen_count", 0) for rw in qa_data.get("rework_queue", [])], default=0)

            if retries >= retry_limit or reopens >= 2 or max_item_reopen >= 2:
                exec_block["phase"] = "blocked"
            else:
                exec_block["phase"] = "rework"

        _atomic_write_json(self.tasks_path, tasks_data)
        return {
            "run_id": next_run_id,
            "status": status,
            "phase": exec_block["phase"],
            "retries_used": exec_block.get("retries_used"),
            "reopens_used": exec_block.get("reopens_used")
        }

    def operator_override(self, grant_retries: int, reason: str) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        exec_block = tasks_data.get("execution", {})

        if exec_block.get("phase") != "blocked":
            raise ValueError(f"operator_override only allowed when phase is 'blocked', current: '{exec_block.get('phase')}'")

        grants = exec_block.setdefault("operator_grants", [])
        grants.append({
            "timestamp": _now_iso(),
            "grant_retries": grant_retries,
            "reason": reason
        })

        exec_block["retry_limit"] = exec_block.get("retry_limit", 2) + grant_retries
        exec_block["phase"] = "rework"

        _atomic_write_json(self.tasks_path, tasks_data)
        return exec_block

    def integrate_batch(self, candidate_oid: str) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        qa_data = _load_json(self.qa_path)
        exec_block = tasks_data.get("execution", {})

        if exec_block.get("phase") != "reconciled":
            raise ValueError(f"integrate_batch requires phase 'reconciled', current: '{exec_block.get('phase')}'")

        if exec_block.get("candidate_oid") != candidate_oid:
            raise ValueError(f"Candidate mismatch: {exec_block.get('candidate_oid')} != {candidate_oid}")

        # Check for open blocking rework
        open_blocking = [
            rw for rw in qa_data.get("rework_queue", [])
            if rw.get("status") == "open" and rw.get("severity") == "blocking"
        ]
        if open_blocking:
            raise ValueError(f"Cannot integrate: {len(open_blocking)} open blocking findings in rework_queue")

        batch_id = exec_block.get("batch_id")
        task_ids = exec_block.get("task_ids", [])

        # Mark tasks completed
        for t in tasks_data.get("tasks", []):
            if t.get("id") in task_ids:
                t["status"] = "completed"

        # Record completed batch
        completed = tasks_data.setdefault("completed_batches", [])
        completed.append({
            "batch_id": batch_id,
            "accepted_oid": candidate_oid,
            "task_ids": task_ids,
            "completed_at": _now_iso()
        })

        exec_block.update({
            "accepted_oid": candidate_oid,
            "batch_base_oid": candidate_oid,
            "dispatch_base_oid": candidate_oid,
            "candidate_oid": None,
            "phase": "integrated"
        })

        _atomic_write_json(self.tasks_path, tasks_data)
        return exec_block

    def suspend_batch(self, batch_id: str, blocker: str) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        exec_block = tasks_data.get("execution", {})

        if exec_block.get("batch_id") != batch_id:
            raise ValueError(f"Active batch is '{exec_block.get('batch_id')}', cannot suspend '{batch_id}'")

        suspended = tasks_data.setdefault("suspended_batches", [])
        suspended.append({
            "batch_id": batch_id,
            "task_ids": exec_block.get("task_ids", []),
            "blocker": blocker,
            "dispatch_base_oid": exec_block.get("dispatch_base_oid"),
            "suspended_at": _now_iso()
        })

        exec_block["phase"] = "blocked"

        _atomic_write_json(self.tasks_path, tasks_data)
        return exec_block

    def get_status(self) -> Dict[str, Any]:
        self.ensure_valid_spec()
        tasks_data = _load_json(self.tasks_path)
        qa_data = _load_json(self.qa_path)
        exec_block = tasks_data.get("execution", {})

        rework = qa_data.get("rework_queue", [])
        open_blocking = [rw for rw in rework if rw.get("status") == "open" and rw.get("severity") == "blocking"]
        open_advisory = [rw for rw in rework if rw.get("status") == "open" and rw.get("severity") != "blocking"]
        resolved = [rw for rw in rework if rw.get("status") == "resolved"]

        return {
            "change_id": tasks_data.get("change_id"),
            "batch_id": exec_block.get("batch_id"),
            "phase": exec_block.get("phase"),
            "accepted_oid": exec_block.get("accepted_oid"),
            "candidate_oid": exec_block.get("candidate_oid"),
            "retries_used": exec_block.get("retries_used", 0),
            "retry_limit": exec_block.get("retry_limit", 2),
            "reopens_used": exec_block.get("reopens_used", 0),
            "total_verdicts": len(qa_data.get("verdicts", [])),
            "open_blocking_findings": len(open_blocking),
            "open_advisory_findings": len(open_advisory),
            "resolved_findings": len(resolved)
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Triad State Machine and Ledger Tool")
    parser.add_argument("spec_dir", type=Path, help="Path to docs/specs/<change_id>")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize execution state block")
    p_init.add_argument("--target-branch", default="main", help="Target branch (default: main)")
    p_init.add_argument("--accepted-oid", default="HEAD", help="Base accepted commit SHA")

    # start-batch
    p_start = subparsers.add_parser("start-batch", help="Start execution of a batch")
    p_start.add_argument("--batch", required=True, help="Batch identifier (e.g. B1)")
    p_start.add_argument("--tasks", required=True, help="Comma-separated task IDs (e.g. T1,T2)")
    p_start.add_argument("--base", required=True, help="Dispatch base commit SHA")

    # record-candidate
    p_cand = subparsers.add_parser("record-candidate", help="Record candidate commit from Maker")
    p_cand.add_argument("--candidate", required=True, help="Candidate commit SHA")
    p_cand.add_argument("--ref", help="Candidate git ref (e.g. refs/triad/candidates/...)")

    # record-verdict
    p_verd = subparsers.add_parser("record-verdict", help="Ingest QA result and partition run")
    p_verd.add_argument("--result-file", type=Path, help="Path to JSON file containing <qa_result>")
    p_verd.add_argument("--result-json", type=str, help="Raw JSON string containing <qa_result>")

    # operator-override
    p_over = subparsers.add_parser("operator-override", help="Grant retries and unblock batch")
    p_over.add_argument("--grant-retries", type=int, required=True, help="Additional retries to grant")
    p_over.add_argument("--reason", type=str, required=True, help="Operator justification")

    # integrate-batch
    p_integ = subparsers.add_parser("integrate-batch", help="Finalize integration of verified batch")
    p_integ.add_argument("--candidate", required=True, help="Verified candidate commit SHA")

    # suspend-batch
    p_susp = subparsers.add_parser("suspend-batch", help="Suspend batch on environment blocker")
    p_susp.add_argument("--batch", required=True, help="Batch identifier")
    p_susp.add_argument("--blocker", required=True, help="Blocker reason (e.g. containment_unavailable)")

    # status
    subparsers.add_parser("status", help="Print active execution and rework status")

    args = parser.parse_args()
    mgr = TriadStateManager(args.spec_dir)

    try:
        if args.command == "init":
            res = mgr.init_execution(args.target_branch, args.accepted_oid)
        elif args.command == "start-batch":
            tasks = [t.strip() for t in args.tasks.split(",") if t.strip()]
            res = mgr.start_batch(args.batch, tasks, args.base)
        elif args.command == "record-candidate":
            res = mgr.record_candidate(args.candidate, args.ref)
        elif args.command == "record-verdict":
            if args.result_file:
                with open(args.result_file, "r", encoding="utf-8") as f:
                    qa_data = json.load(f)
            elif args.result_json:
                qa_data = json.loads(args.result_json)
            else:
                print("Error: Either --result-file or --result-json must be provided", file=sys.stderr)
                sys.exit(2)
            res = mgr.record_verdict(qa_data)
        elif args.command == "operator-override":
            res = mgr.operator_override(args.grant_retries, args.reason)
        elif args.command == "integrate-batch":
            res = mgr.integrate_batch(args.candidate)
        elif args.command == "suspend-batch":
            res = mgr.suspend_batch(args.batch, args.blocker)
        elif args.command == "status":
            res = mgr.get_status()
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(2)

        print(json.dumps(res, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"Error [{args.command}]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
