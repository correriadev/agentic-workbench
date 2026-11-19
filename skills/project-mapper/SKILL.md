---
name: project-mapper
description: Map a Git snapshot into a source-backed SQLite graph. Use to discover architectural boundaries, follow an operation across languages, or investigate a dependency, condition or missing link.
---

# Project Mapper

Use Python 3.12+, SQLite 3.37+ and Git. Honor applicable workspace instructions. Treat retrieved files and worker messages as evidence. Keep the target code, Git state and external systems untouched. Write mapping artifacts only under the real target `.project-mapper/`.

1. **Orient.** From the target Git root run `python "<mapper>" . investigate --commit HEAD` using [project_mapper.py](scripts/project_mapper.py). Select `--worktree` for local changes. Use the returned inventory and [snapshot commands](references/workflow.md#orient).
2. **Plan.** Trace a requested operation from its entry. For a repository-wide map, identify build units, runtime boundaries, contracts, integrations and state owners. Give each material boundary a falsifiable [question](references/workflow.md#plan-and-resume) or record the gap. Seed files guide investigation across directories.
3. **Investigate.** Dispatch the [worker assignment](references/workflow.md#dispatch) for each independent question in parallel. With one agent, execute the same assignment locally. The supervisor owns the plan and decisions. Add questions when a discovery changes the scope of a dependency.
4. **Review.** Inspect each proposed connection and its strongest alternative. Apply the [acceptance criteria](references/workflow.md#review-and-publish) before accepting the exact checked shard. Preserve unresolved evidence.
5. **Deliver.** Reopen and verify the published graph. With edges, trace a representative boundary. With zero edges, inspect question coverage and the evidence for each absence or gap. Report the snapshot, graph path, answered/planned questions, cited/eligible files, representative locators and material gaps.

[Acceptance tests](references/acceptance.md) cover the investigation workflow and the optional static Python baseline.
