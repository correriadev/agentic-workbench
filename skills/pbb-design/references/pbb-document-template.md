# PBB Document Template & Deliverable Contract

This reference defines the required structure and content for the generated Product Backlog Building (PBB) specification document (`PBB.md`).

When writing the deliverable, follow these nine sections in order. Translate section headings into the user's language while preserving IDs and traceability tags.

---

### 1. Product

State the objective, constraints, intended outcome, success signal, and recommendation: proceed, validate first, or do not build now.

Include:
- **In Scope:** The smallest selected slice and why it is necessary.
- **Out of Scope:** Excluded capabilities, reasons, and reconsideration conditions.
- **Four Risks:** Risk, evidence or assumption, status (`Supported`, `Unresolved`, `Blocking`), consequence, validation, and affected decision.
- **Decisions:** Explicit user choices and material accepted tradeoffs.

---

### 2. Problems

List problem IDs (`P1`, `P2`, ...), affected actors, consequences, and evidence or assumption references.

---

### 3. Expectations

List expectation IDs (`E1`, `E2`, ...), linked problem IDs, desired outcomes, and observable success signals. Distinguish proposed targets from measured baselines.

---

### 4. Personas

List persona IDs (`PER1`, `PER2`, ...), roles, goals, interactions, and linked problem and expectation IDs.

---

### 5. Functionalities

List functionality IDs (`F1`, `F2`, ...), action-oriented names, served personas, and linked expectations.

---

### 6. Product Backlog

Provide ordered PBIs (`PBI-01`, `PBI-02`, ...) with:
- **Path:** Functionality, Persona, Problem, Expectation.
- **Outcome:** Small, observable user or business outcome (user story format when appropriate).
- **Acceptance Criteria:** Testable at the product level, covering material failure cases.
- **Dependencies:** Required prerequisites or blocking relationships.
- **Readiness:** `Ready for refinement`, `Provisional`, or `Blocked`.
- **Assumptions & Questions:** Linked assumption or question IDs.

If no delivery work is justified, state that explicitly and identify the evidence needed to reconsider.

---

### 7. Traceability Matrix

Use columns: `Problem | Expectation | Persona | Functionality | PBI`.

Use one row per valid path. Separately identify intentionally deferred problems and expectations.

---

### 8. Assumptions and Evidence

Assign IDs to assumptions and external claims (`A1`, `V1`, ...).
Record:
- Epistemic tag (`[Certain]`, `[Likely]`, `[Guessing]`, `[VERIFY]`).
- Provenance (user report, supplied artifact, retrieved source, unsupported hypothesis).
- Evidence status (unverified, supported within stated bounds, conflicting).
- Verification method.
- Dependent decisions or PBIs.

Keep evidence separate from conclusions and proposed choices.

---

### 9. Open Questions

For each question:
- ID (`Q1`, `Q2`, ...).
- Decision affected and linked PBIs.
- Suggested answer (when defensible) and rationale.
- Status (`Unresolved`, `Provisional`, `Resolved`).

Mark blocking questions. Record resolution source for resolved questions. State when no questions remain.

---

## Final Verification Checklist

Before saving the document:
- Verify complete traceability: Problem → Expectation → Persona → Functionality → PBI for every included item.
- Confirm all four risks influence an explicit decision or have a stated rationale.
- Check that scope exclusions do not contradict necessary acceptance criteria or dependencies.
- Ensure unsupported premises remain visible wherever they affect readiness.
- Remove invented facts, decorative scoring, implementation prescriptions, and unnecessary scope.
- Distinguish a coherent backlog from a validated product opportunity; do not claim evidence that discovery has not produced.
