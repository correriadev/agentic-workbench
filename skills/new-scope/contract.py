#!/usr/bin/env python3
"""Write and query one New Scope specification using only Python and SQLite."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile

sys.dont_write_bytecode = True

from completeness import assess, coverage, repository_path, structural_checks
from execute_export import export_execute_scope

SCHEMA = Path(__file__).with_name("schema.sql")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,127}")
# Fixed SQL identifiers and column order. JSON on stdin is data only.
TABLES = {
    "nodes": ("id kind title content state origin details", 1),
    "sources": ("id project_root path symbol line_start line_end version sha256 excerpt", 1),
    "node_sources": ("node_id source_id", 2),
    "edges": ("src relation dst rationale", 3),
    "task_details": ("task_id project_root kind unit_command runner_source red green", 1),
    "task_files": ("task_id path origin role", 2),
    "verification_cases": ("scenario_id level conditions steps expected command", 1),
    "evidence": ("id scenario_id plan_revision candidate environment observed_at command "
                 "exit_code observations artifact", 1),
}
IMMUTABLE = {"sources", "evidence"}
JSON_FIELDS = {"details", "observations"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def rows(db, sql, args=()):
    return [dict(row) for row in db.execute(sql, args)]


def metadata(db):
    return dict(db.execute("SELECT change_id, revision FROM spec_meta").fetchone())


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"Invalid identifier: {value!r}")


def source_bytes(root, path):
    target = repository_path(root, path)
    if not target.is_file():
        raise ValueError(f"Source must be a regular file: {path}")
    return target.read_bytes()


def source_ref(args, root):
    identifier(args.node)
    if not args.path:
        raise ValueError("source-ref requires a project-relative --path")
    if args.symbol is not None and not args.symbol.strip():
        raise ValueError("Source symbol must be nonempty text")
    if args.excerpt and not args.lines:
        raise ValueError("--excerpt requires an explicit --lines START END range")
    data = source_bytes(root, args.path)
    digest = hashlib.sha256(data).hexdigest()
    record = dict(id=args.node, project_root=str(root), path=args.path, sha256=digest)
    if args.expect_content_id is not None:
        expected = args.expect_content_id.lower()
        if re.fullmatch(r"sha256:[0-9a-f]{64}", expected):
            actual = f"sha256:{digest}"
        elif re.fullmatch(r"git:(?:[0-9a-f]{40}|[0-9a-f]{64})", expected):
            blob = hashlib.new("sha1" if len(expected.removeprefix("git:")) == 40 else "sha256")
            blob.update(f"blob {len(data)}\0".encode("ascii"))
            blob.update(data)
            actual = f"git:{blob.hexdigest()}"
        else:
            raise ValueError("--expect-content-id requires a Git blob or raw SHA-256 content ID")
        if actual != expected:
            raise ValueError(f"Source content changed: {args.path} differs from the expected content ID")
        record["version"] = actual
    if args.symbol is not None:
        record["symbol"] = args.symbol
    if args.lines:
        start, end = args.lines
        lines = data.decode(errors="replace").splitlines()
        if not 1 <= start <= end <= len(lines):
            raise ValueError("Source line range exceeds file or has invalid bounds")
        record.update(line_start=start, line_end=end)
        if args.excerpt:
            excerpt = "\n".join(lines[start - 1:end])
            if excerpt.strip():
                record["excerpt"] = excerpt
    return record


def check_row(table, row, revision):
    for key in ("id", "src", "dst", "task_id", "scenario_id", "node_id", "source_id",
                "runner_source"):
        if row.get(key) is not None:
            identifier(row[key])
    for key, value in row.items():
        if value is None or key in JSON_FIELDS:
            continue
        if key in {"line_start", "line_end", "plan_revision", "exit_code"}:
            if type(value) is not int:
                raise ValueError(f"{table}.{key} must be an integer")
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f"{table}.{key} must be nonempty text")

    if table == "nodes" and not isinstance(row.get("details", {}), dict):
        raise ValueError("Node details must be an object")
    if table == "sources":
        data = source_bytes(row["project_root"], row["path"])
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"Source content changed: {row['path']}")
        if row.get("line_end") or row.get("excerpt"):
            lines = data.decode(errors="replace").splitlines()
            end = row.get("line_end")
            if end and end > len(lines):
                raise ValueError("Source line range exceeds file")
            if row.get("excerpt") and row["excerpt"] not in "\n".join(lines[(row.get("line_start") or 1) - 1:end]):
                raise ValueError("Source excerpt does not match observed content")
    if table == "evidence":
        if not 0 < row["plan_revision"] <= revision or not isinstance(row["observations"], dict) or not row["observations"]:
            raise ValueError("Evidence requires structured observations and a prior plan revision")


def apply(db, proposed, expected):
    if not isinstance(proposed, dict) or set(proposed) - (TABLES.keys() | {"request_id", "reason", "remove_edges"}):
        raise ValueError("Unknown apply field")
    request_id, reason = proposed["request_id"], proposed["reason"]
    identifier(request_id)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Revision reason is required")
    digest = hashlib.sha256(encode(proposed).encode()).hexdigest()
    db.execute("BEGIN IMMEDIATE")
    current = metadata(db)["revision"]
    prior = db.execute("SELECT revision, digest FROM history WHERE request_id=?", (request_id,)).fetchone()
    if prior:
        if prior["digest"] != digest:
            raise ValueError("Request ID already used with different changes")
        return {**metadata(db), "applied_revision": prior["revision"]}
    if current != expected:
        raise ValueError(f"Stale revision: expected {expected}, current {current}")
    changes = []
    seen = set()
    revision = current + 1
    for table, (field_names, key_count) in TABLES.items():
        fields = field_names.split()
        keys = fields[:key_count]
        where = " AND ".join(f"{key}=?" for key in keys)
        entries = proposed.get(table, [])
        if not isinstance(entries, list):
            raise ValueError(f"{table} must be a list")
        for row in entries:
            if not isinstance(row, dict) or row.keys() - set(fields):
                raise ValueError(f"Unknown {table} fields")
            key = tuple(row[name] for name in keys)
            if (table, key) in seen:
                raise ValueError(f"Duplicate {table} key: {key}")
            seen.add((table, key))
            after = {name: row.get(name) for name in fields}
            if table == "nodes":
                after["details"] = row.get("details", {})
            for field in JSON_FIELDS & after.keys():
                after[field] = encode(after[field])
            before = db.execute(f"SELECT * FROM {table} WHERE {where}", key).fetchone()
            before = dict(before) if before else None
            if before == after:
                continue
            if before and (table in IMMUTABLE or
                           (table == "nodes" and (before["kind"] in {"evidence", "decision"}
                            or before["kind"] != after["kind"] or before["origin"] != after["origin"]
                            or (before["state"] == "confirmed" and after["state"] != "confirmed")))):
                raise ValueError(f"Immutable record or identity: {table} {key}")
            check_row(table, row, current)
            if table == "evidence":
                verify_observation(db, row)
            values = tuple(after.values())
            assignments = ", ".join(f"{name}=excluded.{name}" for name in fields[key_count:])
            conflict = f"DO UPDATE SET {assignments}" if assignments else "DO NOTHING"
            db.execute(f"INSERT INTO {table} ({','.join(fields)}) "
                       f"VALUES ({','.join('?' for _ in fields)}) ON CONFLICT "
                       f"({','.join(keys)}) {conflict}", values)
            changes.append({"table": table, "before": before, "after": after})
    for edge in proposed.get("remove_edges", []):
        if set(edge) != {"src", "relation", "dst"}:
            raise ValueError("Edge removals require src, relation and dst")
        key = (edge["src"], edge["relation"], edge["dst"])
        if ("edges", key) in seen:
            raise ValueError("Cannot write and remove the same edge")
        before = db.execute("DELETE FROM edges WHERE src=? AND relation=? AND dst=? RETURNING *", key).fetchone()
        if before:
            changes.append({"table": "edges", "before": dict(before), "after": None})
    structural_checks(db)
    if not changes:
        raise ValueError("No changes to apply; reuse the original request ID for a retry")
    db.execute("INSERT INTO history(revision, request_id, digest, reason, changes) VALUES (?,?,?,?,?)",
               (revision, request_id, digest, reason, encode(changes)))
    db.execute("UPDATE spec_meta SET revision=?", (revision,))
    return metadata(db)


def verify_observation(db, record):
    # Evidence may only refer to a scenario and command that existed in the
    # recorded revision, even if the current plan has since changed.
    scenario = record["scenario_id"]
    for revision in db.execute("SELECT changes FROM history WHERE revision<=? ORDER BY revision DESC",
                               (record["plan_revision"],)):
        for change in json.loads(revision["changes"]):
            after = change["after"]
            if change["table"] == "verification_cases" and after["scenario_id"] == scenario:
                if after["command"] != record["command"]:
                    raise ValueError("Evidence command differs from its recorded plan")
                return
    raise ValueError("Evidence scenario missing from its recorded revision")


def get(db, node_id):
    found = rows(db, "SELECT * FROM nodes WHERE id=?", (node_id,))
    if not found:
        raise ValueError(f"Unknown node: {node_id}")
    node = found[0]
    node["details"] = json.loads(node["details"])
    node["sources"] = rows(db, "SELECT s.* FROM sources s JOIN node_sources ns ON ns.source_id=s.id "
                          "WHERE ns.node_id=? ORDER BY s.id", (node_id,))
    node["edges"] = rows(db, "SELECT * FROM edges WHERE src=? OR dst=? ORDER BY src, relation, dst",
                         (node_id, node_id))
    node["task"] = rows(db, "SELECT * FROM task_details WHERE task_id=?", (node_id,))
    node["files"] = rows(db, "SELECT * FROM task_files WHERE task_id=? ORDER BY path", (node_id,))
    node["verification"] = rows(db, "SELECT * FROM verification_cases WHERE scenario_id=?", (node_id,))
    node["observations"] = rows(db, "SELECT * FROM evidence WHERE id=? OR scenario_id=? ORDER BY id",
                                (node_id, node_id))
    for record in node["observations"]:
        record["observations"] = json.loads(record["observations"])
    return node


def traverse(db, node_id, depth, limit, impact):
    if not db.execute("SELECT 1 FROM nodes WHERE id=?", (node_id,)).fetchone():
        raise ValueError(f"Unknown node: {node_id}")
    visited, frontier, results = {node_id}, {node_id}, []
    for hop in range(1, depth + 1):
        following = set()
        for origin in sorted(frontier):
            links = rows(db, "SELECT * FROM edges WHERE src=? OR dst=? ORDER BY src, relation, dst",
                         (origin, origin))
            for link in links:
                reverse = link["dst"] == origin
                other = link["src"] if reverse else link["dst"]
                if impact and not impact_direction(link["relation"], reverse):
                    continue
                if other in visited:
                    continue
                following.add(other)
                if len(results) == limit:
                    return {"links": results, "truncated": True}
                node = dict(db.execute("SELECT id,kind,title,state FROM nodes WHERE id=?", (other,)).fetchone())
                results.append({"hop": hop, **link, "node": node})
        visited |= following
        frontier = following
        if not frontier:
            break
    return {"links": results, "truncated": False}


def impact_direction(relation, reverse):
    upstream = {"implements", "depends_on", "covers", "supports", "mitigates", "references", "consumes"}
    downstream = {"requires", "verified_by", "produces", "has_request", "has_response",
                  "has_error", "has_assertion", "threatens"}
    if relation == "requires":
        return True
    return relation in (upstream if reverse else downstream)


def scope_text(db):
    meta = metadata(db)
    report = assess(db, check_live_paths=False)
    result = [f"# {meta['change_id']}", "", f"Database revision: {meta['revision']}",
              f"Structural planning status: {'ready' if report['ready'] else 'blocked'}", ""]
    sections = {
        "Objective": ("intent",),
        "Scope and constraints": ("requirement", "constraint", "business_rule"),
        "Acceptance criteria": ("acceptance",),
        "Assumptions and decisions": ("assumption", "decision"),
        "Risks": ("risk",),
        "Open questions and gaps": ("gap",),
        "Implementation plan": ("task",),
    }
    for heading, kinds in sections.items():
        result.extend((f"## {heading}", ""))
        for node in rows(db, "SELECT * FROM nodes WHERE kind IN (" + ",".join("?" for _ in kinds)
                         + ") AND state <> 'superseded' AND id NOT IN "
                           "(SELECT dst FROM edges WHERE relation='supersedes') ORDER BY id", kinds):
            result.append(f"- **{node['id']} — {node['title']}** ({node['state']}): {node['content']}")
        result.append("")
    if report["gaps"]:
        result.extend(("## Validation findings", ""))
        for gap in report["gaps"]:
            result.append(f"- `{gap['node']}` — {gap['code']}: {gap['message']}")
        result.append("")
    return "\n".join(result)


def render(db, folder):
    output = folder / "SCOPE.md"
    with tempfile.NamedTemporaryFile(dir=folder, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        temporary.write_text(scope_text(db), encoding="utf-8")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return {"revision": metadata(db)["revision"], "path": str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("operation", choices=("init", "apply", "inspect", "get", "trace", "impact", "source-ref",
                                              "coverage", "gaps", "validate", "render-scope",
                                              "export-execute-scope", "export-forge"))
    parser.add_argument("node", nargs="?")
    parser.add_argument("--expect", type=int)
    parser.add_argument("--depth", type=int, default=6, choices=range(1, 21))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--path", help="project-relative file for source-ref")
    parser.add_argument("--project-root", type=Path, help="source-ref target when it differs from the spec root")
    parser.add_argument("--symbol", help="source symbol for source-ref")
    parser.add_argument("--lines", nargs=2, type=int, metavar=("START", "END"), help="inclusive source-ref lines")
    parser.add_argument("--expect-content-id", help="verify the source against a Project Mapper locator")
    parser.add_argument("--excerpt", action="store_true", help="include the text of the selected source-ref lines")
    args = parser.parse_args()
    folder = args.folder.absolute()
    if (folder.parent.name != "specs" or folder.parent.parent.name != "docs"
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", folder.name)
            or folder.resolve() != folder):
        raise ValueError("Use a non-symlink docs/specs/<kebab-case-change-id> directory")
    operation = args.operation
    if operation == "source-ref":
        root = args.project_root.resolve() if args.project_root is not None else folder.parents[2]
        print(encode(source_ref(args, root)))
        return 0
    if (args.excerpt or any(value is not None for value in
                            (args.path, args.project_root, args.symbol, args.lines, args.expect_content_id))):
        raise ValueError("Source options are supported only by source-ref")
    path = folder / "context.sqlite"
    if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_nlink != 1)):
        raise ValueError("Database must be a regular file owned by this specification")
    if operation == "init":
        folder.mkdir(parents=True, exist_ok=True)
    writable = operation in {"init", "apply", "render-scope"}
    mode = "rwc" if operation == "init" else "rw" if writable else "ro"
    with closing(sqlite3.connect(f"{path.as_uri()}?mode={mode}", uri=True)) as db, db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        if operation == "init":
            db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA.read_text(encoding="utf-8"))
            db.execute("INSERT OR IGNORE INTO spec_meta(singleton, change_id) VALUES (1,?)", (folder.name,))
        elif operation not in {"apply", "render-scope"}:
            db.execute("BEGIN")
        if operation == "render-scope":
            db.execute("BEGIN IMMEDIATE")
        if metadata(db)["change_id"] != folder.name:
            raise ValueError("Database change ID does not match its specification directory")

        if operation == "apply":
            if args.expect is None:
                raise ValueError("apply requires --expect with the revision read before planning")
            result = apply(db, json.load(sys.stdin), args.expect)
        elif operation in {"init", "inspect"}:
            result = metadata(db)
            if operation == "inspect":
                scope = folder / "SCOPE.md"
                result["scope_current"] = (scope.is_file() and not scope.is_symlink()
                                           and scope.read_text(encoding="utf-8") == scope_text(db))
        elif operation == "get":
            result = get(db, args.node)
        elif operation in {"trace", "impact"}:
            if not 1 <= args.limit <= 500:
                raise ValueError("Use a traversal limit between 1 and 500")
            result = traverse(db, args.node, args.depth, args.limit, operation == "impact")
        elif operation == "render-scope":
            result = render(db, folder)
        elif operation == "coverage":
            result = coverage(db, args.node)
        elif operation in {"export-execute-scope", "export-forge"}:
            scope = folder / "SCOPE.md"
            if scope.is_symlink() or not scope.is_file() or scope.read_bytes() != scope_text(db).encode():
                raise ValueError("Render the current New Scope scope before exporting")
            result = export_execute_scope(db, folder, metadata(db), scope.read_bytes())
        else:
            result = assess(db)
            if operation == "validate":
                problems = [row[0] for row in db.execute("PRAGMA integrity_check") if row[0] != "ok"]
                problems.extend("Foreign key violation: " + str(tuple(row))
                                for row in db.execute("PRAGMA foreign_key_check"))
                structural_checks(db)
                result["integrity"] = problems
                result["ready"] = result["ready"] and not problems
        db.commit()
    print(encode(result))
    return int(operation == "validate" and not result["ready"])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, TypeError, sqlite3.Error) as error:
        sys.exit(str(error))
