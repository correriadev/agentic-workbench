---
doc_type: adr
domain: architecture
stack: [markdown, sqlite]
node_id: "adr:project-mapper-method"
tags: [project-mapper, architecture-recovery, discovery, graph]
edges:
  - relation: references
    target: "adr:project-mapper-research"
  - relation: references
    target: "adr:project-mapper-rea"
updated: 2026-11-19
---
# Architecture Recovery Method

## RESEARCH BASIS

These are techniques found in project source, skill prompts, research papers, and published documentation. They are not interchangeable products or benchmark results. Borrow the methods, not their runtimes.

| Reference | What it does | Rule for Project Mapper |
|---|---|---|
| [Workbench Researcher](../../../skills/researcher/SKILL.md) | Orients on existing indexes, decomposes questions macro to micro, isolates investigations, consolidates via evidence pointers. Its gate checks structure, declared-question coverage and path existence. | Reuse progressive disclosure and focused passes. Do not prescribe its 5×6 tree, require a subagent, or call a real path proof that the cited claim follows. |
| [DiUS deep reconnaissance](https://github.com/DiUS/agent-toolkit/blob/main/skills/codebase-discovery/playbooks/01-deep-recon.md) and [skill](https://github.com/DiUS/agent-toolkit/blob/main/skills/codebase-discovery/SKILL.md) | Prefers declared workspace and manifest structure; falls back to inferred structure; records examined, unreached and excluded areas. Captures code/docs drift and resumes the affected work. | Use an explicit coverage ledger and separate declaration from resolution. A manifest proves what was declared, not the runtime deployment. Do not require interviews or a suite of generated reports. |
| [Software Architecture Analysis](https://github.com/magnus919/agent-skills/blob/main/software-architecture-analysis/SKILL.md) | Uses lenses such as runtime coupling, data ownership and deployment; scopes maps to concrete decisions and records provenance and unknowns. | Multiple memberships are legitimate. “Runs with” and “owns state for” are separate edges. No migration proposal, Mermaid output or architecture judgment is required. |
| [ARCADE Core](https://github.com/usc-softarch/arcade_core/blob/master/scripts/run_clustering.py) and [ARCADE study](https://jgarcia.ics.uci.edu/wp-content/uploads/arcade_msr_2015.pdf) | ARCADE separates extraction from clustering. Its paper compares, among others, ACDC's structural patterns and ARC's implementation concerns. | Compare structural and behavior/concern groupings instead of assuming one partition. Treat disagreement as an inspection lead; do not port clustering algorithms or treat their reported accuracy as ours. |
| [ArchMapper](https://github.com/yannick-leguennec/archmapper) and [reverse-spec](https://github.com/sinedied/agent-skills/blob/main/.agents/skills/reverse-spec/SKILL.md) | ArchMapper resumes checkpointed file analysis and summarizes folders bottom-up. Reverse Spec seeks a reconstruction-grade, testable description. | Keep bounded bottom-up synthesis and make behavior checkable. Avoid per-file model calls, folder hierarchy as truth and a comprehensive rebuild spec. |
| [Aider repo map](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py) | Extracts definition and reference tags and caches by path/mtime; ranks a compact map separately. | Reuse extraction/presentation separation, but key reuse on content and parser profile. No ranking predicate decides which repository facts get retained. |
| [Nx project graph](https://github.com/nrwl/nx/blob/master/packages/nx/src/project-graph/build-project-graph.ts) | Reuses dependency facts from cached files and checks global config and dependency inputs before deciding whether to reuse the file map. | Each extracted relationship needs origin and applicable configuration; resolve against the current inventory before trusting old edges. |
| [GitNexus](https://github.com/abhigyanpatwari/GitNexus/blob/main/gitnexus/skills/gitnexus-guide.md) and [AsyncAPI](https://github.com/asyncapi/spec/blob/master/spec/asyncapi.md#operation-object) | GitNexus distinguishes route, process and symbol; AsyncAPI distinguishes receive and send at channel/message scope. | Separate containment, invocation, publication and subscription. Do not require a spec to exist; use applicable code/config evidence for transport and direction. |
| [Bazel Skyframe](https://github.com/bazelbuild/bazel/blob/master/docs/reference/skyframe.mdx#mapping-to-bazel-concepts) and [Salsa](https://github.com/salsa-rs/salsa/blob/master/book/src/reference/algorithm.md#backdating-sometimes-we-can-be-smarter) | Bazel models directory membership as input; Salsa can reuse dependent computation when an upstream result is semantically unchanged. | A newly discovered file matters even if the registration glob is old. Refresh source anchors without resummarizing a logically identical card. Start with a simple full join, not a new incremental engine. |

## 1. TWO INDEPENDENT PASSES

**Structure first.** Read manifests/workspace membership, build and test configuration, executable entrypoints, runtime registration, deployments and CI. Capture separately the build unit, execution unit and documented owner where each is supported. ADRs suggest intent; do not impose their directory layering on a conflicting implementation.

**Behavior independently.** Start from representative entrypoint or observable output. Follow actual registration, normalized contracts, invocations, storage access and tests in both directions where applicable. Use configuration and symbol resolution, not string co-occurrence. A test definition is evidence of an intended check, not a passing run. A generic library can join a critical flow without becoming a domain.

## 2. GROUPING AND RECONCILIATION

1. Treat a hard boundary backed by runtime or build config as a verified fact *of that type*. It does not prove customer-facing responsibility. Promote coherent, evidence-backed flows as additional views; leave fuzzy grouping as inferred or unassigned.
2. Where the passes disagree, record the competing claims and source kinds. A document may correctly describe a desired future design and still disagree with current behavior; distinguish kinds before declaring a contradiction.
3. Give a node multiple memberships instead of duplicating it. Expose the supporting path or symbol for each material membership. Keep shared infrastructure and unassigned nodes reachable without treating them as universal neighbors.
4. Count what was read and what was resolved, not the number of generated groups. A language we did not parse, a runtime-selected registration and a missing configuration produce different gaps. Avoid universal “project complete” language.

## BOUNDARY DECISIONS IN THE FIRST PROTOTYPE

- For an execution view, start one group per positively identified entrypoint or declared process. A directory or shared package alone is not an execution boundary. Record profile/condition on membership where the input defines one.
- For a behavior view, seed one group from a verified contract or observable outcome. Trace to state changes and outputs. Merge two proposed behavior groups only when the same responsibility is supported by the contract and observable behavior, not just imports. Split when an independently verified boundary, owner or effect requires distinct answers. Record the evidence for merge/split; defer a conflicting grouping rather than inventing a label.
- Resolve event identities within a known transport namespace. For example, `(ordering.bus, order.lifecycle, OrderCancelled, v1)` can link producer and consumer if registration supports all applicable coordinates. An identically named message on another channel does not join; missing routing input is a candidate, not a second resolved consumer.

## 3. WHAT THE MAP SHOULD LOOK LIKE

In [e2e-boilerplate](https://github.com/correriadev/e2e-boilerplate/tree/54ac498c0153d0522042f2ba0af067c2a8cb6136), build/workflow orientation should lead to a report flow: runner, raw diagnostics, report generation and artifact verification. The verifier and the expected behavior are different things. A valid report file can exist while result content is wrong. Do not manufacture controllers and domains because they are common elsewhere.

In [eShop](https://github.com/dotnet/eShop/blob/main/src/Ordering.API/Apis/OrdersApi.cs), a route anchors an ordering flow. The [WebApp registration](https://github.com/dotnet/eShop/blob/main/src/WebApp/Extensions/Extensions.cs) independently proves that an event/handler pair is explicitly registered there. Do not connect those two facts as a same-event publication chain until the intermediates and actual event identity are inspected. This is a useful fixture precisely because the relationship must be discovered rather than assumed.

## REFERENCES

- [Project Mapper Research](PROJECT-MAPPER-RESEARCH.md): scope and design conclusion.
- [REA Evidence, Traversal and Versioning](PROJECT-MAPPER-REA.md): evidence and traversal techniques.
