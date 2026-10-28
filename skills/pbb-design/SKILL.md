---
name: pbb-design
description: Designs a structured Product Backlog using the Product Backlog Building (PBB) methodology from an initial product or feature scope.
---

# PBB Design — Product Backlog Building

Transform an initial product or feature scope into an evidence-grounded Product Backlog using the **Product Backlog Building (PBB)** methodology. Keep business discovery strictly separate from software architecture and technical implementation details.

## 1. Core Principles

- **Problem First:** Start from undesirable situations, never disguised solutions (e.g., *"Users cannot track account status"* instead of *"Need a dashboard"*).
- **Traceable Value:** Every Product Backlog Item (PBI) must trace directly through `Problem/Expectation → Persona → Functionality → PBI`. Remove orphan items.
- **No Silent Invention:** Never fabricate business rules, pricing, permissions, integrations, or compliance constraints. Record missing context explicitly in `Assumptions` and `Open Questions`.

## 2. Discovery & Construction Workflow

1. **Understand the Product:** Extract the product name, core purpose, business context, and scope boundaries in a concise intention statement.
2. **Identify Problems:** List the concrete pain points motivating the product. Mark inferred problems as provisional assumptions.
3. **Identify Expectations:** Map each problem to the desired user or business outcome.
4. **Identify Personas:** Define only actors who directly interact with or are impacted by the product (`Name/Role`, `Primary Goal`, `Key Interactions`, `Linked Problems/Expectations`). Omit fictional demographic fluff.
5. **Identify Functionalities:** Group high-level capabilities delivering recognizable value to personas using concise action-oriented names (e.g., *Browse courses*, *Enroll in course*).
6. **Generate PBIs:** Decompose each functionality into small, independently valuable backlog items linked to a persona:
   ```text
   As a <persona>, I want <capability>, so that <benefit>.
   ```
7. **Resolve Gaps:** Convert decision-relevant ambiguities into open questions with a conservative, scope-preserving suggested answer. Ask the user to confirm or adjust before finalizing (or record as a provisional assumption if running headlessly).

## 3. Output Format

Produce Markdown with these sections in order:

1. `## 1. Product` — Name, objective, and scope boundaries.
2. `## 2. Problems` — Numbered list (`P1`, `P2`...).
3. `## 3. Expectations` — Numbered list (`E1`, `E2`...) mapped to problems.
4. `## 4. Personas` — Roles, goals, interactions, and linked problems/expectations.
5. `## 5. Functionalities` — High-level capabilities (`F1`, `F2`...) mapped to personas.
6. `## 6. Product Backlog` — Ordered PBIs (`PBI-01`, `PBI-02`...) grouped by functionality.
7. `## 7. Traceability Matrix` — Table mapping `PBI → Functionality → Persona → Problem/Expectation`.
8. `## 8. Assumptions` — Explicit provisional assumptions.
9. `## 9. Open Questions` — Decision-relevant gaps (or `No open questions.`):
   ```markdown
   ### Q01 — [Question]
   - **Suggested answer:** [Conservative recommendation]
   - **Rationale:** [Why this preserves scope safely]
   - **Status:** [Validated | Provisional assumption | Unresolved]
   ```

## 4. Self-Validation Checklist

- [ ] Every expectation addresses a concrete problem.
- [ ] Every persona connects to at least one problem/expectation and functionality.
- [ ] Every PBI traces to a functionality and delivers observable user/business value.
- [ ] Zero architecture, database, or code implementation details appear in the backlog.
- [ ] All unconfirmed business rules are isolated in `Assumptions` or `Open Questions`.
