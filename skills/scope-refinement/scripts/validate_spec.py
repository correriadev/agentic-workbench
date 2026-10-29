#!/usr/bin/env python3
"""Validate the tripartite specification directory (SCOPE.md, tasks.json, qa.json).

Usage:
    python validate_spec.py docs/specs/<change-id>
"""
import json
import re
import sys
from pathlib import Path


def validate_spec_dir(spec_path: Path) -> list[str]:
    errors = []
    if not spec_path.is_dir():
        return [f"Directory not found: {spec_path}"]

    scope_file = spec_path / "SCOPE.md"
    tasks_file = spec_path / "tasks.json"
    qa_file = spec_path / "qa.json"

    # 1. Existence check
    for file, name in [(scope_file, "SCOPE.md"), (tasks_file, "tasks.json"), (qa_file, "qa.json")]:
        if not file.is_file():
            errors.append(f"Missing required file: {name}")

    if errors:
        return errors

    # 2. SCOPE.md validation
    scope_text = scope_file.read_text(encoding="utf-8")
    acceptances = re.findall(r"^-\s+\*\*(A\d+):\*\*", scope_text, re.MULTILINE)
    if not acceptances:
        errors.append("SCOPE.md must define at least one acceptance criterion matching '- **A1:**'")

    # 3. tasks.json validation
    try:
        tasks_data = json.loads(tasks_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return errors + [f"tasks.json is not valid JSON: {err}"]

    tasks = tasks_data.get("tasks", [])
    if not tasks:
        errors.append("tasks.json contains no tasks")

    task_ids = set()
    edges = 0
    linear_predecessors = 0

    for idx, task in enumerate(tasks):
        t_id = task.get("id")
        if not t_id or t_id in task_ids:
            errors.append(f"Task index {idx} has invalid or duplicate id: {t_id}")
        task_ids.add(t_id)

        if not task.get("title") or not task.get("description"):
            errors.append(f"Task {t_id} missing title or description")

        if "contract_delta" not in task or not isinstance(task["contract_delta"], dict):
            errors.append(f"Task {t_id} missing required 'contract_delta' object")

        if not task.get("files_allowed") or not isinstance(task["files_allowed"], list):
            errors.append(f"Task {t_id} missing non-empty 'files_allowed' array")

        deps = task.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append(f"Task {t_id} 'depends_on' must be a list of objects")
        else:
            edges += len(deps)
            for dep in deps:
                if isinstance(dep, dict):
                    if not dep.get("task") or not dep.get("reason"):
                        errors.append(f"Task {t_id} depends_on entry must have 'task' and 'reason'")
                    if idx > 0 and dep.get("task") == tasks[idx - 1].get("id"):
                        linear_predecessors += 1
                else:
                    errors.append(f"Task {t_id} depends_on item must be an object with task and reason")

    # Anti-linear chain check
    if len(tasks) >= 4 and linear_predecessors == len(tasks) - 1 and edges == len(tasks) - 1:
        errors.append("Anti-Linear DAG violation: tasks form an artificial strict linked-list (T1->T2->T3...). Decouple independent tasks into parallel roots/branches.")

    # 4. qa.json validation
    try:
        qa_data = json.loads(qa_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return errors + [f"qa.json is not valid JSON: {err}"]

    if "metrics" not in qa_data or not isinstance(qa_data["metrics"], list):
        errors.append("qa.json missing mandatory 'metrics' array")

    invariants = qa_data.get("invariants", [])
    if not invariants:
        errors.append("qa.json must contain at least one invariant")

    qa_acceptances = set()
    for inv in invariants:
        inv_id = inv.get("id", "unknown")
        for acc in inv.get("acceptance_ids", []):
            qa_acceptances.add(acc)

        eval_cmd = inv.get("eval_command")
        manual_gate = inv.get("manual_gate")
        if not eval_cmd and not manual_gate:
            errors.append(f"Invariant {inv_id} must define either 'eval_command' or 'manual_gate: true'")

    # 5. Traceability closure
    task_acceptances = {acc for task in tasks for acc in task.get("acceptance_ids", [])}
    for acc in acceptances:
        if acc not in task_acceptances:
            errors.append(f"Acceptance {acc} from SCOPE.md not claimed in tasks.json")
        if acc not in qa_acceptances:
            errors.append(f"Acceptance {acc} from SCOPE.md not evaluated in qa.json invariants")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_spec.py <spec_directory>")
        sys.exit(2)

    spec_dir = Path(sys.argv[1])
    errors = validate_spec_dir(spec_dir)
    if errors:
        print(f"[FAIL] Specification validation failed for {spec_dir}:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"[PASS] Tripartite specification is valid: {spec_dir}")
        sys.exit(0)


if __name__ == "__main__":
    main()
