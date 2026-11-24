# Consult a published project map

Read an existing `.project-mapper/graph.sqlite` with the installed Project Mapper
CLI in offline mode. Use `--expect-revision COMMIT` before the subcommand when
the intended mapped commit is known. Compare the `graph_identity.sha256` and
snapshot across related queries and restart if publication changes.

In `plan`, start from a material risk or acceptance criterion. Use the linked
`details.project_mapper` records when the New Scope specification supplies them.
Otherwise search by an exact path, symbol or English behavior terms. Use
`--terms` for English keywords with a natural-language question. Open the
relevant discovery for conditions and evidence locators. Use a typed,
shallow `trace --summary` when the risk depends on a call, transaction boundary,
external effect or test relationship.

```text
python "<mapper>" . --offline search "<path, symbol or behavior terms>" --limit 5
python "<mapper>" . --offline open "<discovery ID>"
python "<mapper>" . --offline trace "<key>" --type "<relation>" --direction out --depth 1 --summary
python "<mapper>" . --offline coverage --area "<path or question>" --summary
```

Choose incoming edges for tests or callers and outgoing edges for effects
and dependencies. Expand only when another hop can change the evidence
requirement. Use `node` for its own evidence and targeted coverage for
material gaps or truncation. For older compatible CLIs, use their
available search and traversal limits and compare the snapshot manually.
Record current source paths and symbols or line ranges in `source_refs`.
Keep the map identity and limitations with the planning rationale.

In `check`, start with the published obligation and the candidate's evidence.
Use map links to find decisive test definitions, configurations and observation
points. Inspect those current sources. Compare each relied-on locator's
`content_id` using New Scope's `source-ref --expect-content-id` when available.
For a local check, `sha256:` hashes raw bytes and `git:` hashes
`b"blob " + decimal_length + b"\0" + bytes` using SHA-1 for 40 hex characters
or SHA-256 for 64. Base the verdict on the actual candidate and recorded
observations from the planned scenario.

A globally partial map can support an individual lookup. Use
`docs/README.md` and its index when the map or CLI is unavailable or leaves
a material question open. Without docs, use the root README, manifests,
source and tests. Keep the map read-only and record missing material evidence
in the finding.
