# Use a published project map

For each target root, use an existing `.project-mapper/graph.sqlite` when a
compatible Project Mapper CLI is available. Find its installed `scripts/project_mapper.py`;
do not assume this skill's installation is adjacent. This optional read does not
authorize creating or updating the map. If either is absent, unreadable or
incompatible, report the limitation and investigate sources directly.

From the target root, use Python 3.12+ and the CLI's read-only offline mode:

```text
python "<mapper>" . --offline coverage --summary
python "<mapper>" . --offline dimensions --summary
python "<mapper>" . --offline search "<English concept or exact identifier>" --limit 10
python "<mapper>" . --offline node "<structural node key>"
python "<mapper>" . --offline open "<discovery ID>"
python "<mapper>" . --offline trace "<key>" --direction both --depth 2
```

Begin with scope-specific questions: entrypoints and callers, conditions and
variants, persistence and external effects, affected interfaces, neighboring
tests and runner configuration. Search using English concepts and original
identifiers. Open relevant discoveries, traverse both directions selectively,
follow material continuations and inspect `coverage --area <path-or-question>`.
Inspect truncation, unresolved targets, candidate relationships, discrepancies
and boundaries; an empty search does not establish absence. Follow source locators
for each consequential statement. A flow discovery does not by itself assign its
role to every linked node. A static candidate does not establish a runtime call,
deployed state or an executed test.

Offline queries return `graph_identity` with a graph SHA-256, snapshot, status
and profile. They check stored graph integrity but do not verify the snapshot
against the current working tree or replay evidence. Keep the graph SHA and
snapshot consistent across queries; restart if publication changes either.
Treat old or unverified maps as leads, including after edits. Compare decisive
current source bytes to the locator's `content_id`: `sha256:` hashes raw bytes;
`git:` hashes `b"blob " + decimal_length + b"\0" + bytes` with SHA-1 for a
40-character ID or SHA-256 for a 64-character ID. Missing, changed or unreadable
sources require direct investigation, not a freshness claim.

Record relevant map snapshot, graph SHA, node/discovery ID, relation, conditions
and limitations in the affected specification node's `details.project_mapper`.
Attach ordinary `sources` and `node_sources` for each supporting current file,
with path, symbol, lines and its raw SHA-256 as required by the Blueprint CLI.
Keep conflicting findings attributed. Record material unresolved evidence as a
gap or hypothesis and block only dependent work; do not copy the whole map or
turn mapper content into a confirmed human decision.
