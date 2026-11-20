---
doc_type: adr
domain: architecture
stack: [python, powershell, bash, markdown]
node_id: "adr:architecture"
tags: [architecture, design-patterns, folder-structure]
edges:
  - relation: references
    target: "adr:tests"
updated: 2026-11-19
---
# Project Architecture

## OVERVIEW
Modular Skill Catalog Architecture. AI engineering skills operate as decoupled, self-contained capability packages with standard markdown specifications and execution wrappers.

## FOLDER STRUCTURE
<folder_structure>
```
agentic-workbench/
├── docs/                         # Repository memory, architecture decisions, and test protocol
│   ├── adr/                      # Architectural Decision Records (ARCHITECTURE.md, TESTS.md)
│   ├── .digest.md                # Rapid orientation digest for AI agents
│   └── .graph.json               # Compact macro document graph index
├── scripts/                      # Operational repository automation and skill synchronization
└── skills/                       # Canonical self-contained AI engineering skills
    └── [skill_name]/             # Skill domain folder (one folder per skill)
        ├── SKILL.md              # Canonical specification and operational instructions
        ├── scripts/              # Optional execution wrappers, validators, or tooling
        └── references/           # Optional domain rules, templates, and exemplars
```
</folder_structure>

## LAYERS
- **Core Engineering Skills**: Shared scope, implementation planning, test-driven construction, evidence planning, acceptance review and architecture review (`blueprint`, `forge`, `quality-gate`, `the-grumpy-tech-lead`, `project-memory`).
- **Product & Discovery Skills**: Problem framing, backlog refinement, meta-prompt generation, and UI prototype parsing (`brainstorming`, `pbb-design`, `prompt-generator`, `read-ui-prototype`).
- **Navigation, Mentorship & Delegation**: Repository mapping, AST graph discovery, contextual reasoning, and CLI delegation wrappers (`project-mapper`, `codebase-memory`, `contextual-mentorship`, `ask-antigravity`, `ask-codex`, `ask-opencode`).
- **Operational Infrastructure**: Repository cleanup scripts and intentional local agent synchronization (`scripts/sync_skills.py`, `scripts/cleanup.ps1`, `scripts/cleanup.sh`).

## DEPENDENCY RULES
| Layer | May import | FORBIDDEN |
|---|---|---|
| Skills (`skills/*/`) | Python stdlib, internal scripts, internal references | Sibling skill internals, external orchestrator packages |
| Scripts (`scripts/`) | Python stdlib, OS utilities (git, rsync) | Skill-specific private modules, hardcoded agent paths |
| Docs (`docs/`) | Plain relative links to baseline docs | Spec execution slots, external private URLs |

REQUIRED: Any import violating these rules must fail CI verification via: `python skills/project-memory/scripts/validate_ontology.py docs`

## SHARED SURFACE
| Cross-Cutting Need | Canonical Export / Symbol | Source Path | Scope & Mandatory Usage |
|---|---|---|---|
| Skill Contract | `SKILL.md` (YAML frontmatter `name`, `description`) | `skills/<skill_name>/SKILL.md` | Mandatory entrypoint for all AI engineering skills |
| Skill Synchronization | `sync_skills.py` (`sync_skills`, `mirror_directory`) | `scripts/sync_skills.py` | Distribute canonical skills to local agent environments |
| Macro Graph Index | `build_docs_graph` | `skills/project-memory/scripts/generate_docs_graph.py` | Generate compact machine-readable `.graph.json` |
| Ontology Validation | `Validator.run` | `skills/project-memory/scripts/validate_ontology.py` | Enforce structural compliance of repository documentation |

