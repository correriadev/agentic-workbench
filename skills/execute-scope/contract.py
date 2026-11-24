#!/usr/bin/env python3
"""Inspect and update one change's contracts using optimistic concurrency."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import re
import sqlite3


def digest(data):
    return hashlib.sha256(data).hexdigest()


def contract_digest(contract):
    return digest(json.dumps(contract, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":"), allow_nan=False).encode())


def read(path):
    if not path.exists():
        return None, None
    data = path.read_bytes()
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return value, digest(data)


@contextmanager
def lock(folder):
    # Keep the lock file in place so all processes lock the same inode.
    with (folder / ".contracts.guard").open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def save(path, value):
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    atomic_write(path, data.encode())


def atomic_write(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


def indexed(items):
    result = {item["id"]: item for item in items}
    if len(result) != len(items):
        raise ValueError("Duplicate IDs")
    return result


def nonempty_text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_blueprint(folder, document):
    source = folder / 'context.sqlite'
    binding = document.get('blueprint_source')
    if not binding:
        if source.exists():
            raise ValueError('New Scope specification exists; reconcile the task plan with its current revision')
        return  # Legacy plans without a New Scope database remain supported.
    if (not isinstance(binding, dict) or set(binding) != {'revision', 'sha256'}
            or type(binding['revision']) is not int or not isinstance(binding['sha256'], str)
            or source.is_symlink() or not source.is_file()
            or any((folder / ('context.sqlite' + suffix)).exists() for suffix in ('-wal', '-journal'))):
        raise ValueError('New Scope source is unavailable, active, or invalid')
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('BEGIN')
        row = db.execute('SELECT change_id, revision FROM spec_meta').fetchone()
        if (not row or row != (document['change_id'], binding['revision'])
                or digest(source.read_bytes()) != binding['sha256']):
            raise ValueError('New Scope specification changed; reconcile the task plan')
        nodes = {key: (content, json.loads(details)) for key, content, details in db.execute(
            "SELECT id,content,details FROM nodes WHERE kind='task' "
            "AND state NOT IN ('superseded','resolved') "
            "AND id NOT IN (SELECT dst FROM edges WHERE relation='supersedes')")}
        planned = indexed(document['tasks'])
        blocked = indexed(document.get('blocked_tasks', []))
        if planned.keys() & blocked.keys() or planned.keys() | blocked.keys() != nodes.keys():
            raise ValueError('New Scope tasks and blockers must match the specification')
        for key, task in planned.items():
            details = db.execute('SELECT project_root,kind,unit_command,red,green FROM task_details WHERE task_id=?',
                                 (key,)).fetchone()
            if not details:
                raise ValueError('New Scope task is missing its operational mapping')
            root, kind, command, red, green = details
            files = list(db.execute('SELECT path,origin,role FROM task_files WHERE task_id=? ORDER BY path', (key,)))
            content, extra = nodes[key]
            checks = extra.get('evidence_checks', [])
            qa_ids = list(dict.fromkeys([*extra.get('qa_ids', []),
                                         *(qa for check in checks for qa in check['qa_ids'])]))
            dependencies = [dict(task=entry[0]) for entry in db.execute(
                "SELECT dst FROM edges WHERE src=? AND relation='depends_on' ORDER BY dst", (key,))]
            acceptance = [entry[0] for entry in db.execute(
                "SELECT e.dst FROM edges e JOIN nodes n ON n.id=e.dst WHERE e.src=? AND e.relation='implements' "
                "AND n.kind='acceptance' AND n.state NOT IN ('superseded','resolved') "
                "AND n.id NOT IN (SELECT dst FROM edges WHERE relation='supersedes') ORDER BY e.dst", (key,))]
            expected = dict(id=key, kind=kind, project_path=root, description=content, technical_steps=[content],
                            acceptance_ids=acceptance, files_allowed=[p for p, _, _ in files],
                            planned_files=[p for p, origin, _ in files if origin == 'new'], depends_on=dependencies,
                            qa_ids=qa_ids, evidence_checks=checks)
            if kind == 'implementation':
                expected.update(unit_tests=dict(files=[p for p, _, role in files if role == 'unit'], command=command),
                                red=red, green=green)
            if extra.get('smoke_command'):
                expected['smoke_command'] = extra['smoke_command']
            actual = {k: v for k, v in task.items() if k not in ('status', 'phase', 'attempts', 'error')}
            if actual != expected:
                raise ValueError('New Scope task definition differs from its specification: ' + key)


def text_list(value):
    return isinstance(value, list) and bool(value) and all(map(nonempty_text, value))


def scoped_acceptance_ids(folder, scope_text):
    source = folder / 'context.sqlite'
    if source.exists() or source.is_symlink():
        if (source.is_symlink() or not source.is_file()
                or any((folder / ('context.sqlite' + suffix)).exists() for suffix in ('-wal', '-journal'))):
            raise ValueError('Specification source is unavailable, active, or invalid')
        with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as db:
            db.execute('PRAGMA trusted_schema=OFF')
            db.execute('BEGIN')
            meta = db.execute('SELECT change_id, revision FROM spec_meta').fetchone()
            match = re.search(r'(?m)^Database revision: ([0-9]+)$', scope_text)
            if not meta or meta[0] != folder.name or not match or meta[1] != int(match.group(1)):
                raise ValueError('New Scope specification and scope revisions differ; render the current scope')
            active = {row[0] for row in db.execute(
                "SELECT id FROM nodes WHERE kind='acceptance' AND state <> 'superseded' "
                "AND id NOT IN (SELECT dst FROM edges WHERE relation='supersedes')")}
            section = re.search(r'(?ms)^## Acceptance criteria[ \t]*\r?\n(.*?)(?=^## |\Z)', scope_text)
            rendered = set(re.findall(r'(?m)^- \*\*([A-Za-z][A-Za-z0-9_.:-]*) — ', section.group(1))) if section else set()
            if not section or rendered != active:
                raise ValueError('New Scope acceptance criteria do not match the rendered scope')
            return active
    # Standalone scopes declare each acceptance ID at the beginning of a line or table row.
    return set(re.findall(r'(?m)^[|*# \-]*\*{0,2}(A[A-Za-z0-9_-]*)(?=\*|\s|[:|—])', scope_text))


def validate_qa(contract, scope_text, folder, *, publishing=False):
    obligations = indexed(contract["obligations"])
    risks = set(re.findall(r"(?m)^[|*# \-]*\*{0,2}(R[0-9]+)\b", scope_text))
    acceptances = scoped_acceptance_ids(folder, scope_text)
    coverage = {}
    for entry in contract.get("risk_coverage", []):
        key, refs = entry["risk_id"], set(entry["obligation_ids"])
        if key in coverage or not refs or any(
            ref not in obligations or key not in obligations[ref]["risk_ids"] for ref in refs
        ):
            raise ValueError("Invalid risk coverage")
        coverage[key] = refs
    if risks != coverage.keys():
        raise ValueError("QA coverage must match scoped risks")
    if not obligations and not contract.get("empty_obligations_rationale"):
        raise ValueError("Empty QA contract requires an explicit scope decision")
    for obligation in obligations.values():
        if not text_list(obligation.get("acceptance_ids")) or set(obligation["acceptance_ids"]) - acceptances:
            raise ValueError("QA obligation references an unknown or inactive acceptance criterion")
        if publishing:
            for field in ("acceptance_ids", "risk_ids", "preconditions", "observables",
                          "assertions", "artifacts", "source_refs"):
                if not text_list(obligation.get(field)):
                    raise ValueError(f"Invalid or missing QA field: {field}")
            for field in ("failure_to_detect", "stimulus", "environment"):
                if not nonempty_text(obligation.get(field)):
                    raise ValueError(f"Invalid or missing QA field: {field}")
            if (obligation["status"] == "pending" and not nonempty_text(obligation.get("pending_reason"))
                or obligation["status"] == "ready" and obligation["pending_reason"] is not None):
                raise ValueError("Invalid QA pending reason")
        if type(obligation["blocking"]) is not bool or obligation["status"] not in ("ready", "pending"):
            raise ValueError("Invalid obligation status")
        for risk in obligation["risk_ids"]:
            if obligation["id"] not in coverage.get(risk, set()):
                raise ValueError("Obligation missing from risk coverage")
    return obligations


def task_state(task):
    return task["status"], task["phase"]


STATE_FIELDS = {"status", "phase", "attempts", "error"}


def task_definition(task):
    return {key: value for key, value in task.items() if key not in STATE_FIELDS}


def validate_replan(planned, previous, phases, scope_changed, qa_changed):
    invalidated = set()
    for key, task in planned.items():
        prior = previous.get(key)
        if (not prior or task_definition(task) != task_definition(prior)
            or scope_changed or qa_changed and task.get("evidence_checks")
            or task_state(prior)[0] != "pending" and task_state(task)[0] == "pending"):
            invalidated.add(key)
    while True:
        dependents = {
            key for key, task in planned.items()
            if any(dep["task"] in invalidated for dep in task["depends_on"])
        }
        if dependents <= invalidated:
            break
        invalidated.update(dependents)
    for key, task in planned.items():
        initial = ("pending", phases[key])
        if task_state(task) != initial and (
            key in invalidated or task_state(task) != task_state(previous[key])
        ):
            raise ValueError(f"Replanned task {key} must restart at {initial}")


def validate_tasks(tasks):
    phases = {}
    for key, task in tasks.items():
        check_ids = [check["id"] for check in task.get("evidence_checks", []) if "id" in check]
        if any(not nonempty_text(check_id) for check_id in check_ids) or len(set(check_ids)) != len(check_ids):
            raise ValueError("Duplicate or empty check ID within task")
        kind = task.get("kind", "implementation")
        if kind == "implementation":
            test = task["unit_tests"]
            if not test["files"] or not test["command"].strip():
                raise ValueError("Implementation requires a focused test mapping")
            if not set(test["files"]) <= set(task["files_allowed"]):
                raise ValueError("Unit tests must use authorized paths")
            phases[key] = "red_pending"
        elif kind == "evidence" and task.get("evidence_checks"):
            phases[key] = "evidence_pending"
        else:
            raise ValueError("Invalid task kind or missing evidence checks")
    remaining = {key: {dep["task"] for dep in task["depends_on"]} for key, task in tasks.items()}
    while remaining:
        ready = {key for key, deps in remaining.items() if not deps}
        if not ready:
            raise ValueError("Cyclic or unknown task dependency")
        remaining = {key: deps - ready for key, deps in remaining.items() if key not in ready}
    return phases


def write_paths(task):
    paths = task.get("files_allowed", [])
    if not isinstance(paths, list) or any(not nonempty_text(path) for path in paths):
        raise ValueError("Task write paths must be a list of explicit project-relative files")
    authorized = []
    for path in paths:
        portable = path.replace("\\", "/") if os.name == "nt" else path
        relative = PurePosixPath(portable)
        if (relative.is_absolute() or relative.as_posix() != portable or not relative.parts
                or ".." in relative.parts or re.search(r'[\\:*?\x00-\x1f]', portable)):
            raise ValueError(f"Invalid task write path: {path}")
        authorized.append((path, relative))
    return authorized


def check_live_write_paths(task):
    root = Path(task["project_path"])
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("Task must have an existing absolute project root")
    if is_redirected(root.lstat()):
        raise ValueError("Task project root is a symlink or reparse point")
    missing = []
    for path, relative in write_paths(task):
        current = root
        for part in relative.parts:
            current = current / part
            try:
                info = current.lstat()
            except FileNotFoundError:
                missing.append(path)
                break
            if is_redirected(info):
                raise ValueError(f"Task write path traverses a symlink or reparse point: {path}")
        else:
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"Task write path is not a regular file: {path}")
    return missing


def is_redirected(info):
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))


def validate_task_contract(folder, document, scope, revision):
    validate_blueprint(folder, document)
    if (document["scope_revision"], document.get("qa_revision"), document["change_id"]) != (
        scope, revision, folder.name
    ):
        raise ValueError("Task plan revision mismatch")
    tasks = indexed(document["tasks"])
    phases = validate_tasks(tasks)
    blocked = indexed(document.get("blocked_tasks", []))
    if blocked.keys() & tasks.keys():
        raise ValueError("Executable and blocked task IDs must be disjoint")
    return tasks, phases, blocked


def task_qa_ids(task):
    return set(task.get("qa_ids", [])) | {qa for check in task.get("evidence_checks", []) for qa in check["qa_ids"]}


def preflight(folder, task_id):
    scope_bytes = (folder / "SCOPE.md").read_bytes()
    scope = digest(scope_bytes)
    document, tasks_digest = read(folder / "tasks.json")
    if document is None:
        raise ValueError("Publish the task plan first")
    qa, _ = read(folder / "qa.json")
    contract = qa.get("contract") if qa is not None else None
    if qa is not None and (not isinstance(contract, dict) or contract["scope_revision"] != scope
                           or contract["change_id"] != folder.name):
        raise ValueError("Replan the stale or legacy QA contract")
    revision = contract_digest(contract) if contract is not None else None
    tasks, phases, blocked = validate_task_contract(folder, document, scope, revision)
    if task_id in blocked:
        raise ValueError(f"Task is blocked: {task_id}")
    if task_id not in tasks:
        raise ValueError(f"Unknown task: {task_id}")
    task = tasks[task_id]
    status, phase = task_state(task)
    active_phases = {phases[task_id]}
    if phases[task_id] == "red_pending":
        active_phases.add("green_pending")
    if ((status, phase) != ("completed", "completed")
            and (status not in {"pending", "in_progress"} or phase not in active_phases)):
        raise ValueError(f"Task is not ready for execution or reconciliation: {task_id}")
    if any(task_state(tasks[dep["task"]]) != ("completed", "completed") for dep in task["depends_on"]):
        raise ValueError("Task dependencies are incomplete")
    obligations = validate_qa(contract, scope_bytes.decode(), folder) if contract else {}
    links = task_qa_ids(task)
    if links - obligations.keys():
        raise ValueError("Unknown QA obligation")
    evidence = document.get("evidence", [])
    finished = {record["attempt_id"] for record in evidence if record.get("event") == "result"}
    return dict(task=task, scope_revision=scope, qa_revision=revision, tasks_digest=tasks_digest,
                blueprint_source=document.get("blueprint_source"), missing_paths=check_live_write_paths(task),
                qa_obligations=[obligations[key] for key in sorted(links)],
                unfinished_attempts=[record for record in evidence if record.get("event") == "started"
                                     and record["task_id"] == task_id and record["id"] not in finished])


def validate_transition(before, after, first):
    old, new = task_state(before), task_state(after)
    if old == new:
        return
    final = "green_pending" if first == "red_pending" else first
    status, phase = old
    if status == "pending" and phase in (first, final):
        allowed = {("in_progress", phase)}
    elif status == "in_progress" and phase in (first, final):
        allowed = {("pending", phase), ("failed", phase), ("failed", "failed")}
        allowed.add(("completed", "completed") if phase == final else ("in_progress", final))
    else:
        allowed = set()
    if new not in allowed:
        raise ValueError(f"Invalid task transition {old} -> {new}")


def validate_legacy_evidence(record, tasks, revision, obligations):
    required = ("command", "test_refs", "assertions", "environment")
    if any(not record.get(key) for key in required) or record.get("observed_values") is None or type(record.get("exit_code")) is not int:
        raise ValueError("Incomplete execution evidence")
    task = tasks[record["task_id"]]
    links = set(record["qa_ids"])
    executed = task["status"] == "completed" or (
        task["status"] == "failed" and record["exit_code"] != 0
    )
    if (record["qa_revision"] != revision or not record["candidate"] or not links
        or links - obligations.keys() or not executed
        or not any(check["command"] == record["command"] and links <= set(check["qa_ids"])
                   for check in task.get("evidence_checks", []))):
        raise ValueError("Evidence does not match a executed planned check")



def validate_start(record, tasks, revision, obligations):
    task = tasks[record["task_id"]]
    definition = record["definition"]
    check = next(
        (item for item in task.get("evidence_checks", []) if item.get("id") == record["check_id"]), None
    )
    if not check or definition != {"cwd": task["project_path"], "check": check}:
        raise ValueError("Attempt definition does not match its planned check")
    if (not nonempty_text(record["id"]) or record["definition_digest"] != contract_digest(definition)
        or not revision or record["qa_revision"] != revision
        or task["status"] not in ("in_progress", "completed")
        or not nonempty_text(record["candidate"]) or not record["environment"]
        or not text_list(check["qa_ids"]) or set(check["qa_ids"]) - obligations.keys()):
        raise ValueError("Invalid check attempt start")


def validate_result(record, start):
    if (start["event"] != "started" or not nonempty_text(record["id"])
        or record["status"] not in ("observed", "inconclusive")
        or not record.get("artifact_ref") or not nonempty_text(record["candidate_after"])):
        raise ValueError("Invalid check attempt result")
    if record["status"] == "observed" and (
        start["candidate"] != record["candidate_after"]
        or start["environment"] != record["environment_after"]
        or type(record["exit_code"]) is not int
        or record.get("observed_values") is None
        or not text_list(record.get("test_refs"))
        or not text_list(record.get("assertions"))
    ):
        raise ValueError("Observed result requires stable identity and recorded observations")


def validate_new_evidence(evidence, old, tasks, previous, revision, obligations):
    finished = {record["attempt_id"] for record in old.values() if record.get("event") == "result"}
    for key, record in evidence.items():
        if key in old:
            continue
        if record.get("event") == "started":
            validate_start(record, tasks, revision, obligations)
            validate_start(record, previous, revision, obligations)
        elif record.get("event") == "result":
            attempt = record["attempt_id"]
            if attempt not in old or attempt in finished:
                raise ValueError("Result requires a previously persisted unfinished attempt")
            validate_result(record, old[attempt])
            finished.add(attempt)
        else:
            raise ValueError("Append new evidence as check attempt events")


def verify_finding_evidence(record, evidence, tasks, revision, obligations, assessment, obligation_id, status):
    if record.get("event") == "result":
        start = evidence[record["attempt_id"]]
        validate_result(record, start)
        if (start["candidate"] != assessment["candidate"] or start["qa_revision"] != revision
            or obligation_id not in start["definition"]["check"]["qa_ids"]):
            raise ValueError("Finding cites unrelated or stale evidence")
        if status != "INCONCLUSIVE":
            if record["status"] != "observed":
                raise ValueError("A conclusive finding requires an observed result")
            task = tasks.get(start["task_id"], {})
            if (task.get("project_path") != start["definition"]["cwd"]
                or start["definition"]["check"] not in task.get("evidence_checks", [])):
                raise ValueError("Finding cites a superseded check definition")
        if status == "PASS" and record.get("exit_code") != 0:
            raise ValueError("PASS cannot cite a failed check")
        return
    if record.get("event"):
        raise ValueError("Findings must cite results, not attempt starts")
    validate_legacy_evidence(record, tasks, revision, obligations)
    if (record["candidate"] != assessment["candidate"] or obligation_id not in record["qa_ids"]
        or status == "PASS" and record["exit_code"] != 0):
        raise ValueError("Finding cites unrelated, stale or failed evidence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("operation", choices=("inspect", "plan", "build", "qa-plan", "qa-check", "scope", "preflight"))
    parser.add_argument("task_id", nargs="?", help="task to inspect before planned execution")
    parser.add_argument("--expect", help="Current destination file digest, or absent")
    args = parser.parse_args()
    folder = args.folder
    if args.operation == "preflight":
        if args.task_id is None:
            parser.error("preflight requires a task ID")
        print(json.dumps(preflight(folder, args.task_id), ensure_ascii=False))
        return
    if args.task_id is not None:
        parser.error("a task ID is supported only by preflight")
    proposed = None if args.operation == "inspect" else (
        sys.stdin.read() if args.operation == "scope" else json.load(sys.stdin)
    )
    with lock(folder):
        scope_path = folder / "SCOPE.md"
        scope_bytes = scope_path.read_bytes() if scope_path.exists() else None
        scope = digest(scope_bytes) if scope_bytes is not None else None
        if args.operation == "scope":
            if (folder / 'context.sqlite').exists() or (folder / 'context.sqlite').is_symlink():
                raise ValueError('New Scope owns this scope; render it from the specification')
            if args.expect != (scope or "absent") or not proposed.strip():
                raise ValueError("Scope changed or is empty")
            atomic_write(scope_path, proposed.encode())
            return
        if scope is None and args.operation != "inspect":
            raise ValueError("Create SCOPE.md first")
        tasks, tasks_digest = read(folder / "tasks.json")
        qa, qa_digest = read(folder / "qa.json")
        contract = qa.get("contract") if qa else None
        revision = contract_digest(contract) if contract is not None else None
        if args.operation == "inspect":
            print(json.dumps(dict(scope_revision=scope, qa_revision=revision,
                                  tasks_digest=tasks_digest, qa_digest=qa_digest)))
            return
        value = proposed
        task_write = args.operation in ("plan", "build")
        current_digest = tasks_digest if task_write else qa_digest
        if args.expect != (current_digest or "absent"):
            raise ValueError("Destination changed. Inspect and reconcile before retrying.")
        if args.operation == "qa-plan":
            if value["scope_revision"] != scope or value["change_id"] != folder.name:
                raise ValueError("QA contract has stale scope or wrong change ID")
            validate_qa(value, scope_bytes.decode(), folder, publishing=True)
            value = {"contract": value, "assessments": qa.get("assessments", []) if qa else []}
        else:
            if qa and (contract is None or contract["scope_revision"] != scope
                       or contract["change_id"] != folder.name):
                raise ValueError("Replan the stale or legacy QA contract")
            obligations = validate_qa(contract, scope_bytes.decode(), folder) if contract else {}
            if task_write:
                planned, phases, _ = validate_task_contract(folder, value, scope, revision)
                previous = indexed(tasks["tasks"]) if tasks else {}
                if args.operation == "plan":
                    validate_replan(
                        planned, previous, phases,
                        bool(tasks) and tasks["scope_revision"] != scope,
                        bool(tasks) and tasks.get("qa_revision") != revision,
                    )
                for key, task in planned.items():
                    if args.operation == "plan":
                        write_paths(task)
                    else:
                        validate_transition(previous[key], task, phases[key])
                        if task_state(task) != task_state(previous[key]):
                            if any(task_state(previous[dep["task"]]) != ("completed", "completed")
                                   for dep in task["depends_on"]):
                                raise ValueError("Task dependencies are incomplete")
                            if task["status"] == "in_progress":
                                check_live_write_paths(task)
                    if task_qa_ids(task) - obligations.keys():
                        raise ValueError("Unknown QA obligation")
                evidence = indexed(value.get("evidence", []))
                old_evidence = indexed(tasks.get("evidence", [])) if tasks else {}
                if any(evidence.get(key) != record for key, record in old_evidence.items()):
                    raise ValueError("Evidence history is append-only")
                if args.operation == "plan" and evidence != old_evidence:
                    raise ValueError("Only build may append evidence")
                if args.operation == "build":
                    def definition(document):
                        return {**{k: v for k, v in document.items() if k not in ("tasks", "evidence")},
                                "tasks": [task_definition(task) for task in document["tasks"]]}
                    if not tasks or definition(value) != definition(tasks):
                        raise ValueError("Build cannot change the plan")
                    validate_new_evidence(evidence, old_evidence, planned, previous, revision, obligations)
            else:
                if args.operation == 'qa-check' and tasks:
                    validate_blueprint(folder, tasks)
                if (not contract or value["qa_revision"] != revision
                    or value["scope_revision"] != scope or not value["candidate"]):
                    raise ValueError("Assessment does not match current contract")
                assessments = qa.get("assessments", [])
                if value["id"] in indexed(assessments):
                    raise ValueError("Assessment ID already exists")
                if value["status"] not in ("PASS", "FAIL", "INCONCLUSIVE"):
                    raise ValueError("Unknown assessment status")
                evidence = indexed(tasks.get("evidence", [])) if tasks else {}
                findings = indexed(value["findings"])
                if findings.keys() != obligations.keys():
                    raise ValueError("Assess every obligation exactly once")
                blocking = []
                for key, finding in findings.items():
                    status = finding["status"]
                    refs = finding["evidence_ids"]
                    if status not in ("PASS", "FAIL", "INCONCLUSIVE") or not finding["rationale"]:
                        raise ValueError("Invalid finding")
                    if status != "INCONCLUSIVE" and not refs:
                        raise ValueError("A conclusive finding requires evidence")
                    for ref in refs:
                        verify_finding_evidence(
                            evidence[ref], evidence, indexed(tasks["tasks"]),
                            revision, obligations, value, key, status,
                        )
                    if obligations[key]["blocking"]:
                        if obligations[key]["status"] == "pending" and status != "INCONCLUSIVE":
                            raise ValueError("Pending obligation requires inconclusive finding")
                        blocking.append(status)
                expected = ("FAIL" if "FAIL" in blocking else
                            "INCONCLUSIVE" if "INCONCLUSIVE" in blocking or value.get("contract_gap")
                            else "PASS")
                if value["status"] != expected:
                    raise ValueError("Assessment status contradicts its findings")
                value = {**qa, "assessments": [*assessments, value]}
        save(folder / ("tasks.json" if task_write else "qa.json"), value)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError, sqlite3.Error) as error:
        sys.exit(str(error))
