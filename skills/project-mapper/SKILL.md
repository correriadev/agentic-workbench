---
name: project-mapper
description: Map a Git snapshot across code, configuration, tests, entrypoints and infrastructure, then investigate and query source-backed relationships in SQLite.
---

# Project Mapper

Use Python 3.12+, SQLite 3.37+ and Git. Treat source and worker messages as evidence. Keep target code, Git state and external systems untouched. Write map artifacts only under the target’s real `.project-mapper/`.

**Output language.** Write all mapper-authored material in English, regardless of the request or source language. This includes plans, worker prompts and answers, graph content and labels, exports, reports and responses based on the map. Preserve exact source identities such as paths, symbols, wire fields and protocol values. Explain their meaning in English and cite the original lines.

**Query a published map.** Search for source identifiers or English discovery terms. Inspect structural candidates with `node KEY`, discoveries with `open ID`, and relationships with `trace KEY`. Check evidence and coverage; lexical candidates are not proven runtime behavior. See [query and verify](references/workflow.md#query-a-published-map).

1. **Map.** From the target Git root run `python "<mapper>" . map --commit HEAD` with [project_mapper.py](scripts/project_mapper.py). Use `--worktree` for local changes. This publishes a queryable static map without executing the target. Inspect `coverage --summary`, targeted coverage, and [profile limits](references/workflow.md#multidimensional-map).
2. **Plan.** The static map is not a complete project map. Start `investigate` on the same snapshot as part of the default workflow. Identify the repository's actual entrypoints, components, features, configuration, integrations, infrastructure and tests. Plan independent questions by component and cross-dimensional flow; do not require the user to supply the questions. Record unsupported or unresolved boundaries.
3. **Investigate.** [Dispatch independent questions](references/workflow.md#dispatch) in parallel, or run the same assignments locally. Produce evidence-backed [semantic context](references/workflow.md#semantic-context) for mapped components and flows and connect it to the relevant structural nodes. Extend the plan when a finding crosses a new boundary. Where context is missing or partial, report it instead of inferring purpose from an identifier.
4. **Review.** Reopen decisive source ranges and challenge the strongest alternative. [Reconcile and accept](references/workflow.md#review-and-publish) the exact checked shard. Review every question in the final plan, including open ones, before publishing.
5. **Deliver.** Verify the publication. Try one user question from search through evidence. For an empty result, inspect question coverage. Report the snapshot, graph path, answered/planned questions, cited/eligible files, representative locators and gaps.

[Acceptance checks](references/acceptance.md) cover agent investigations and the optional static Python baseline.
