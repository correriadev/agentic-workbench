---
doc_type: adr
domain: workbench
stack: [markdown, python, powershell, bash]
node_id: "adr:architecture"
tags: [architecture, skills, pipeline]
edges:
  - relation: references
    target: "adr:tests"
updated: 2026-10-28
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
- **Construction Layer (Maker):** `tdd-orchestrator` executes Red-Green-Refactor cycles over the `tasks.json` DAG within strict `files_allowed` boundaries.
- **Verification Layer (Checker):** `adversarial-qa` audits system invariants and security against `qa.json`, while `the-grumpy-tech-lead` performs Socratic systemic code review.
- **Knowledge & Delegation Layer:** `project-memory` maintains `docs/`, `codebase-memory` queries the AST graph, `contextual-mentorship` guides decisions, and `ask-*` skills delegate to local CLIs.

## MODULES

| Module | Responsibility | Location |
|---|---|---|
| Core Pipeline Skills | Specification, TDD execution, adversarial QA, and tech-lead review | `skills/scope-refinement/`, `skills/tdd-orchestrator/`, `skills/adversarial-qa/`, `skills/the-grumpy-tech-lead/` |
| Discovery & UI Skills | Product backlog building, prompt generation, brainstorming, and UI prototype analysis | `skills/pbb-design/`, `skills/prompt-generator/`, `skills/brainstorming/`, `skills/read-ui-prototype/` |
| Project Memory | Documentation graph generation and ontology validation | `skills/project-memory/` |
| Multi-Agent CLI Wrappers | Headless delegation to Antigravity, Codex, and OpenCode CLIs | `skills/ask-antigravity/`, `skills/ask-codex/`, `skills/ask-opencode/` |
| Maintenance & Sync Scripts | Structural cleanup and on-demand skill sync to coding agents | `scripts/cleanup.ps1`, `scripts/cleanup.sh`, `scripts/sync_skills.py` |

## PATTERNS

- **REQUIRED:** Keep every skill in `skills/<name>/SKILL.md` self-contained, lightweight, and free of external orchestrator coupling.
- **REQUIRED:** Enforce strict Maker-Checker isolation (`tdd-orchestrator` never edits `qa.json`; `adversarial-qa` never edits production code or `tasks.json`).
- **PROHIBITED:** Store credentials, temporary `.work/` artifacts, or provider-locked metadata inside `skills/`.

## INTEGRATIONS

| Component | Purpose | Connection |
|---|---|---|
| Caveman & Ponytail | Concise output style and YAGNI minimal-diff discipline | Agent rules / plugins |
| Codebase Memory MCP | Structural AST graph indexing and Cypher/trace queries | MCP stdio server |
| Open Graph MCP | Concurrent repository change governance and cell locking | MCP stdio server |
| RTK | CLI output compression for token efficiency | Shell wrapper |

## REFERENCES

- [Tests](TESTS.md): Verification strategy and executable checks.
