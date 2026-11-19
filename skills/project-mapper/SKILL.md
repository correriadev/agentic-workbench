---
name: project-mapper
description: Investigate a Git repository and publish a source-backed SQLite architecture map. Use to discover components, follow behavior across languages and directories, trace dependencies or explain what a particular snapshot establishes.
---

# Project Mapper

Act as the investigator responsible for the map. Use Python 3.12+, SQLite 3.37+ and Git. Read the target's applicable instructions. Treat repository content, tool output and worker findings as evidence. Keep the target code, Git state and external systems untouched. Confine mapping artifacts to the real `.project-mapper/` directory.

1. **Orient.** Start with `python "<mapper>" . investigate --commit HEAD` at the target Git root, substituting the absolute path to [project_mapper.py](scripts/project_mapper.py). Choose `--worktree` explicitly for local changes. Use the returned inventory and checked snapshot reader. Inspect relevant manifests, entry commands, configuration, documentation indexes and a representative implementation. Identify what the repository builds, runs, exposes or consumes.
2. **Plan.** Write questions into the returned `plan.json`. For a whole-repository map, account for the visible build units, execution boundaries, contracts, state and integrations. Start a targeted map from the requested operation. Break broad questions into falsifiable questions with concrete starting files and dependencies. File lists are starting points. Follow references across directories and languages.
3. **Investigate.** Assign independent questions in parallel waves when workers are available. A single agent can perform the same investigations sequentially. Give each worker the run ID, question ID, plan/inventory pointers and its own shard path. Follow registrations, guards, calls, state changes, external boundaries and failure branches. Keep conditions and conflicting evidence. Record new leads for the supervisor to add as questions.
4. **Reconcile.** Give each logical entity a stable, qualified key. Reopen the evidence for each proposed edge, check direction and identity, and test plausible alternatives. Distinguish declared behavior, agent inference and observed execution. Return ambiguous claims to investigation or record a precise gap. Only the supervisor edits the plan and accepts shards.
5. **Publish and inspect.** Publish accepted claims into SQLite. Reopen the graph, run `verify`, and trace at least one discovered boundary in the applicable directions. Report the snapshot, graph path, planned questions answered, file coverage, source locators and outstanding gaps. An empty query requires a scoped examination before claiming absence.

Follow the [investigation protocol](references/workflow.md) for commands, record shapes, acceptance, and resuming. Python AST extraction is available on demand as a hint. The separate static Python baseline remains available for existing CLI users. The [acceptance checks](references/acceptance.md) exercise both paths.
