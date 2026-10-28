"""Read-only contract probes, not execution of scope-refinement by an LLM.

Run from ai-dev-environment: python -B docs/specs/otimizacao_scope_refinement/experimento.py
Synthetic fixtures exercise only the proposed dependency/readiness policy.
"""
import copy
import hashlib
import json
import platform
import re
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills/authored"
OUTPUT = Path(__file__).parent


def inspect_plan(plan, revision):
    """Partial experimental gate; not a production validator or factual verifier."""
    errors = []
    if plan.get("schema_version") != 1:
        errors.append("schema")
    if plan.get("status") != "ready":
        errors.append("not_ready")
    if plan.get("base_revision") != revision:
        errors.append("stale_revision")
    tasks = plan.get("tasks", [])
    identifiers = [task["id"] for task in tasks]
    if not tasks or len(identifiers) != len(set(identifiers)):
        errors.append("task_identity")
    accepted = {item["id"] for item in plan.get("acceptance", [])}
    evidence = {item["id"]: item for item in plan.get("evidence", [])}
    graph = {}
    for task in tasks:
        deps = task.get("depends_on")
        if not isinstance(deps, list) or any(dep not in identifiers for dep in deps):
            errors.append("dependency")
            continue
        graph[task["id"]] = set(deps)
        if not task.get("acceptance_ids") or not set(task["acceptance_ids"]) <= accepted:
            errors.append("acceptance")
        for ref in task.get("evidence_ids", []):
            if ref not in evidence or evidence[ref]["status"] != "supported":
                errors.append("evidence_requires_review")
    while graph:
        ready = {key for key, deps in graph.items() if not deps}
        if not ready:
            errors.append("cycle")
            break
        graph = {key: deps - ready for key, deps in graph.items() if key not in ready}
    if any(question["blocking"] and question["status"] != "resolved" for question in plan.get("questions", [])):
        errors.append("blocking_question")
    return sorted(set(errors))


def main():
    start = time.perf_counter()
    files = sorted((SKILLS / "scope-refinement").rglob("*"))
    files = [path for path in files if path.is_file()]
    hashes = {str(path.relative_to(ROOT).as_posix()): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    text = (SKILLS / "scope-refinement/agents/03-tactical-design.md").read_text(encoding="utf-8")
    examples = re.findall(r"^## Section 6 — Ordered Development Tasks\n```json\n(.*?)\n```", text, re.M | re.S)
    assert len(examples) == 2
    tasks = [task for block in examples for task in json.loads(block)]
    violations = [dict(title=task["title"], scope_items=len(task["scope"])) for task in tasks if not 2 <= len(task["scope"]) <= 4]
    assert len(violations) == 1
    # This follows the documented no-fence fallback, not an installed parser.
    raw = json.dumps(json.loads(examples[0]))
    extracted = raw[raw.index("{"):raw.rindex("}") + 1]
    try:
        json.loads(extracted)
    except json.JSONDecodeError:
        fallback_failed = True
    else:
        fallback_failed = False
    assert fallback_failed
    pbi = dict(id="PBI-7", title="Export orders", description="Export only visible orders",
               assumptions=[dict(id="Q01", status="Provisional model assumption", answered_by="model", answer="CSV only")],
               source="fixture:pbb", acceptance=["Preserve authorization"])
    projected = dict(scope=pbi["title"] + " " + pbi["description"], projectPaths=["fixture/api"], domain="export_orders", rules="No additional rules provided")
    assert pbi["assumptions"][0]["status"] not in json.dumps(projected)
    plan = dict(schema_version=1, status="ready", base_revision="fixture-r1",
        acceptance=[dict(id="AC1", statement="Preserve authorization")],
        evidence=[dict(id="E1", status="supported", source="fixture:policy")], questions=[],
        tasks=[dict(id=identifier, project_id=project, depends_on=deps, acceptance_ids=["AC1"], evidence_ids=["E1"])
               for identifier, project, deps in (("api:contract", "api", []), ("web:consumer", "web", []),
                                                  ("cross:verify", "api", ["api:contract", "web:consumer"]))])
    assert inspect_plan(plan, "fixture-r1") == []
    probes = []
    def check(name, variant, expected, revision="fixture-r1"):
        actual = inspect_plan(variant, revision)
        assert expected in actual, (name, actual)
        probes.append(dict(name=name, rejected_for=actual))
    check("changed_revision", plan, "stale_revision", "fixture-r2")
    variant = copy.deepcopy(plan)
    variant["evidence"][0]["status"] = "stale"
    check("stale_evidence", variant, "evidence_requires_review")
    variant["evidence"][0]["status"] = "conflicted"
    check("conflicted_evidence", variant, "evidence_requires_review")
    variant = copy.deepcopy(plan)
    variant["questions"] = [dict(id="Q01", blocking=True, status="provisional")]
    check("provisional_blocking_answer", variant, "blocking_question")
    variant = copy.deepcopy(plan)
    variant["tasks"][0]["depends_on"] = ["cross:verify"]
    check("dependency_cycle", variant, "cycle")
    variant = copy.deepcopy(plan)
    variant["tasks"][0]["depends_on"] = ["unknown"]
    check("unknown_dependency", variant, "dependency")
    variant = copy.deepcopy(plan)
    variant["tasks"][0]["acceptance_ids"] = []
    check("missing_acceptance", variant, "acceptance")
    variant = copy.deepcopy(plan)
    variant["tasks"][1]["id"] = variant["tasks"][0]["id"]
    check("duplicate_task", variant, "task_identity")
    with tempfile.TemporaryDirectory(prefix="scope-investigation-") as directory:
        root = Path(directory)
        expected = [root / "004-api-test-scenarios.md", root / "004-web-test-scenarios.md"]
        for path in expected:
            path.write_text("", encoding="utf-8")
        existence_gate = all(path.is_file() for path in expected)
        assert existence_gate
        incomplete = dict(schema_version=1, status="draft", base_revision="fixture-r1", tasks=[])
        check("empty_planning_output", incomplete, "not_ready")
    identifiers = [Path(path).name for path in ("workspace/acme/service", "workspace/beta/service")]
    assert len(set(identifiers)) < len(identifiers)
    assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in hashes.items())
    result = dict(environment=dict(python=platform.python_version(), platform=platform.platform()),
        method="Static source checks plus synthetic policy probes; no LLM execution or production validation.",
        source_sha256=hashes, source_files=len(files), source_characters=sum(len(p.read_text(encoding="utf-8")) for p in files),
        example_task_count=len(tasks), example_scope_violations=violations,
        documented_object_fallback_fails_on_two_task_array=fallback_failed,
        pbb_documented_projection=projected, omitted_pbb_fields=["id", "source", "assumptions", "acceptance"],
        existence_gate_accepts_empty_files=existence_gate, duplicate_project_basenames=identifiers,
        candidate_accepts_join=True, candidate_rejections=probes,
        required_artifact_counts=[dict(projects=p, current=2+2*p, proposed_minimal=1) for p in (1,2,10,50)],
        elapsed_ms=round((time.perf_counter()-start)*1000, 2),
        limitations=["Candidate gate is partial and hand-written, not semantic validation.",
                     "PBB projection models documented fields, not full runtime context.",
                     "Artifact counts measure mandated structure, not quality or tokens.",
                     "Single run; elapsed time is a harness cost, not refinement performance."])
    (OUTPUT / "resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({key: value for key, value in result.items() if key != "source_sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
