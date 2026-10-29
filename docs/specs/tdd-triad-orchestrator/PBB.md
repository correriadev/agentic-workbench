# Product Backlog Building (PBB) — Self-Managing TDD Triad Orchestrator

## 1. Product

### Objective
Transform the existing monolithic `tdd-orchestrator` skill into an autonomous, self-managing engineering triad where `tdd-orchestrator` acts strictly as the supervisor/conductor, delegating hands-on Red-Green-Refactor construction to a new `tdd-maker` skill and independent verification to `adversarial-qa`, isolated via persistent Git worktrees.

### Constraints
- Keep all skills self-contained, lightweight, and provider-neutral under `skills/<name>/SKILL.md`.
- Enforce strict Maker-Checker isolation: Maker never inspects or mutates `qa.json` or writes outside `files_allowed`; Checker never mutates production code or `tasks.json`.
- Minimal diff and zero daemon bloat: avoid heavy message queues, external databases, or long-running daemons. Use native Git capabilities and Python standard library.
- Compatible with Windows (PowerShell/NTFS) and Unix-like environments (Linux/macOS).

### Intended Outcome
Eliminate cognitive context pollution and role blurring by separating orchestration from code synthesis, resulting in higher first-pass code quality and fully reproducible verification loops.

### Success Signal
Executing `/tdd-orchestrator` runs all pending tasks in `tasks.json`, delegates implementation to `tdd-maker`, submits immutable candidate commits to `adversarial-qa`, executes rework loops upon defect detection, and integrates approved changes via fast-forward without human intervention.

### Recommendation
**Proceed.** The problem is acute, boundaries are validated across multiple model perspectives (Gemini, Codex, GLM-5.3), and the MVP scope follows strict YAGNI principles.

### In Scope
- Creation of `skills/tdd-maker/SKILL.md` as the dedicated Red-Green-Refactor construction worker.
- Refactoring `skills/tdd-orchestrator/SKILL.md` into a pure supervisory coordinator owning `tasks.json` governance, subagent dispatch, and QA gating.
- Lightweight worktree slot management using two persistent detached worktrees (`maker-slot`, `qa-slot`).
- Candidate handoff via immutable commit hashes and durable Git refs (`refs/triad/candidates/<run_id>`).
- Subprocess process-tree termination to avoid file locks on workspace cleanup.

### Out of Scope
- Distributed multi-host worker clustering.
- Real-time event bus daemons (Watchman, sockets, Redis, or Kafka).
- Cryptographic ed25519 payload signing (unnecessary for cooperative single-machine local agent execution).
- Dynamic elastic worktree pools beyond the two fixed slots.

### Four Product Risks

| Risk | Evidence / Assumption | Status | Consequence if Wrong | Validation | Affected Decision |
|---|---|---|---|---|---|
| **Value** | Model focus degrades when coordinating DAGs while writing deep code diffs in the same prompt context. | Supported | Single agent fails to follow strict TDD or skips QA checks. | Compare test assertion rigor and QA loop compliance between monolithic and triad execution. | Keep roles strictly separated across subagents. |
| **Usability** | User wants a single entrypoint `/tdd-orchestrator` that runs autonomously without micro-managing subagents. | Supported | User must manually trigger three separate skills sequentially. | Automated orchestrator coordinates the full loop internally. | `tdd-orchestrator` remains the single public interface. |
| **Feasibility** | Git worktree creation and switching with `--detach` is fast and native across Windows, Linux, and macOS. | Supported | I/O bottlenecks or file locking stall the agentic loop. | Benchmark slot preparation time and verify process cleanup. | Use persistent pre-allocated slots instead of ephemeral creation/deletion. |
| **Business Viability** | Spawning subagents consumes tokens and execution time. | Supported | Token overhead outweighs the quality benefits of role separation. | Evaluate token expenditure per completed task in single-attempt vs retry scenarios. | Dispatch full batches of pending tasks rather than spawning subagents per single line of code. |

### Decisions
1. **Name Selection:** Name the hands-on construction skill `tdd-maker` to align directly with the repository's established Maker-Checker doctrine.
2. **State Governance:** `tdd-orchestrator` maintains exclusive authority over `tasks.json` mutations and QA rework task generation. `tdd-maker` only consumes tasks and outputs code commits.
3. **Topology:** Use two persistent worktree slots (`maker-slot` and `qa-slot`) with detached HEAD rather than destroying and recreating worktrees on every run.
4. **Handoff Mechanism:** Use Git commit SHAs and explicit refs (`refs/triad/candidates/<run_id>`) for handoff; discard external message buses.

