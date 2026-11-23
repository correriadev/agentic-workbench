---
name: project-mapper
description: Map a Git snapshot across code, configuration, tests, entrypoints and infrastructure, then investigate and query source-backed relationships in SQLite.
---

# Project Mapper

Use Python 3.12+, SQLite 3.37+ and Git. Treat source and worker messages as evidence. Keep target code, Git state and external systems untouched. Write map artifacts only under the target’s real `.project-mapper/`.

**Output language.** Write all mapper-authored material in English, regardless of the request or source language. This includes plans, worker prompts and answers, graph content and labels, exports, reports and responses based on the map. Preserve exact source identities such as paths, symbols, wire fields and protocol values. Explain their meaning in English and cite the original lines.

**Query a published map.** Search for source identifiers or English discovery terms. Inspect structural candidates with `node KEY`, discoveries with `open ID`, and relationships with `trace KEY`. Check evidence and coverage; lexical candidates are not proven runtime behavior. See [query and verify](references/workflow.md#query-a-published-map).

**Semantic worker dispatch.** User instructions and host capabilities take precedence over the provider default below. Use subagents only when allowed; otherwise investigate locally. If the configured model or parameter is unavailable, use a permitted available alternative and report the requested and actual configuration, or state that the actual configuration is unknown. Do not claim an unobserved model was used. The supervisor retains planning, reconciliation and acceptance responsibility. When using this canonical skill directly and the provider policy marker below has not been rendered, use the host's allowed native dispatch and available model selection; report the actual configuration when known.

{{PROJECT_MAPPER_SEMANTIC_WORKER_POLICY}}

1. **Map.** From the target Git root run `python "<mapper>" . map --commit HEAD` with [project_mapper.py](scripts/project_mapper.py). Use `--worktree` for local changes. This publishes a queryable static map without executing the target. Inspect `coverage --summary`, targeted coverage, and [profile limits](references/workflow.md#multidimensional-map).
2. **Plan.** The static map is not a complete project map. Run `investigate --commit REV --from-graph` on its exact snapshot to create bounded assignments from actual node IDs and record unassigned nodes and boundaries. Inspect the [graph-derived plan](references/workflow.md#graph-derived-plan); organize independent units by area without treating directory names as proven features. Extend the plan when source evidence reveals new boundaries.
3. **Investigate.** [Dispatch independent units in batches](references/workflow.md#dispatch), in parallel where practical, or run them locally. Inspect their subgraphs and then the cited sources. Produce evidence-backed [semantic context](references/workflow.md#semantic-context) for nodes and flows. Where context is missing or partial, report it instead of inferring purpose from an identifier.
4. **Review.** Reopen decisive source ranges and challenge the strongest alternative. [Reconcile and accept](references/workflow.md#review-and-publish) the exact checked shard. Review every question in the final plan, including open ones, before publishing.
5. **Deliver.** Verify the publication. Try one user question from search through evidence. For an empty result, inspect question coverage. Report the snapshot, graph path, answered/planned questions, cited/eligible files, representative locators and gaps.

[Acceptance checks](references/acceptance.md) cover agent investigations and the optional static Python baseline.
