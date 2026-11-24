# Use a published project map

Read the existing `.project-mapper/graph.sqlite` with an installed compatible
Project Mapper CLI. Use the Git-free `--offline` mode throughout execution.
When the task supplies a committed revision, pass `--expect-revision COMMIT`
before the subcommand. Compare `graph_identity.sha256` and its snapshot across
related queries. Reopen the context if publication changes.

Start from the requested procedure or the files and verification commands
reported by `preflight TASK_ID`. When the New Scope CLI and database are available,
use `get TASK_ID` to inspect the selected spec task. Open the linked behavior,
risk or source nodes when they supply a decision you need for this phase.
Use `details.project_mapper` links to open or trace the relevant map records
directly. Otherwise search by an exact path, symbol or behavior terms. Use
`--terms` for English keywords with a natural-language question.

```text
python "<mapper>" . --offline search "<path, symbol or behavior terms>" --limit 5
python "<mapper>" . --offline open "<discovery ID>"
python "<mapper>" . --offline trace "<key>" --type "<relation>" --direction in --depth 1 --summary
python "<mapper>" . --offline coverage --area "<path or question>" --summary
```

Choose direction and relationship types for the question. Find callers or
tests on incoming edges and dependencies or effects on outgoing edges. Expand
when another hop may change the implementation or verification. Read `node`
when you need the node's own evidence and scope. Use targeted coverage for
gaps or truncation and global coverage for repository-wide questions.
For older compatible CLIs, use the available search and traversal limits and
compare the returned snapshot manually.

A partial map can still answer a focused question. When the map is unavailable
or omits decisive evidence, use `docs/README.md` and its index to find current
source and tests. Without docs, use the root README, manifests and adjacent
source. Keep unresolved impacts visible. Attribute map findings to their
scope and establish runtime or test outcomes from actual observations.

Compare decisive current source bytes with each locator's `content_id`.
Use New Scope's `source-ref --expect-content-id` when available. The hashes
can also be computed locally without Git. Use raw SHA-256 for `sha256:` and
hash `b"blob " + decimal_length + b"\0" + bytes` for `git:`, with SHA-1 for
40 hex characters or SHA-256 for 64. Reopen current files and tests before
editing. After a file changes, use current source to assess material impacts.

Use `files_allowed` and the current phase to determine which mapped files
can change. Reconcile a planned task that needs a different file, command or
prerequisite. In direct mode, present the revised scope before acting.