---

## 2. Problems

- `P1`: **Cognitive Overload in Monolithic Orchestrator.** `tdd-orchestrator` currently performs both DAG coordination and hands-on code writing, leading to context loss and test-skipping under long contexts.
- `P2`: **Weakened Maker-Checker Boundary.** When the same agent context manages both the rework queue and code generation, it tends to implement shallow fixes that satisfy surface assertions without addressing systemic invariant failures.
- `P3`: **Workspace Collision and Dirty State.** Executing tests and builds in the primary working directory creates untracked artifacts, file lock issues, and potential branch corruption during concurrent agent operations.

---

## 3. Expectations

- `E1`: **Dedicated Construction Worker.** Hands-on implementation is performed exclusively by `tdd-maker` within restricted `files_allowed` boundaries.
- `E2`: **Autonomous Loop Gating.** `tdd-orchestrator` evaluates verdicts from `adversarial-qa`, autonomously generates rework tasks in `tasks.json`, and re-dispatches until `PASS` or budget exhaustion.
- `E3`: **Isolated, Clean Workspaces.** Maker and QA execute in dedicated, isolated Git worktree slots, leaving the primary branch clean until final fast-forward integration.
- `E4`: **Deterministic Artifact Handoff.** Every implementation handoff is represented by an immutable Git commit and reachable ref.

---

## 4. Personas

- `PER1`: **Software Engineer / Operator.** Invokes `/tdd-orchestrator`, reviews the final consolidated diff, and expects verified, production-ready code without having to micromanage agent steps.
- `PER2`: **Triad Orchestrator (System Persona).** Selects pending tasks, dispatches the Maker, captures candidate commits, requests adversarial verification, and manages the lifecycle FSM.

---

## 5. Functionalities

- `F1`: **`tdd-maker` Construction Skill.** Contract and instructions for executing Red-Green-Refactor on assigned tasks within blast-radius boundaries.
- `F2`: **`tdd-orchestrator` Supervisory Protocol.** Workflow logic for topological task selection, Maker dispatch, verdict evaluation, and rework task creation.
- `F3`: **Git Worktree Slot Manager.** Lightweight protocol or helper script to manage `maker-slot` and `qa-slot`, handle `git reset --hard`, and terminate lingering background processes.
- `F4`: **Candidate Commit & Handoff Gating.** Logic to record candidate refs, verify `files_allowed` diffs, invoke `adversarial-qa`, and perform `--ff-only` merge upon approval.

---

## 6. Product Backlog

### PBI-01: Extract Construction Protocol into `tdd-maker` Skill
- **Path:** F1 → PER2 → P1 → E1
- **Outcome:** A self-contained skill `skills/tdd-maker/SKILL.md` that executes the Red-Green-Refactor cycle for pending tasks in `tasks.json` within strict `files_allowed` bounds and outputs a candidate commit.
- **Acceptance Criteria:**
  - Skill file exists at `skills/tdd-maker/SKILL.md` with standard YAML frontmatter.
  - Mandates RED phase (failing test confirmed via runner), GREEN phase (minimal implementation), and REFACTOR phase.
  - Prohibits reading or modifying `qa.json` or mutating tasks outside `files_allowed`.
  - Concludes by generating an immutable Git commit containing only authorized changes.
- **Dependencies:** None.
- **Readiness:** Ready for refinement.
- **Assumptions & Questions:** A1, A2.

### PBI-02: Refactor `tdd-orchestrator` into Pure Supervisory Conductor
- **Path:** F2 → PER2 → P1 → E2
- **Outcome:** Refactored `skills/tdd-orchestrator/SKILL.md` stripped of raw code editing instructions, dedicated entirely to DAG execution, Maker dispatch, and QA coordination.
- **Acceptance Criteria:**
  - `skills/tdd-orchestrator/SKILL.md` delegates all construction to `tdd-maker`.
  - Orchestrator retains exclusive authority to mark tasks `completed` in `tasks.json`.
  - Evaluates `qa.json#.verdicts` and appends rework tasks with sequential IDs (`T*`, origin `RW-*`) upon `FAIL`.
  - Enforces max retry budget (default 2); halts cleanly with summary if budget is exhausted.
- **Dependencies:** PBI-01.
- **Readiness:** Ready for refinement.
- **Assumptions & Questions:** A1, A3.

