# Use a published project map

For each project root, locate an installed compatible Project Mapper
`scripts/project_mapper.py` and an existing `.project-mapper/graph.sqlite`.
The map is optional. If absent, incompatible, incomplete or unreadable, follow
`docs/README.md` and its index; if docs are absent, use the root README,
manifests, source and tests. Report any material missing context.
Do not create, update or regenerate a map as part of Execute Scope's read-only context
step; those operations have separate write effects.

Use only the CLI's Git-free offline mode, from the target root:

```text
python "<mapper>" . --offline coverage --summary
python "<mapper>" . --offline search "<English concept or exact identifier>" --limit 10
python "<mapper>" . --offline node "<node key>"
python "<mapper>" . --offline open "<discovery ID>"
python "<mapper>" . --offline trace "<key>" --direction both --depth 2
```

In direct mode, use entrypoints, callers, conditions, adjacent tests, runners
and cross-boundary effects as leads for the plan. In planned mode, open the
task in the New Scope database, and trace its related behavior, risk and source
nodes; `tasks.json` intentionally does not copy all specification details. When
the New Scope CLI is available, run `python "<new-scope>/contract.py"
"<spec-folder>" get <task-id>` and `trace <task-id> --depth 3`, then `get`
relevant linked nodes. Otherwise inspect the same database read-only. Start
from any `details.project_mapper` references on those nodes; inspect the
relevant map discoveries, edges, source ranges and coverage. Ask what
else calls or depends on the modified behavior. Pass the responsible executor
the snapshot, graph SHA, relevant IDs, evidence locators and known gaps.

Each result includes `graph_identity`: snapshot, SHA-256, status and profile.
Offline mode checks stored graph integrity; it does not replay claims or check
the live checkout. Keep the same identity across related queries; restart if it
changes. Compare source bytes with the locator's `content_id`: `sha256:` is a
raw SHA-256; `git:` is the Git blob hash of `b"blob " + decimal_length + b"\0"
+ bytes`, using SHA-1 for 40 hex characters or SHA-256 for 64. Reopen decisive
current files and tests even when identities match. If a file changes during
implementation, the old map describes an earlier snapshot: inspect the current
code and report material unresolved impacts. Do not infer runtime execution,
test execution, or node-specific purpose from an unverified structural candidate
or a shared flow description. Respect truncated results and coverage gaps.

Map links identify leads, never write authorization. If a planned task needs a
different file, command or prerequisite, stop that task and reconcile the plan;
in direct mode present the changed scope before acting.
