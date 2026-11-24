# Use a published project map

Read the existing `.project-mapper/graph.sqlite` with the installed Project
Mapper CLI in offline mode. Locate that CLI independently of New Scope's
installation. When the intended committed revision is known from the task
context, pass `--expect-revision COMMIT` before the subcommand. Across related
queries compare `graph_identity.sha256` and its snapshot. Restart a batch if its
publication changes.

Begin with the exact endpoint, path, symbol or English behavior terms relevant
to a scope decision. Locate the affected contract, observable effects and
nearby tests. Use `--terms` for English keywords with a natural-language
question. Open a discovery for its conditions and source ranges. Use a typed,
shallow `trace --summary` when the question needs relationships. Expand only
where a material continuation remains. For older compatible CLIs use the
available search and depth controls and compare the returned snapshot manually.

```text
python "<mapper>" . --offline search "<identifier or English behavior terms>" --limit 5
python "<mapper>" . --offline open "<discovery ID>"
python "<mapper>" . --offline trace "<key>" --type "<relation>" --direction out --depth 1 --summary
python "<mapper>" . --offline coverage --area "<path or question>" --summary
```

Use `node` when you need that node's evidence or subject-specific context.
Request global coverage or dimensions when the decision needs repository-wide
breadth. Inspect relevant gaps, truncation, candidate relationships and
conflicting sources. Attribute findings to the subject or flow they describe.
Support absence claims with scoped coverage and current sources.
Coverage can be partial overall and sufficient for an
individual lookup. Use `docs/README.md` and its index for questions the graph
leaves open or when the map or CLI is absent, stale, unreadable or incompatible.
If docs are unavailable, start from the root README, manifests and current
sources. Use static facts to locate behavior and test definitions. Runtime,
deployment and test execution claims require their own observations.

For each decisive locator, use [source-ref](graph-cli.md#current-source-references)
with its path, inclusive line range and `--expect-content-id`. Inspect the
source in that range. A revision match pins the published snapshot. A content
ID match checks the current file bytes. When a file differs, consult its current
version and record a new source reference for the inspected lines.

Record relevant map snapshot, graph SHA, node/discovery ID, relation, conditions
and limitations in the affected specification node's `details.project_mapper`.
Link the inspected current `sources` through `node_sources`. Keep the map's
conditions and limitations attached to the claim they qualify. Use observed
repository nodes for established facts, planned nodes for proposed changes,
and hypotheses or gaps for evidence still needed. Identify the affected
acceptance criterion, the observable effect and its test or runner. Block work
that depends on an unresolved gap.
