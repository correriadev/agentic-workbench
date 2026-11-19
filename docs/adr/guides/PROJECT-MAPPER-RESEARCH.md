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
  - relation: references
    target: "adr:project-mapper-rea"
  - relation: references
    target: "adr:project-mapper-method"
  - relation: references
    target: "adr:project-mapper-validation"
updated: 2026-11-19
---
# Project Mapper Research

## OVERVIEW

Research conclusions and prototype recommendation. The proposed standalone `project-mapper` recovers software architecture from an inspectable checkout, persists a versioned graph, and emits bounded views. This is a new skill and schema, not a revision of Project Memory. No existing skill, CBM, REA, MCP server, or Jev is a runtime prerequisite. No prototype, mapping accuracy, or cost improvement has been verified in this research.

## RESEARCH CONCLUSIONS

1. **Recover several boundaries instead of discovering one hierarchy.** Start from the units the repo actually builds or runs. Recover behavior independently via contracts and reachable effects. Reconcile the two views without forcing every node into a single group. A deployment boundary and a business process answer different questions.
2. **Make source scope part of every negative answer.** Distinguish inventory coverage, relation-extraction coverage, and the portion exported to the reader. A page with no subscribers is not evidence that the repository has none. Neither is a partial extractor's empty graph.
3. **Separate semantic identity, source occurrence and observation.** Identical bytes can occur in two packages under different runtime or resolution rules. A move can change the evidence pointer without changing meaning. An unchanged consumer can acquire a new dependency when configuration or the repository inventory changes.
4. **Context selection is not evidence collection.** Produce factual records and typed edges first. A later ranking pass may decide which cards to show; it cannot upgrade an inferred edge to runtime evidence or delete a relevant but low-ranked dependency from the graph.

## WHAT TO BUILD FIRST

Start with a local SQLite schema, one source-language family and two contrasting, independently verified repository slices. Make four operations explicit: build a snapshot, refresh it, trace by edge type and direction, and export a bounded view. Do not begin with a multi-language indexer, vector search, autonomous runtime instrumentation, or a generalized incremental engine.

Keep the evidence and normalized graph local. Export compact cards plus source pointers, coverage and continuation. Make a contract lookup independent of the visible architectural branch, so a consumer in another service remains reachable after a higher-level prune. Use incremental extraction only after a clean build can recover the independently known edges and admit unknowns.

## DEEP DIVES

| Guide | Question it answers |
|---|---|
| [REA Evidence, Traversal and Versioning](PROJECT-MAPPER-REA.md) | Which machinery in the most extreme reference transfers to a source mapper, and what does the published evidence actually prove? |
| [Architecture Recovery Method](PROJECT-MAPPER-METHOD.md) | How should this skill infer architectural divisions, reconcile evidence and select lessons from the other repositories? |
| [Local Contract and Falsification](PROJECT-MAPPER-VALIDATION.md) | What must the first implementation store, invalidate, export and prove before measuring efficiency? |

## REFERENCES

- [Project Architecture](../ARCHITECTURE.md): skill autonomy and repository structure.
- [Testing Protocol](../TESTS.md): repository verification.
- [REA Evidence, Traversal and Versioning](PROJECT-MAPPER-REA.md): primary-source analysis.
- [Architecture Recovery Method](PROJECT-MAPPER-METHOD.md): comparative research.
- [Local Contract and Falsification](PROJECT-MAPPER-VALIDATION.md): experimental design.
