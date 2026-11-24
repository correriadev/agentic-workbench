"""Deterministic planning checks over typed relationships and observable contracts."""
from collections import defaultdict
from graphlib import TopologicalSorter
import json
from pathlib import Path, PurePosixPath
import re


def repository_path(root, path):
    base = Path(root)
    relative = PurePosixPath(path)
    if (not base.is_absolute() or not base.is_dir() or relative.is_absolute()
            or relative.as_posix() != path or path == "."
            or ".." in relative.parts or re.search(r'[\\:*?\[\]<>|"\x00-\x1f]', path)):
        raise ValueError(f"Invalid project-relative path: {path}")
    target = (base / path).resolve()
    if not target.is_relative_to(base.resolve()):
        raise ValueError(f"Path escapes project root: {path}")
    return target


def active():
    return """state NOT IN ('superseded', 'resolved') AND id NOT IN
              (SELECT dst FROM edges WHERE relation='supersedes')"""


def structural_checks(db):
    types = dict(db.execute("SELECT id, kind FROM nodes"))
    for table, column, kind in (
        ("task_details", "task_id", "task"),
        ("verification_cases", "scenario_id", "test_scenario"),
        ("evidence", "id", "evidence"),
    ):
        for (key,) in db.execute(f"SELECT {column} FROM {table}"):
            if types[key] != kind:
                raise ValueError(f"{key} must be a {kind} for {table}")
    for key, origin in db.execute("SELECT id, origin FROM nodes WHERE kind='evidence'"):
        if origin != "execution" or not db.execute("SELECT 1 FROM evidence WHERE id=?", (key,)).fetchone():
            raise ValueError(f"{key} requires an execution record")
    tasks = TopologicalSorter()
    replacements = TopologicalSorter()
    confirmed = {key for (key,) in db.execute("SELECT id FROM nodes WHERE state='confirmed'")}
    target_types = {
        "has_request": ("api_contract", "request_field"),
        "has_response": ("api_contract", "response_field"),
        "has_error": ("api_contract", "error_contract"),
        "has_assertion": ("test_scenario", "assertion"),
        "depends_on": ("task", "task"),
    }
    for src, relation, dst in db.execute("SELECT src, relation, dst FROM edges"):
        if relation in target_types and (types[src], types[dst]) != target_types[relation]:
            raise ValueError(f"Invalid endpoint types for {relation}: {src}, {dst}")
        if relation == "depends_on":
            tasks.add(src, dst)
        if relation == "supersedes":
            if types[src] != types[dst]:
                raise ValueError("Replacement must preserve node type")
            if dst in confirmed and src not in confirmed:
                raise ValueError("A confirmed node requires a human-confirmed replacement")
            replacements.add(src, dst)
    list(tasks.static_order())
    list(replacements.static_order())


class Plan:
    def __init__(self, db):
        self.db = db
        self.nodes = {}
        self.kinds = defaultdict(set)
        self.links = defaultdict(set)
        for row in db.execute(f"SELECT * FROM nodes WHERE {active()} ORDER BY id"):
            node = dict(row)
            node["details"] = json.loads(node["details"])
            self.nodes[node["id"]] = node
            self.kinds[node["kind"]].add(node["id"])
        for src, relation, dst in db.execute("SELECT src, relation, dst FROM edges"):
            if src in self.nodes and dst in self.nodes:
                self.links[src, relation].add(dst)
                self.links[dst, "^" + relation].add(src)
        for node, scenario in db.execute("SELECT id, scenario_id FROM evidence"):
            if node in self.nodes and scenario in self.nodes:
                self.links[scenario, "^supports"].add(node)

    def linked(self, key, relation, *kinds):
        return sorted(node for node in self.links[key, relation]
                      if not kinds or self.nodes[node]["kind"] in kinds)

    def source(self, key):
        return self.db.execute("SELECT 1 FROM node_sources WHERE node_id=?", (key,)).fetchone()

    def mapping(self, key):
        return self.db.execute("SELECT * FROM verification_cases WHERE scenario_id=?", (key,)).fetchone()

    def scenarios(self, key):
        return self.linked(key, "verified_by", "test_scenario")

    def assertions(self, scenario):
        return self.linked(scenario, "has_assertion", "assertion")

    def obligations(self, key):
        return sorted(set(self.linked(key, "requires", "verification_obligation"))
                      | set(self.linked(key, "^covers", "verification_obligation")))

    def matrix(self, key=None):
        included = self.kinds["behavior"] | self.kinds["acceptance"] | self.kinds["risk"] | self.kinds["verification_obligation"]
        if key and key not in included:
            raise ValueError("Coverage filter must name an active behavior, acceptance, risk or obligation")
        for item in sorted({key} if key else included):
            obligations = self.obligations(item)
            scenarios = set(self.scenarios(item))
            for obligation in obligations:
                scenarios.update(self.scenarios(obligation))
            yield {
                "node": item,
                "obligations": obligations,
                "scenarios": [
                    {"id": scenario, "assertions": self.assertions(scenario),
                     "recorded_evidence": self.linked(scenario, "^supports", "evidence")}
                    for scenario in sorted(scenarios)
                ],
                "required_observables": self.nodes[item]["details"].get("observables", []),
            }