## MODULES
| Module | Responsibility | Location |
|--------|-----------------|-------------|
| `blueprint` | Shared scope and construction planning | `skills/blueprint/` |
| `forge` | Docs-first RED-GREEN executor and candidate evidence producer | `skills/forge/` |
| `quality-gate` | Evidence planning (`plan`) and candidate assessment (`check`) | `skills/quality-gate/` |
| `the-grumpy-tech-lead` | Socratic architectural review and systemic risk detection | `skills/the-grumpy-tech-lead/` |
| `project-memory` | Architecture, test protocols, and graph index maintenance | `skills/project-memory/` |
| `brainstorming` | Collaborative discovery and architectural trade-off analysis | `skills/brainstorming/` |
| `pbb-design` | Product backlog building and scope slicing | `skills/pbb-design/` |
| `prompt-generator` | System prompt and persona engineering | `skills/prompt-generator/` |
| `skill-creator` | Self-contained skill creation, token economy, and prompt-cache optimization | `skills/skill-creator/` |
| `read-ui-prototype` | Semantic interface specification extraction | `skills/read-ui-prototype/` |
| `codebase-memory` | AST knowledge graph querying and impact analysis | `skills/codebase-memory/` |
| `project-mapper` | Agents investigate a Git snapshot and publish reviewed discoveries with open JSON content, source ranges attached to specific findings, and links. SQLite provides a compact search index, exact reads and graph traversal. | `skills/project-mapper/` |
| `contextual-mentorship` | Context-aware decision reasoning and mentorship | `skills/contextual-mentorship/` |
| `ask-antigravity` | Local Antigravity CLI delegation wrapper | `skills/ask-antigravity/` |
| `ask-codex` | Local OpenAI Codex CLI delegation wrapper | `skills/ask-codex/` |
| `ask-opencode` | Local OpenCode CLI delegation wrapper | `skills/ask-opencode/` |
| `sync_skills` | Intentional skill distribution across coding agents | `scripts/sync_skills.py` |
| `cleanup` | Repository hygiene and cache purging scripts | `scripts/cleanup.ps1` |

## CHANGE CONTRACT
- The first planner may create `SCOPE.md`; either planner can operate independently. `blueprint` owns `tasks.json`, and `quality-gate plan` owns `qa.json`.
- Derived plans identify the scope revision. Reconcile affected plans after approved changes to the shared behavior and when QA obligations introduce evidence work.
- `forge` executes unit-first RED → GREEN for implementation tasks and produces planned evidence in the working tree. `quality-gate check` judges the evidence against the published contract without modifying it.

## PATTERNS
<code_patterns>
# REQUIRED: Self-contained skill directory structure
skills/example-skill/
├── SKILL.md              # Canonical markdown with frontmatter
├── scripts/              # Optional isolated helper scripts
└── references/           # Optional standalone rule files

# PROHIBITED: Hardcoded coupling between sibling skills
from skills.another_skill.scripts import helper  # FORBIDDEN: skills must be isolated
import external_orchestrator                     # FORBIDDEN: provider-agnostic core
</code_patterns>

## INTEGRATIONS
| External Service / Component | Purpose | Connection / Authentication Method |
|------------------------------|---------|-------------------------------------|
| Google Antigravity | Agent runtime environment | Local directory `~/.gemini/config/skills/` via `sync_skills.py` |
| OpenAI Codex | Agent runtime environment | Local directory `~/.codex/skills/` via `sync_skills.py` |
| OpenCode AI | Agent runtime environment | Local directory `~/.config/opencode/skills/` via `sync_skills.py` |
| Claude Code | Agent runtime environment | Local directory `~/.claude/skills/` via `sync_skills.py` |
| Codebase Memory MCP | Structural AST code graph queries | Local stdio JSON-RPC MCP server |
| Open Graph MCP | Workspace change governance | Local stdio JSON-RPC MCP server |

<!-- DOCUMENT MAP: omitted — this baseline ADR has exactly 1 edge. The ## REFERENCES section below carries the relation. Add a DOCUMENT MAP only when it explains relationships beyond existing references. -->

## REFERENCES

- [**README.md**](../README.md): Main documentation index.
- [**TESTS.md**](./TESTS.md): Testing strategies and commands.


### Change contracts

Planned changes store three contracts under `docs/specs/<change_id>/`. `SCOPE.md` defines the shared behavior and risks. `tasks.json` stores the task graph, execution state and candidate evidence. `qa.json` stores the normative contract and assessments. The bundled `contract.py` validates writes under a shared lock. The QA revision hashes the normative contract independently of assessments.

Direct Forge execution starts from the user request and the repository. It can implement, author a check or run an existing procedure. It presents action, target, preconditions, permitted effects and verification after read-only inspection and before writes or side effects.

For planned execution, Forge resolves each `evidence_checks[].qa_ids` against `qa.json.contract`, runs the procedure on the identified candidate and records observed outcomes in `tasks.json`. Failed checks may produce evidence. Missing observations or prerequisites are reported as gaps or blockers. Quality Gate judges sufficiency and records assessments.