### PBI-03: Worktree Slot Management & Process Hygiene Protocol
- **Path:** F3 → PER1 → P3 → E3
- **Outcome:** Clear protocol and helper commands for managing two persistent detached worktrees (`maker-slot` and `qa-slot`), ensuring process termination and clean resets between runs.
- **Acceptance Criteria:**
  - Worktrees created outside the main working tree using `git worktree add --detach`.
  - Slot reuse sequence documented and verifiable: kill lingering processes, `git reset --hard <base>`, and clean untracked files while preserving dependency caches.
  - Instructions handle process termination reliably on Windows and POSIX.
- **Dependencies:** PBI-01, PBI-02.
- **Readiness:** Ready for refinement.
- **Assumptions & Questions:** A4, Q1.

### PBI-04: Immutable Ref Handoff and Fast-Forward Integration
- **Path:** F4 → PER2 → P2 → E4
- **Outcome:** Deterministic commit handoff mechanism using `refs/triad/candidates/<run_id>` and validation against `files_allowed` prior to QA dispatch and main integration.
- **Acceptance Criteria:**
  - Orchestrator inspects Maker's candidate commit diff against `files_allowed` globs before invoking QA.
  - QA is dispatched pointing directly to the candidate commit in `qa-slot`.
  - When QA status is `PASS`, orchestrator merges the candidate commit into the target branch via `git merge --ff-only`.
  - Rejection or failure preserves the candidate ref for debugging and appends rework tasks without polluting the primary branch.
- **Dependencies:** PBI-02, PBI-03.
- **Readiness:** Ready for refinement.
- **Assumptions & Questions:** A5, Q2.

---

## 7. Traceability Matrix

| Problem | Expectation | Persona | Functionality | PBI |
|---|---|---|---|---|
| P1 (Cognitive Overload) | E1 (Dedicated Maker) | PER2 (Orchestrator) | F1 (Maker Skill) | PBI-01 |
| P1 (Cognitive Overload) | E2 (Autonomous Gating) | PER2 (Orchestrator) | F2 (Orchestrator Refactor) | PBI-02 |
| P2 (Maker-Checker Boundary) | E2 (Autonomous Gating) | PER2 (Orchestrator) | F2 (Orchestrator Refactor) | PBI-02 |
| P2 (Maker-Checker Boundary) | E4 (Deterministic Handoff) | PER2 (Orchestrator) | F4 (Candidate Handoff) | PBI-04 |
| P3 (Workspace Collision) | E3 (Isolated Workspaces) | PER1 (Operator) | F3 (Worktree Manager) | PBI-03 |
| P3 (Workspace Collision) | E4 (Deterministic Handoff) | PER2 (Orchestrator) | F4 (Candidate Handoff) | PBI-04 |

---

## 8. Assumptions and Evidence

- `A1` (`[Certain]`): Splitting construction and orchestration removes conflicting prompt instructions and keeps token context bounded. Provenance: agent engineering best practices and user requirements.
- `A2` (`[Likely]`): Subagents running `tdd-maker` can complete full Red-Green-Refactor cycles within a designated worktree without parent intervention. Provenance: workbench architecture.
- `A3` (`[Certain]`): `adversarial-qa` remains unmodified as the independent checker; it only needs a target path or commit to audit. Provenance: `skills/adversarial-qa/SKILL.md`.
- `A4` (`[Likely]`): Two persistent worktree slots with detached HEAD eliminate branch collisions and avoid the high overhead of repeated worktree creation/deletion on Windows. Provenance: Codex analysis.
- `A5` (`[Certain]`): Fast-forward merge guarantees that production code reflects exactly what was tested and passed by adversarial QA. Provenance: Git semantics.

---

## 9. Open Questions

- `Q1`: Should worktree preparation be packaged into a lightweight Python CLI script (e.g. `scripts/triad_runner.py`) or embedded directly as shell command instructions in `tdd-orchestrator`?
  - *Suggested Answer:* Embed clear shell steps in `tdd-orchestrator` with an optional standalone helper script for full automation.
  - *Status:* Provisional. Linked PBIs: PBI-03.
- `Q2`: Should `tdd-maker` receive the entire batch of pending tasks from `tasks.json` in one run, or should the orchestrator dispatch one task at a time?
  - *Suggested Answer:* Dispatch the batch of pending tasks that share satisfied dependencies, allowing Maker to produce a single cohesive candidate commit per round.
  - *Status:* Resolved. Linked PBIs: PBI-01, PBI-02.
