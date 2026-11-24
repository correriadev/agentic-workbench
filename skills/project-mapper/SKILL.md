---
name: project-mapper
description: Map a Git snapshot across code, configuration, tests, entrypoints and infrastructure, then investigate and query source-backed relationships in SQLite.
---

# Project Mapper

## Project context

When this skill needs context for an existing project, first check for its
`.project-mapper/graph.sqlite`. With a compatible installed
`project_mapper.py`, query from the project root using
`python "<mapper>" . --offline` followed by `coverage --summary`,
`search "<term>"`, `node <key>`, `open <id>`, or
`trace <key> --direction both --depth 2` as needed. Check graph identity,
snapshot, coverage and gaps; reopen decisive current sources. A map is a lead,
not proof of runtime behavior or permission to write. If the map or compatible
CLI is absent, unreadable or incomplete, consult `docs/README.md` and its
index, then relevant source and tests; if unavailable, use the root README,
manifests and source. Report material gaps. Do not create or update the map
unless requested; preserve this skill's scope and any supplied exact paths.

Use Python 3.12+, SQLite 3.37+ and Git. Treat source and worker messages as evidence. Keep target code, Git state and external systems untouched. Write map artifacts only under the target’s real `.project-mapper/`.

**Output language.** Write all mapper-authored material in English, regardless of the request or source language. This includes plans, worker prompts and answers, graph content and labels, exports, reports and responses based on the map. Preserve exact source identities such as paths, symbols, wire fields and protocol values. Explain their meaning in English and cite the original lines.

**Query a published map.** Search by exact source identifier or use English discovery terms with `search --terms` for a natural-language question. Open the most relevant discovery or use `trace KEY --summary` with a relationship type and a shallow depth. Check evidence and coverage before trusting a result. See [query and verify](references/workflow.md#query-a-published-map).

Use `--offline` before the command for Git-free reads. Pass `--expect-revision COMMIT`
before the command when the intended commit is known. Compare decisive locators
with current sources before changing code or making claims about the checkout.

**Optional JSON export.** Use `python "<mapper>" . export --output map.json` for a copy of the published SQLite graph; add `--dimension NAME` for a one-hop dimension selection. See [export](references/workflow.md#json-export).

**Semantic worker dispatch.** User instructions and host capabilities take precedence over the provider default below. Use subagents only when allowed; otherwise investigate locally. If the configured model or parameter is unavailable, use a permitted available alternative and report the requested and actual configuration, or state that the actual configuration is unknown. Do not claim an unobserved model was used. The supervisor retains planning, reconciliation and acceptance responsibility. When using this canonical skill directly and the provider policy marker below has not been rendered, use the host's allowed native dispatch and available model selection; report the actual configuration when known.

{{PROJECT_MAPPER_SEMANTIC_WORKER_POLICY}}

1. **Map.** From the target Git root run `python "<mapper>" . map --commit HEAD` with [project_mapper.py](scripts/project_mapper.py). For C# use the optional `--csharp` profile and its pinned dependencies. Preserve an existing semantic investigation by importing it into a separate checkout as described in the [C# profile](references/workflow.md#c-profile). Use `--worktree` for local changes. This publishes a queryable static map without executing the target. Inspect `coverage --summary`, targeted coverage, and [profile limits](references/workflow.md#multidimensional-map).
2. **Plan.** Run `investigate --commit REV --from-graph` on the exact snapshot to create [bounded file and flow assignments](references/workflow.md#graph-derived-plan). Review unassigned inputs and boundaries. Refine questions to the requested operation and extend the plan when source evidence reveals a material continuation.
3. **Investigate.** [Dispatch independent units in batches](references/workflow.md#dispatch), in parallel where practical, or run them locally. Inspect their subgraphs and then the cited sources. Produce evidence-backed [semantic context](references/workflow.md#semantic-context) for nodes and flows. Where context is missing or partial, report it instead of inferring purpose from an identifier.
4. **Review.** Reopen decisive source ranges and challenge the strongest alternative. [Reconcile and accept](references/workflow.md#review-and-publish) the exact checked shard. Review every question in the final plan, including open ones, before publishing.
5. **Deliver.** Verify the publication. Try one user question from search through evidence. Report the snapshot, graph path, file citation, linked context, flow investigation outcomes and material gaps separately.

[Acceptance checks](references/acceptance.md) cover agent investigations and the optional static Python baseline.