def coverage(db, key=None):
    return list(Plan(db).matrix(key))


def nonempty_names(value):
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v.strip() for v in value)


def assess(db, check_live_paths=True):
    plan = Plan(db)
    gaps = []
    blocked = set()

    def add(node, code, message):
        gaps.append(dict(node=node, code=code, message=message))
        if node in plan.kinds["task"]:
            blocked.add(node)

    for kind in ("intent", "acceptance", "behavior", "task"):
        if not plan.kinds[kind]:
            add("spec", "missing_" + kind, f"Define at least one {kind}.")

    for key, node in plan.nodes.items():
        kind, state, details = node["kind"], node["state"], node["details"]
        reason = details.get("rationale")
        justified = isinstance(reason, str) and bool(reason.strip())
        if state == "blocked" or (kind == "gap" and state != "resolved"):
            add(key, "explicit_blocker", node["content"])
        if node["origin"] == "repository" and not plan.source(key):
            add(key, "missing_provenance", "Link the repository observation to its source.")
        if kind in {"requirement", "acceptance"}:
            implementations = plan.linked(key, "^implements", "task", "component")
            behaviors = plan.linked(key, "requires", "behavior")
            if not implementations and not any(plan.linked(b, "^implements", "task", "component") for b in behaviors):
                add(key, "missing_implementation", "Link a planned task or component implementing this criterion.")
        if kind in {"decision", "assumption"} and not (justified or plan.source(key)
                                                       or plan.linked(key, "^supports")
                                                       or node["origin"] == "human"):
            add(key, "ungrounded_decision", "Link inspected evidence or provide a technical rationale.")
        if kind == "risk":
            if state == "applicable" and not plan.obligations(key):
                add(key, "uncovered_risk", "Define a verification obligation for the applicable risk.")
            elif state not in {"applicable", "blocked"} and not (state == "not_applicable" and justified):
                add(key, "risk_applicability", "Resolve applicability or justify why the risk is out of scope.")
        if kind == "api_contract":
            for facet, relation in (("request", "has_request"), ("response", "has_response"), ("error", "has_error")):
                exemptions = details.get("facet_exemptions", {})
                waiver = exemptions.get(facet) if isinstance(exemptions, dict) else None
                if not plan.linked(key, relation) and not (isinstance(waiver, str) and waiver.strip()):
                    add(key, "api_missing_" + facet, f"Model the {facet} contract or justify its absence.")
        if kind == "behavior":
            if not plan.scenarios(key) and not justified:
                add(key, "untested_behavior", "Link a scenario or justify the absence of a planned test.")
            methods = plan.linked(key, "requires", "method")
            if details.get("method_required") or methods:
                if not methods or any(not grounded_method(plan, method) for method in methods):
                    add(key, "missing_method", "Identify observed methods or link planned methods to implementation tasks.")
        if kind == "test_scenario":
            mapping = plan.mapping(key)
            if not mapping or not plan.assertions(key):
                add(key, "incomplete_scenario", "Define conditions, steps, expected outcome and assertions.")
            elif mapping["level"] != "manual" and not mapping["command"]:
                add(key, "missing_scenario_command", "Define the command for this automated scenario.")
        if kind == "assertion" and not nonempty_names(details.get("observables")):
            add(key, "assertion_missing_observable", "Specify the observable measured by this assertion.")
        if kind == "verification_obligation":
            check_obligation(plan, key, details, add)
        if kind == "task":
            check_task(plan, key, add, check_live_paths)

    targeted = {gap["node"] for gap in gaps}
    # A task consumes the criteria and methods it implements and the verification
    # it requires. Propagate blockers across those links and task prerequisites.
    for key in plan.kinds["task"]:
        related = set()
        for relation in ("implements", "requires", "verified_by", "mitigates", "covers"):
            related.update(plan.linked(key, relation))
        for node in tuple(related):
            if plan.nodes[node]["kind"] in {"acceptance", "requirement"}:
                related.update(plan.linked(node, "requires", "behavior"))
        for node in tuple(related):
            if plan.nodes[node]["kind"] == "behavior":
                related.update(set(plan.linked(node, "^threatens", "risk")) & targeted)
            related.update(plan.linked(node, "requires", "api_contract", "method", "gap"))
            related.update(plan.obligations(node))
            related.update(plan.scenarios(node))
        for node in tuple(related):
            related.update(plan.scenarios(node))
            related.update(plan.assertions(node))
        if related & targeted:
            add(key, "blocked_by_plan_gap", "Resolve related findings: " + ", ".join(sorted(related & targeted)) + ".")
    while True:
        affected = {key for key in plan.kinds["task"] - blocked
                    if blocked.intersection(plan.linked(key, "depends_on", "task"))}
        if not affected:
            break
        for key in affected:
            add(key, "blocked_dependency", "Resolve blocked prerequisite tasks.")
    return {
        "ready": not gaps,
        "gaps": sorted(gaps, key=lambda gap: (gap["node"], gap["code"])),
        "blocked_tasks": sorted(blocked),
        "ready_tasks": sorted(plan.kinds["task"] - blocked),
        "delivery": "unassessed",
        "recorded_evidence_count": db.execute("SELECT count(*) FROM evidence").fetchone()[0],
    }


