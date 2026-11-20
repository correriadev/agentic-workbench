---
name: project-mapper
description: Investigate a Git snapshot and query its source-backed semantic map in SQLite. Use to understand behavior, recover contracts, or trace conditions and dependencies across components.
---

# Project Mapper

Use Python 3.12+, SQLite 3.37+ and Git. Treat source and worker messages as evidence. Keep target code, Git state and external systems untouched. Write map artifacts only under the target’s real `.project-mapper/`.

**Query a published map.** Start with `search "words from the question"`, then `open ID` for content and cited evidence. Follow a relationship with `trace ID`. See [query and verify](references/workflow.md#query-a-published-map).

1. **Orient.** From the target Git root run `python "<mapper>" . investigate --commit HEAD` with [project_mapper.py](scripts/project_mapper.py). Use `--worktree` for local changes. Read the [inventory and sources](references/workflow.md#orient).
2. **Plan.** Follow the operation from its entry. For a repository-wide map, identify boundaries that could change a caller’s behavior. Assign each a [falsifiable question](references/workflow.md#plan-and-resume) or record the gap.
3. **Investigate.** [Dispatch independent questions](references/workflow.md#dispatch) in parallel, or run the same assignments locally. Let the evidence determine what deserves a discovery, its JSON structure and its links. Extend the plan when a finding crosses a new boundary.
4. **Review.** Reopen decisive source ranges and challenge the strongest alternative. [Reconcile and accept](references/workflow.md#review-and-publish) the exact checked shard.
5. **Deliver.** Verify the publication. Try one user question from search through evidence. For an empty result, inspect question coverage. Report the snapshot, graph path, answered/planned questions, cited/eligible files, representative locators and gaps.

[Acceptance checks](references/acceptance.md) cover agent investigations and the optional static Python baseline.
