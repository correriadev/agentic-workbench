---
name: skill-creator
description: Create, audit, or optimize self-contained AI agent skills (SKILL.md, scripts, references) with strict token economy, single-source rule deduplication, and prefix-stable prompt caching.
---

# Skill Creator

Create and refine provider-agnostic, self-contained skills (`skills/<skill-name>/SKILL.md`) that give coding agents non-obvious operational guidance with minimal token footprint and maximum KV-cache reuse.

## 1. Core Principles

- **Assume Agent Competence:** Include only domain constraints, state transitions, schemas, or edge cases that change the agent's decisions. Omit generic advice, posture fluff ("You act as an impartial judge"), and self-evident tutorials.
- **Self-Contained & Provider-Agnostic:** Every skill in `skills/<name>/SKILL.md` must work standalone without runtime imports from sibling skills. When host-specific subagent parameters are needed, use a single renderable placeholder token (`PROVIDER_SUBAGENTS_POLICY` inside double curly braces) resolved by `scripts/sync_skills.py`.
- **Match Specificity to Risk:** Use open-ended outcome criteria for creative/discovery work; reserve strict state machines, NUL-safe git commands, and JSON schemas for high-risk or multi-agent transactional workflows.
- **Progressive Disclosure:** Keep `SKILL.md` focused on the entrypoint contract, core workflow, and invariants. Move large reference tables, optional templates, or deterministic automation into `references/` or `scripts/`, loaded only on demand.

## 2. Token Economy & Structural Deduplication

Before finalizing any new or updated skill, audit both **static prompt tokens** (loaded on every skill invocation) and **runtime IPC tokens** (consumed across subagent dispatches and tool loops):

1. **Single-Source Rule Authority:** State each constraint once in its authoritative section:
   - Never repeat security prohibitions in `<system_role>`, `<execution_protocol>`, and `<pre_flight_check>`.
   - Define recurring composite actions (e.g., `BLOCK`, `Slot Hygiene`) once and reference them by name in state tables and steps.
   - Render host policy tokens (`PROVIDER_SUBAGENTS_POLICY`) **once** in a shared protocol header—never duplicate the placeholder across multiple dispatch sections.
   - However, **preserve cross-skill security boundaries** when subagents run with isolated contexts (`fork_turns: none`): each worker skill must retain its own air-gap and immutability rules.
2. **Table & Schema Compression:**
   - Merge redundant table columns (e.g., combine `Definitive Signature` and `Discriminator Test` when they restate the same condition).
   - Keep JSON/Markdown output contracts strict, retaining all required keys, enums, and null types, but strip outer Markdown code fences around XML delimiter tags (emit `<result>{...}</result>` directly) and require concise diagnostic/evidence excerpts.
3. **Pointer-Over-Payload IPC (Runtime Token Saving):**
   - When an orchestrator dispatches a worker with local disk/git access, instruct it to pass **pointers** (file paths, commit OIDs, diff commands, and only the active batch's task records)—never paste full `tasks.json` files, `SCOPE.md`, or raw `git diff` outputs inline into the dispatch prompt.

## 3. Prompt Caching Architecture (`Prefix-Stable Dispatch`)

Provider APIs (OpenAI GPT-6/Codex, Anthropic Claude, Google Gemini, DeepSeek/GLM) match prompt caches on an **exact byte-for-byte prefix** (75–90% input token discount). Any dynamic value placed early invalidates the entire downstream cache.

### A. Static-to-Dynamic Prompt Layering
Structure `SKILL.md` instructions and subagent dispatch templates strictly from most stable to most volatile:

```text
[1. STATIC PREFIX — Identical across all runs & batches]
- Skill instructions (SKILL.md), system role, security boundaries, and output schema.
- Change-level invariants: change_id, scope_hash, slot path, discovered repo test/build commands.

[2. SEMI-STATIC BATCH CONTEXT — Identical across retries of the same batch]
- batch_id, assigned task objects, or applicability map serialized in deterministic key order.

[3. VOLATILE ATTEMPT SUFFIX — Changes per retry/attempt (ALWAYS LAST)]
- attempt counter, dispatch_base_oid, candidate_oid, delta repair tasks, or open rework items.
```

### B. Multi-Turn KV-Cache Preservation Inside Workers
- **Deterministic Turn-1 Warmup:** Instruct subagents to execute a fixed mandatory first action (e.g., `cd <slot>`) before any exploratory reads or commands, keeping the Turn-1 prefix identical across retries.
- **Append-Only Retries:** On retry or rework, keep the original task block unchanged and append delta findings at the end of the prompt rather than rewriting or reordering earlier JSON keys.

## 4. Anatomy & Conventions

```text
skills/<skill-name>/
├── SKILL.md          # Required: YAML frontmatter (name, description) + concise Markdown body
├── scripts/          # Optional: Deterministic CLI helpers, validators, or test suites
└── references/       # Optional: On-demand schemas, templates, or deep domain rules
```

### Frontmatter Rules
- `name`: Lowercase hyphen-case (`^[a-z0-9-]+$`, max 64 chars), matching the folder name.
- `description`: Concise (1–2 sentences, max 1024 chars, no `<` or `>`). State what the skill does and when to trigger it.

## 5. Verification & Synchronization Workflow

After creating or updating a skill in `skills/<skill-name>/`:

1. **Validate Frontmatter & Structure:** Ensure valid YAML frontmatter (`name`, `description`), no leftover `[TODO:...]` placeholders, and balanced code fences.
2. **Audit Token Footprint:** Verify zero duplicate policy tokens, zero repeated section procedures, and strict `Static -> Semi-Static -> Dynamic Suffix` ordering in any subagent dispatch instructions.
3. **Update Architecture Docs (if adding/removing a skill):** Register new skills in `docs/adr/ARCHITECTURE.md` and regenerate the documentation graph:
   ```powershell
   python skills/project-memory/scripts/generate_docs_graph.py docs
   python skills/project-memory/scripts/validate_ontology.py docs
   ```
4. **Synchronize to Agent Environments:** Propagate canonical skills to Antigravity, Codex, OpenCode, and Claude:
   ```powershell
   python scripts/sync_skills.py
   ```