def grounded_method(plan, method):
    node = plan.nodes[method]
    if node["state"] == "observed":
        return bool(plan.source(method))
    return node["state"] == "planned" and bool(plan.linked(method, "^implements", "task"))


def check_obligation(plan, key, details, add):
    required = details.get("observables")
    artifacts = details.get("artifacts")
    if not nonempty_names(required) or not nonempty_names(artifacts):
        add(key, "insufficient_evidence_contract", "Define required observable IDs and evidence artifacts.")
        return
    scenarios = plan.scenarios(key)
    required = set(required)
    missing = set(required)
    measured_anywhere = set()
    for scenario in scenarios:
        if not plan.mapping(scenario):
            continue
        measured = set()
        for assertion in plan.assertions(scenario):
            values = plan.nodes[assertion]["details"].get("observables")
            if nonempty_names(values):
                measured.update(values)
        measured_anywhere.update(measured)
        missing = min(missing, required - measured, key=lambda items: (len(items), sorted(items)))
    if details.get("observation_mode") == "independent":
        missing = required - measured_anywhere
    if missing:
        add(key, "inadequate_verification", "Planned assertions do not observe: " + ", ".join(sorted(missing)) + ".")


def check_task(plan, key, add, check_live_paths):
    task = plan.db.execute("SELECT * FROM task_details WHERE task_id=?", (key,)).fetchone()
    if task is None:
        add(key, "missing_task_details", "Define project, task kind, and operational mapping.")
        return
    links = plan.linked(key, "implements", "acceptance", "requirement", "behavior")
    obligations = plan.linked(key, "requires", "verification_obligation")
    if not links and not obligations:
        add(key, "untraced_task", "Link the task to behavior, acceptance or a verification obligation.")
    for (dst,) in plan.db.execute("SELECT dst FROM edges WHERE src=? AND relation='depends_on'", (key,)):
        if dst not in plan.nodes:
            add(key, "inactive_dependency", f"Replace retired prerequisite {dst}.")
    files = list(plan.db.execute("SELECT * FROM task_files WHERE task_id=?", (key,)))
    for file in files if check_live_paths else ():
        try:
            path = repository_path(task["project_root"], file["path"])
            if file["origin"] == "existing" and not path.is_file():
                raise ValueError("Existing file was not found")
            if file["origin"] == "new" and path.exists() and not path.is_file():
                raise ValueError("Planned file is occupied by a non-file entry")
        except (ValueError, OSError) as error:
            add(key, "ungrounded_task_path", f"{file['path']}: {error}")
    if not Path(task["project_root"]).is_absolute():
        add(key, "ungrounded_project", "Identify an absolute project root.")
    elif check_live_paths and not Path(task["project_root"]).is_dir():
        add(key, "ungrounded_project", "Identify an existing absolute project root.")
    if task["kind"] == "evidence":
        if not (plan.scenarios(key) or any(plan.scenarios(item) for item in obligations)):
            add(key, "missing_evidence_check", "Link an evidence task to a verification scenario.")
        return
    units = [file for file in files if file["role"] == "unit"]
    source = plan.db.execute("SELECT project_root FROM sources WHERE id=?", (task["runner_source"],)).fetchone()
    command = task["unit_command"]
    scenarios = [plan.mapping(test) for test in plan.scenarios(key)]
    if (not units or not command or not task["red"] or not task["green"]
            or not source or Path(source["project_root"]) != Path(task["project_root"])
            or not any(row and row["level"] == "unit" and row["command"] == command for row in scenarios)
            or re.search(r"[;&|<>\x00-\x1f]|\x60|\$\(", command)):
        add(key, "invalid_unit_mapping", "Map authorized unit files, a grounded focused unit scenario and RED/GREEN outcomes.")
