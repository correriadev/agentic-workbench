---
name: scope-refinement
description: Evidence-based scope refinement — translates intent and codebase inspection into an atomic tripartite specification (SCOPE.md, tasks.json, qa.json) for Agentic TDD and Adversarial QA.
---

# Scope Refinement

Senior Software Architect role. Transform requirements and codebase evidence into an atomic tripartite change specification separating Intent (Human), Construction (TDD), and Verification (Adversarial QA).

---

## 1. Inputs

Collect or receive these variables:

| Variable | Description | Validation |
|---|---|---|
| `${scope}` | Business goal, bug description, or change intent | Non-empty text |
| `${projectPaths}` | Local paths of relevant projects (one or more) | Must exist on filesystem |
| `${change_id}` | Identifier for the change folder | `kebab-case` string |
| `${rules}` | Optional constraints or execution guidelines | Defaults to `"Standard practices"` |

Target spec directory: `docs/specs/${change_id}/`.

---

## 2. Grounding (Docs-First Inspection & Discrepancy Investigation)

Inspect documentation and codebase before modeling:

1. **Docs-First Fast-Path (if available):**
   - Check if `${projectPaths}` contains a `docs/` directory with architectural context (e.g., `docs/.digest.md`, `docs/.graph.json`, ADRs in `docs/adr/`, or domain specs).
   - Read these documents first to establish domain boundaries, invariants, and existing contracts without scanning raw code blindly.
   - Record relevant architectural evidence with `kind: "doc"`.

2. **Codebase Inspection (Direct or Fallback):**
   - Search and read source files around the affected domains using file read or search tools.
   - If `docs/` is absent, direct source inspection serves as the primary ground truth.
   - Validate current implementation details, integration points, and file paths with `kind: "code"`.

3. **Active Discrepancy Investigation (MANDATORY):**
   - If a discrepancy is detected between documentation/assumptions and code implementation (e.g., doc states an invariant that code contradicts, or conflicting assumptions):
     - Investigate the code to identify the exact divergence and impact.
     - **NEVER resolve silently.**
     - Escalate the discrepancy directly into the Clarification Interview (Section 4) as a priority question to inform the user.

4. **Record Evidence Items:**
   - `id`: `E1`, `E2`, ...
   - `kind`: `"doc"` | `"code"`
   - `path`: Project-relative path to existing doc, config, or source file.
   - `note`: Concrete fact, invariant, or contract observed.

---

## 3. Strategic Discovery (Optional)

Execute only when:
- Boundaries or data ownership are unknown in existing code.
- Terminology conflicts exist between involved projects.

When triggered, summarize bounded contexts and invariants in a short "Boundaries & Invariants" section inside `SCOPE.md`. Do not create separate files.

---

## 4. Clarification Interview

Resolve ambiguity and discrepancies with minimal friction:
- Limit to **0–5 blocking questions**. Ask only if a wrong assumption alters the DAG or acceptance criteria.
- **Discrepancy Escalation:** Any discrepancy found between documentation/assumptions and code has **highest priority**. Inform the user clearly:
  *"Discrepancy found: [Doc path] states [X], but [Code path] implements [Y]. Which takes precedence for this change?"*
- Every question must include a grounded recommendation based on the investigation.
- When human input is available, ask directly.
- When running headless, adopt the recommendation and record it under `assumptions` (`"from": "Discrepancy Q1 default recommendation"`).

Format:
- Question: `Q1`, `Q2`, ...
- Assumption: `S1`, `S2`, ... with `id`, `text`, and `from`.

---

## 5. Vertical Slicing & Test Pyramid Ownership

Decompose the change by outcome and risk, adhering to the Maker-Checker separation:

### Test Pyramid Segregation
- **TDD Agent (Worker):** Owns construction-adjacent tests written *before* implementation.
  - `tier: "unit"` — Local unit tests with isolated mocks.
  - `tier: "integration"` — Narrow integration tests (single hop: service to local DB/API).
- **Adversarial QA Agent (Judge):** Owns destruction-adjacent tests written against system boundaries.
  - `type: "edge"` — Broad cross-component integration.
  - `type: "e2e"` — End-to-end flows. TDD never writes E2E tests.
  - `type: "property"` — Fuzzing, property invariants, and fault injection.
  - `mock_policy: "real"` — QA attacks real integration seams; never reuses TDD mocks.

