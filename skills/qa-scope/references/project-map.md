# Consult a published project map

For each target project, locate an existing `.project-mapper/graph.sqlite` and
a compatible installed Project Mapper `scripts/project_mapper.py`. Use the
public CLI in read-only offline mode from the project root:

```text
python "<mapper>" . --offline coverage --summary
python "<mapper>" . --offline search "<English concept or exact identifier>" --limit 10
python "<mapper>" . --offline node "<node key>"
python "<mapper>" . --offline open "<discovery ID>"
python "<mapper>" . --offline trace "<key>" --direction both --depth 2
```

In `plan`, follow relevant entrypoints, conditions, persistence, external
effects, tests and observation points. Inspect coverage and unresolved links.
When `context.sqlite` exists, inspect relevant acceptance, behavior and risk
nodes and their `details.project_mapper` references using the installed
New Scope CLI's `get` and `trace`, or read the database directly in read-only
mode. Retain source paths and symbols in `source_refs`; report the map snapshot,
graph SHA, relevant IDs and material limitations without changing the QA schema
or turning map findings into user-confirmed requirements.

In `check`, use these links to understand the planned behavior and what to
inspect. Judge the actual candidate, test definitions and recorded execution
observations against the published QA obligations. An earlier map snapshot is
not proof of the changed candidate or an executed test. Reopen decisive current
source and compare bytes with locator `content_id`; `sha256:` is a raw SHA-256,
while `git:` is the Git blob hash of `b"blob " + decimal_length + b"\0" +
bytes` (SHA-1 for 40 hex characters, SHA-256 for 64). An unverified static
relationship is only a candidate. Keep the same `graph_identity` snapshot and
SHA across related offline queries and restart if publication changes them.

Offline queries check stored graph integrity, not the live checkout or execution.
If the map or compatible CLI is absent, unreadable or incomplete, follow
`docs/README.md` and its index, inspect current source and tests, and report
material gaps. If docs are absent, use the root README, manifests and code.
Do not create or update a map as part of QA; map absence alone does not block a
conclusion supported by other evidence. Missing material evidence yields an
inconclusive assessment as described in the skill.
