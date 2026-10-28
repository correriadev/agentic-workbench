"""Controlled investigation; does not modify the skill or project memory.

Run: python -B docs/specs/otimizacao_project_memory/experimento.py
Results are synthetic, not an agent benchmark or production evidence.
"""
import hashlib
import json
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/authored/project-memory"
sys.path.insert(0, str(SKILL / "scripts"))
from generate_docs_graph import build_docs_graph, parse_markdown_file
from validate_ontology import Validator


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def document(root, name, source=None, premise=None, statement="Fixture observation", extra=""):
    graph = dict(node_id=f"feature:{name}", domain="fixture", implements=[], tested_by=[],
                 entrypoints=[], registration_files=[], reference_files=[], code_files=[], test_files=[])
    if source:
        graph["knowledge"] = dict(schema_version=1,
            entities=[dict(id="capability:run", type="capability", label="Run", definition="Fixture", aliases=[])],
            claims=[dict(id="claim:run", subject="capability:run", relation=None, object=None,
                         statement=statement, kind="observation", status="supported",
                         evidence=[dict(kind="code", source=source, locator="run", snapshot="old-revision")],
                         derived_from=[premise] if premise else [], gap=None)])
    path = root / "docs/feature" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ndoc_type: feature\ndomain: fixture\nstack: [python]\nnode_id: feature:{name}\ntags: [fixture, run]\nedges: []\nupdated: 2026-10-28\n---\n```graph\n{compact(graph)}\n```\n# {name}\n{extra}", encoding="utf-8")
    return path


def publish(root):
    graph = build_docs_graph(root / "docs")
    graph["related_projects"] = []
    (root / "docs/.graph.json").write_text(compact(graph), encoding="utf-8")
    return graph


def measured(operation):
    counts = dict(reads=0, characters=0, file_checks=0)
    read, exists = Path.read_text, Path.is_file
    def counted_read(path, *args, **kwargs):
        value = read(path, *args, **kwargs)
        counts["reads"] += 1
        counts["characters"] += len(value)
        return value
    def counted_exists(path):
        counts["file_checks"] += 1
        return exists(path)
    with patch.object(Path, "read_text", counted_read), patch.object(Path, "is_file", counted_exists):
        start = time.perf_counter()
        value = operation()
        counts["milliseconds"] = (time.perf_counter() - start) * 1000
    return value, counts


def main():
    fingerprints = {p.relative_to(SKILL).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    result = dict(environment=dict(python=platform.python_version(), platform=platform.platform()),
                  skill_sha256=fingerprints, repetitions=3, scale=[], probes={})
    for size in (10, 100, 500):
        with tempfile.TemporaryDirectory(prefix="project-memory-investigation-") as directory:
            root = Path(directory)
            for number in range(size):
                document(root, f"f{number:04}")
            publish(root)
            target = root / "docs/feature/f0000.md"
            old_projection = parse_markdown_file(target, root)
            document(root, "f0000", extra="Editorial change; routing unchanged.")
            def baseline():
                graph = publish(root)
                return graph, Validator(root / "docs").validate(["feature:f0000"])
            def candidate():
                # Experimental no-op guard, requires a known previous projection.
                assert parse_markdown_file(target, root) == old_projection
                graph = json.loads((root / "docs/.graph.json").read_text(encoding="utf-8"))
                return graph, Validator(root / "docs").validate(["feature:f0000"])
            measurements = dict(baseline=[], candidate=[])
            for repetition in range(3):
                order = (baseline, candidate) if repetition % 2 == 0 else (candidate, baseline)
                values = {}
                for operation in order:
                    value, stats = measured(operation)
                    measurements[operation.__name__].append(stats)
                    values[operation.__name__] = value
                assert values["baseline"] == values["candidate"]
            result["scale"].append(dict(documents=size, graph_characters=len(compact(values["baseline"][0])),
                equivalent=True, graph_writes=dict(baseline=3, candidate=0), measurements=measurements))
    with tempfile.TemporaryDirectory(prefix="project-memory-probes-") as directory:
        root = Path(directory)
        (root / "src").mkdir()
        source = root / "src/run.py"
        source.write_text("def run():\n    return False\n", encoding="utf-8")
        document(root, "a", "src/run.py", statement="run returns True")
        document(root, "b", "src/run.py", premise="feature:a#claim:run")
        document(root, "c", "src/run.py", statement="run returns False")
        publish(root)
        result["probes"]["contradictory_claims_accepted"] = Validator(root / "docs").validate()
        source.rename(root / "src/renamed.py")
        publish(root)
        result["probes"]["renamed_evidence_accepted"] = Validator(root / "docs").validate()
        (root / "src/renamed.py").unlink()
        publish(root)
        result["probes"]["deleted_evidence_accepted"] = Validator(root / "docs").validate()
        result["probes"]["targeted_a_does_not_visit_dependent_b"] = Validator(root / "docs").validate(["feature:a"])
        assert result["probes"]["targeted_a_does_not_visit_dependent_b"]["documents_checked"] == 1
        document(root, "oversized", extra="x" * 10001)
        publish(root)
        result["probes"]["oversized_accepted"] = Validator(root / "docs").validate(["feature:oversized"])
        unrelated = document(root, "unrelated")
        unrelated.write_text(unrelated.read_text(encoding="utf-8").replace('"entrypoints":[]', '"entrypoints":["src/missing.py"]'), encoding="utf-8")
        try:
            publish(root)
        except ValueError as error:
            result["probes"]["unrelated_stale_route_blocks_build"] = str(error).replace(str(root), "FIXTURE")
        else:
            raise AssertionError("Missing routing path should fail")
    assert all(hashlib.sha256((SKILL / path).read_bytes()).hexdigest() == digest for path, digest in fingerprints.items())
    output = Path(__file__).with_name("resultados.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in result["scale"]:
        print(row["documents"], row["graph_characters"], {
            name: dict(ms_median=round(statistics.median(v["milliseconds"] for v in samples), 2),
                       ms_range=[round(min(v["milliseconds"] for v in samples), 2), round(max(v["milliseconds"] for v in samples), 2)],
                       reads=samples[0]["reads"], characters=samples[0]["characters"], file_checks=samples[0]["file_checks"])
            for name, samples in row["measurements"].items()})
    print(json.dumps(result["probes"], ensure_ascii=False))
    print("Skill hashes unchanged; results:", output)


if __name__ == "__main__":
    main()
