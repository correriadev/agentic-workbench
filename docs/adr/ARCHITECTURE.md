---
doc_type: adr
domain: workbench
stack: [markdown, python, powershell, bash]
node_id: "adr:architecture"
tags: [architecture, skills, pipeline]
edges:
  - relation: references
    target: "adr:tests"
updated: 2026-10-29
---
# Agentic Workbench Architecture

## FOLDER STRUCTURE

```text
agentic-workbench/
  skills/           # Self-contained provider-neutral skills (one folder per skill)
  docs/             # Navigation index, digest, graph, and architectural records (adr/)
  scripts/          # Maintenance and synchronization scripts (cleanup.ps1, cleanup.sh, sync_skills.py)
  AGENTS.md         # Universal agent operating rules
  CLAUDE.md         # Claude Code operating rules
  README.md         # Overview, third-party plugins, and skill catalog
```

## LAYERS

- **Discovery & Product Layer:** `brainstorming`, `pbb-design`, `prompt-generator`, and `read-ui-prototype` translate human intent, prompts, and visual prototypes into structured problem spaces and specs.
- **Specification Layer (Intent):** `scope-refinement` inspects `docs/` and codebase evidence to emit the atomic tripartite contract (`SCOPE.md`, `tasks.json`, `qa.json`).
- **Supervision Layer:** `tdd-orchestrator` owns the `tasks.json` DAG, batch dispatch, candidate diff validation, bounded rework, and integration. It never writes production code or tests.
- **Construction Layer (Maker):** `tdd-maker` executes strict Red-Green-Refactor within each task's `files_allowed`, returning candidate commits and terminal evidence without reading or modifying `qa.json` or changing task state.
- **Verification Layer (Checker):** `adversarial-qa` audits system invariants and security against `qa.json`, while `the-grumpy-tech-lead` performs Socratic systemic code review.
- **Knowledge & Delegation Layer:** `project-memory` maintains `docs/`, `codebase-memory` queries the AST graph, `contextual-mentorship` guides decisions, and `ask-*` skills delegate to local CLIs.

## MODULES

| Module | Responsibility | Location |
|---|---|---|
| Core Pipeline Skills | Specification, supervision, TDD construction, adversarial QA, and tech-lead review | `skills/scope-refinement/`, `skills/tdd-orchestrator/`, `skills/tdd-maker/`, `skills/adversarial-qa/`, `skills/the-grumpy-tech-lead/` |
| Discovery & UI Skills | Product backlog building, prompt generation, brainstorming, and UI prototype analysis | `skills/pbb-design/`, `skills/prompt-generator/`, `skills/brainstorming/`, `skills/read-ui-prototype/` |
| Project Memory | Documentation graph generation and ontology validation | `skills/project-memory/` |
| Multi-Agent CLI Wrappers | Headless delegation to Antigravity, Codex, and OpenCode CLIs | `skills/ask-antigravity/`, `skills/ask-codex/`, `skills/ask-opencode/` |
| Maintenance & Sync Scripts | Structural cleanup and on-demand skill sync to coding agents | `scripts/cleanup.ps1`, `scripts/cleanup.sh`, `scripts/sync_skills.py` |

## PATTERNS

- **REQUIRED:** Keep every skill in `skills/<name>/SKILL.md` self-contained, lightweight, and free of external orchestrator coupling.
- **REQUIRED:** Separate authority: supervisor owns `tasks.json`; Maker owns authorized construction changes and never reads or modifies `qa.json`; QA authors findings/verdicts without editing production code, `tasks.json`, or `SCOPE.md`. Supervisor imports validated QA results without changing the verification contract.
- **PROHIBITED:** Store credentials, temporary `.work/` artifacts, or provider-locked metadata inside `skills/`.

## TDD TRIAD

The skill contracts define `tdd-orchestrator -> tdd-maker -> adversarial-qa`; Git commands provide slot management without a separate runner or external orchestrator.

1. **REQUIRED:** Dispatch ordered task batches to a fresh Maker context in persistent `maker-slot`; prepare independent QA in persistent `qa-slot`. Keep both worktrees at detached HEAD and serialize slot ownership. Preserve evidence before reuse; retain dependency caches and stop on unknown changes.
2. **REQUIRED:** Validate each task commit against its own `files_allowed` and the cumulative batch diff against authorized scopes. Pin immutable candidate refs under `refs/triad/candidates/`; run QA on the exact candidate OID and explicit base-to-candidate diff.
3. **REQUIRED:** Keep control state canonical in the specification directory. Overlay SCOPE/QA inputs in `qa-slot`, validate QA-only output changes, and preserve reproducers before cleanup. Never pass `qa.json` into Maker context.
4. **REQUIRED:** Map each open blocking finding to one task with exact `origin: RW-*`. Persist retry use across resume; use the configured batch limit or minimum blocking-invariant limit, default 2 additional attempts. Only QA resolves findings.
5. **REQUIRED:** Integrate only matching QA PASS candidates with zero open blockers using `git merge --ff-only`, after confirming the target base has not advanced. Mark tasks completed only after integration. Keep failed candidates outside the target branch.

These are agent operating contracts, not an OS sandbox or an automated enforcement service. Their canonical definitions are `skills/tdd-orchestrator/SKILL.md` and `skills/tdd-maker/SKILL.md`.

## INTEGRATIONS

| Component | Purpose | Connection |
|---|---|---|
| Caveman & Ponytail | Concise output style and YAGNI minimal-diff discipline | Agent rules / plugins |
| Codebase Memory MCP | Structural AST graph indexing and Cypher/trace queries | MCP stdio server |
| Open Graph MCP | Concurrent repository change governance and cell locking | MCP stdio server |
| RTK | CLI output compression for token efficiency | Shell wrapper |

## REFERENCES

- [Tests](TESTS.md): Verification strategy and executable checks.