### Traceability Closure Rule
Every business acceptance criterion `A*` in `SCOPE.md` must map to:
1. At least one task in `tasks.json` (`acceptance_ids: ["A*"]`).
2. At least one blocking invariant in `qa.json` (`acceptance_ids: ["A*"]`).

---

## 6. Output Specification: The Tripartite Artifacts

Generate three distinct files in `docs/specs/${change_id}/`:

### A. `docs/specs/${change_id}/SCOPE.md` (Intent Tier — Human)
Pure Markdown artifact representing the business and architectural contract:

```markdown
# Scope: ${change_id}

## 1. Intent & Boundaries
- **Objective:** Concise business outcome.
- **In Scope:** Explicit functional additions/modifications.
- **Out of Scope:** Explicit non-goals.

## 2. Behavioral Delta & Acceptance Criteria
- **A1:** Given [precondition], When [action], Then [observable outcome].
- **A2:** Given [precondition], When [action], Then [observable outcome].

## 3. Decisions & Discrepancy Resolutions
- Recorded assumptions (S1, S2...) and user-approved discrepancy resolutions.

## 4. Amendment Log
- Initial baseline established by refinement. (Human changes here trigger recompilation).
```

### B. `docs/specs/${change_id}/tasks.json` (Worker Tier — TDD Agent)
Machine-readable Directed Acyclic Graph (DAG) for implementation:

```json
{
  "change_id": "${change_id}",
  "scope_hash": "sha256_of_SCOPE.md",
  "tasks": [
    {
      "id": "T1",
      "title": "Verifiable task description",
      "project_path": "path/to/project",
      "tier": "unit | integration",
      "depends_on": [],
      "acceptance_ids": ["A1"],
      "evidence_ids": ["E1"],
      "files_allowed": ["src/module/**", "tests/unit/**"],
      "red": {
        "test_file": "tests/unit/feature.spec.ts",
        "test_ids": ["test_case_name"]
      },
      "status": "pending",
      "origin": "scope"
    }
  ]
}
```

### C. `docs/specs/${change_id}/qa.json` (Judge Tier — Adversarial QA Gate)
Strict verification contract for independent quality auditing:

```json
{
  "change_id": "${change_id}",
  "scope_hash": "sha256_of_SCOPE.md",
  "snapshot_ref": "pending",
  "invariants": [
    {
      "id": "QA-I-01",
      "type": "concurrency | property | e2e | failure_injection | boundary",
      "acceptance_ids": ["A1"],
      "statement": "Machine-checkable universal predicate",
      "harness": "artillery | k6 | hypothesis | custom_script",
      "mock_policy": "real | contract-fake",
      "severity": "blocking | advisory",
      "budget": { "max_wall_clock_s": 180, "max_retries": 2 }
    }
  ],
  "rework_queue": [],
  "verdicts": []
}
```

---

## 7. Mechanical Readiness Gate

Before completing, self-validate the generated directory against these 7 checks:
1. **Triad Existence:** All 3 files (`SCOPE.md`, `tasks.json`, `qa.json`) exist in `docs/specs/${change_id}/`.
2. **JSON Integrity:** `tasks.json` and `qa.json` parse with zero errors.
3. **DAG Validity:** At least one task has `"depends_on": []`, and the graph resolves topographically without cycles.
4. **Traceability Closure:** Every acceptance `A*` in `SCOPE.md` is referenced by $\ge 1$ task in `tasks.json` AND $\ge 1$ blocking invariant in `qa.json`.
5. **Blast-Radius Confinement:** Every task in `tasks.json` defines non-empty `files_allowed`.
6. **Measurable Invariants:** Every entry in `qa.json` has a concrete predicate, harness, and severity.
7. **Zero Open Blockers:** `open_questions` is empty; all discrepancies are resolved or captured in `assumptions`.

If any check fails, correct the specification and re-verify before finishing.

---

## 8. General Rules

- **No Production Code:** Do not write implementation files.
- **Spec Isolation:** Do not modify existing specs outside `docs/specs/${change_id}/`.
- **Maker-Checker Isolation:** TDD agent never writes to `qa.json`; Adversarial QA never directly edits `tasks.json` (appends only to `rework_queue`).
