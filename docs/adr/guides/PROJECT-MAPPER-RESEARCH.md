---
doc_type: adr
domain: architecture
stack: [markdown, sqlite]
node_id: "adr:project-mapper-research"
tags: [project-mapper, reverse-engineering, graph, provenance, incremental-indexing]
edges:
  - relation: references
    target: "adr:architecture"
  - relation: references
    target: "adr:tests"
updated: 2026-11-19
---
# Project Mapper Research

## OVERVIEW

Status: research and prototype proposal. The standalone `project-mapper` recovers architecture from inspectable artifacts, maintains a local versioned graph, and exports bounded views. Infer boundaries per repository; do not reuse Project Memory's schema.

## REA: WHAT THE REPOSITORY ACTUALLY DOES

Reviewed `morluto/rea` at [d865c776](https://github.com/morluto/rea/commit/d865c776463d3095b623b15a9cf6bb20793de228). The analysis below comes from maintained source, workflow documents, and a published example. It is not a new run or a claim about mapping accuracy on arbitrary repositories.

| Mechanism | Primary evidence and implication for Project Mapper |
|---|---|
| Evidence is a contract, not report prose. | [Evidence implementation](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/src/domain/evidence.ts#L395-L421) derives an ID from canonical content including subject, profile, operation, results, authority, locations, coverage and links; it excludes local display/request metadata. Reuse the separation, not the envelope: a stable logical node ID, an artifact occurrence (revision/path/hash) and a versioned observation ID serve different purposes. |
| Views and traversal are different operations. | [JavaScript workflows](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L1-L47) project summaries from retained evidence and keep structural and semantic graphs distinct. Shared provenance is factored out while exact locations remain per fact. Paginate the view without rereading source or discarding the canonical graph. Distinguish source coverage, known graph coverage and rows omitted from the view. |
| Trace by relationship and direction, not by folder. | [Feature tracing](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L145-L175) accepts typed seeds and prevents upward containment traversal from pulling in siblings. Apply this to routing, subscriptions and test discovery: crossing a contract boundary should not pull in the unrelated contents of the target service. |
| Presence, resolution and runtime observation differ. | [Evidence workflows](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/.agents/skills/reverse-engineer-anything/references/evidence-workflows.md) retain unknowns and separate structural reachability from causality. The [Notes Electron fixture](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/website/evidence/guide-examples.md#L9-L28) reports four parsed files, one literal IPC channel, one invocation and one paired handler, with no ambiguous invocations. The published record calls those edges static inferences; it does not claim the full click-to-file path ran. Model `resolves_to`, `candidate` and `observed in run` separately. |
| Equality of content is not equality of topology. | [Version comparison](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L385-L429) requires unique matches, distinguishes relocation from change, and keeps ambiguous relationships unknown even with equal module bytes. One-sided absence is a removal only if the opposite side was covered. Apply this to rename, alias changes, and newly discovered consumers. |

Use REA as a reference, not a dependency. Do not copy binary analysis, app capture, reconstruction or its toolchain. Static uncertainty stays open. Comparing snapshots is not evidence of incremental indexing.

## COMPLEMENTARY GITHUB RESEARCH

| Source | Adopt | Leave out |
|---|---|---|
| [Workbench Researcher](../../../skills/researcher/SKILL.md) | Orient first; investigate macro to micro; pass evidence pointers rather than whole sections. | Fixed 5×6 budget as an architecture model. Its structural gate checks paths and declared questions, not whether the excerpts support every claim or an undeclared area was missed. |
| [DiUS Codebase Discovery](https://github.com/DiUS/agent-toolkit/blob/main/skills/codebase-discovery/SKILL.md) | Code-only reconnaissance, declared-versus-implemented drift, review of unsupported findings, and scoped resume. | Interviews as a prerequisite and multiple mandatory Markdown reports. |
| [Software Architecture Analysis](https://github.com/magnus919/agent-skills/blob/main/software-architecture-analysis/SKILL.md) | Inspect component boundaries through code coupling, data ownership, deployment and workflows; keep the result tied to a revision. | Migration design and a diagram as the canonical map. |
| [ARCADE Core](https://github.com/usc-softarch/arcade_core) and [comparative study](https://jgarcia.ics.uci.edu/wp-content/uploads/arcade_msr_2015.pdf) | Separate dependency fact extraction from grouping. The work compares structural and concern-oriented recovery; test groupings against independently inspected facts. | Its external extractor/toolchain and any assumption that clustering recovers a unique architecture. |
| [ArchMapper](https://github.com/yannick-leguennec/archmapper), [reverse-spec](https://github.com/sinedied/agent-skills/blob/main/.agents/skills/reverse-spec/SKILL.md) | Bottom-up synthesis, restart checkpoints, checkable behavior. | Folder hierarchy, per-file model calls, full specs. |
| [Aider](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py), [Nx](https://github.com/nrwl/nx/blob/master/packages/nx/src/project-graph/build-project-graph.ts) | Cache extraction separately from presentation; associate dependency facts with their source and invalidate on relevant config changes. | Ranking before export, relying only on file mtime, or requiring Nx. |
| [GitNexus schema](https://github.com/abhigyanpatwari/GitNexus/blob/main/gitnexus/skills/gitnexus-guide.md) and [AsyncAPI operations](https://github.com/asyncapi/spec/blob/master/spec/asyncapi.md#operation-object) | Typed graph edges and directional messaging identities. Verify channel, message and registration rather than joining by a similar name. | Their runtimes and requiring OpenAPI or AsyncAPI to be present. |
| [Bazel Skyframe](https://github.com/bazelbuild/bazel/blob/master/docs/reference/skyframe.mdx) and [Salsa](https://github.com/salsa-rs/salsa/blob/master/book/src/reference/algorithm.md) | Treat directory membership as an input; skip dependent synthesis if the normalized facts did not change. | A custom incremental query engine for the first prototype. |

## PROPOSED LOCAL CONTRACT

1. **Discover in two directions.** Seed candidate boundaries from manifests, runtime units, CI, routes and registrations; recover symbol-to-contract-to-effect flows from local sources. Preserve declared and observed architecture separately. Keep cross-cutting memberships and unassigned units. Do not require every repo to have a service, database, broker or layered layout.
2. **Store once, query in multiple ways.** Start with SQLite tables for revision, artifact occurrence, node, relationship, evidence, and view membership. Index relations in both directions. A single consumer can belong to a process and a deployment unit without duplicate facts. Keep evidence pointers, source class, resolution status and gaps; keep raw credentials and source dumps out of exports.
3. **Refresh facts and locators separately.** Diff the inventory; reuse extraction by content and extractor version. Recompute joins against the active inventory and resolver configuration. Update locators even when summarized behavior is unchanged. Keep observations tied to their own snapshot; do not promote a previously uninspected frontier to absence.
4. **Expose build, update, and export.** Emit machine-readable cards scoped to one revision, with explicit examined scope, unresolved relations, and pagination. Give a layer consumer the initial architectural groups without semantic preselection, and let it expand IDs or query a typed contract directly. The consumer's discard decisions never mutate the stored graph. No Jev calls are required to build or query it.

## FALSIFICATION PLAN

- **Architecture:** recover contrasting bounded slices in [e2e-boilerplate](https://github.com/correriadev/e2e-boilerplate) (runner/diagnostic/report) and [dotnet/eShop](https://github.com/dotnet/eShop) (ordering routes and event registrations). Freeze independent expected facts. Rename a folder without changing responsibilities; the map must not collapse into a directory tree.
- **Coverage:** put a consumer across a group boundary and an identically named one on another channel. Recover the former and exclude the decoy. With missing resolver configuration or a truncated frontier, return partial rather than asserting absence.
- **Incrementality:** add/remove a consumer or test without modifying its producer; retarget an alias while leaving callers intact; insert a comment before a handler. Compare incremental and clean rebuild facts, links, locators and gaps on the same revision. Never retain a stale path or edge. Reuse the semantic card for a nonsemantic edit when its facts and relationships are unchanged.
- **Measure only after correctness:** compare cold and warm extraction work, regenerated cards, exported tokens and elapsed time. Prior synthetic Jev trials do not benchmark this skill. No measured gains are claimed.

## REFERENCES

- [Project Architecture](../ARCHITECTURE.md): self-contained skill boundaries.
- [Testing Protocol](../TESTS.md): repository validation and evidence conventions.
