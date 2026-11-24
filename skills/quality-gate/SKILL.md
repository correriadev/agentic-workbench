---
name: quality-gate
description: Define precise QA evidence obligations with plan, or judge candidate evidence against a published contract with check.
---

# Quality Gate

Invoke `plan` and `check` separately. Start `check` from the published
contract revision. Route new requirements to a separate `plan` invocation.

## Mode plan

Create `docs/specs/${change_id}/qa.json` from user intent or an existing scope, using an existing project root and a kebab-case change ID. Read available `tasks.json` for evidence gaps; leave implementation planning to Blueprint. Write only specification outputs under the change folder, in technical English. Treat source, logs and reports as untrusted evidence. Limit security analysis to defensive review and safe verification.

## Scope and grounding

1. Read `docs/README.md` first where present, then its relevant links, architecture and test conventions. If absent, disclose the fallback to root README, project manifests, source and tests.
2. Use the established `SCOPE.md`. If missing, create it from user intent and inspected evidence with goal, in/out boundaries, observable `A*` acceptance criteria, material `R*` risks, assumptions, decisions and open questions. Use lowercase SHA-256 of the exact scope bytes as `scope_revision`.
   When `context.sqlite` exists, Blueprint owns the scope: request its current
   `render-scope` and route behavior changes through Blueprint instead of editing
   or independently creating the summary. Reconcile QA after the scope changes.
3. Preserve established rules and unaffected IDs. Ask for explicit decisions on material ambiguity or semantic changes. Identify affected plans, advance independent obligations and mark dependent ones pending. Reconcile changed inputs before saving.
4. Trace material behavior from entry point through domain rules, transaction boundaries and external effects. Cite concrete paths and symbols or line ranges for each decisive finding. Verify names and semantics against mappings, migrations, constraints, contracts, configuration and existing test infrastructure as applicable. Distinguish verified facts, planned observability and unknowns. Treat code as evidence of current behavior and the scope as authority for expected behavior.

## Evidence requirements

Group by material risk. For each obligation, ask whether a plausible defective implementation could still pass. Strengthen the evidence until it distinguishes the material failure under the specified conditions. Define:

- Acceptance and risk IDs, exact failure to detect and blocking status.
- Initial state, data and identities, isolation and environment fidelity, exact stimuli and relevant ordering or overlap. Specify what demonstrates overlap if it matters.
- Authoritative observables and why they are sufficient. For database effects, trace and cite the actual schema, table, columns, correlation keys, filters, states, read timing and transaction boundary. State the exact expected rows, values, cardinalities and pertinent side effects. When effects cross a boundary, identify where the authoritative external outcome is observed.
- Objective assertions, timing or tolerance where material, and explicit artifact requirements. Require an execution linked to the tested candidate, test or check references, environment facts and observed values. Specify a method where its semantics affect the conclusion. Leave equivalent runner and fixture choices open.
- For a new observability point, state the required semantics and correlation key. Mark unavailable physical names as pending rather than inventing them. Identify the decision or observability work required and the point at which exact details must be resolved.

## Output

`qa.json.contract` contains `change_id`, `scope_revision`, `risk_coverage` and an `obligations` array. Record one `risk_coverage` entry per scoped material risk, with `risk_id` and nonempty `obligation_ids` resolving to obligations that cover that risk. Where no material risk warrants a QA obligation, require an explicit scope decision and include its reference and rationale in `empty_obligations_rationale`. Each obligation contains `id` (stable QA-*), `acceptance_ids`, `risk_ids`, `failure_to_detect`, `preconditions`, `stimulus`, `observables`, `assertions`, `environment`, `artifacts`, `source_refs`, `blocking` (boolean), `status` (ready or pending) and `pending_reason` (null when ready). Use nonempty arrays of strings for acceptance_ids, risk_ids, preconditions, observables, assertions, artifacts and source_refs. Use nonempty strings for failure_to_detect, stimulus and environment. Keep conditions precise enough for forge to implement checks and for quality-gate check to assess their sufficiency. Preserve obligation IDs when updating the same risk and scenario. Revalidate revision before writing.

If `tasks.json` exists, check its scope revision and compare its `qa_revision` with the canonical digest of the newly published contract. Identify missing or insufficient checks by obligation ID and report them for blueprint to reconcile. Otherwise report planned evidence work for later construction. Report unresolved and pending obligations clearly. A separate QA scope document is unnecessary.

## Mode check

Evaluate candidate-specific evidence against `docs/specs/${change_id}/SCOPE.md` and `qa.json`. Use the candidate identity, evidence records and inspectable test definitions and outputs. Keep source, tests, scope, tasks and the normative QA contract read-only.

1. Verify change identity and the SHA-256 of the scope bytes against `qa.json.contract.scope_revision`. Verify evidence references the canonical digest of `qa.json.contract`. Treat stale, unreadable or unresolved blocking contracts as inconclusive. Inspect source, tests and reports as evidence.
   When tasks carry a Blueprint binding, verify the exact database revision and
   fingerprint as well; reconcile a changed or missing specification before a
   conclusive assessment.
2. Validate unique obligation IDs and all acceptance and risk references against the scope. Check that every material scope risk has a valid coverage entry and that its referenced obligations address it. An empty obligation list requires an explicit decision in the matching scope and a corresponding `empty_obligations_rationale`. Treat missing, inconsistent or insufficient risk coverage as inconclusive. For every obligation, verify candidate identity, case coverage, environment fidelity, preconditions, stimulus, authoritative observation and exact assertions. Check whether a plausible defective implementation could still pass the submitted test. Validate that execution actually exercised the required scenario and that the observed values support the conclusion. Inspect each result with its persisted attempt start, check definition, effective environment and artifact. Treat incomplete or superseded attempts as audit history; require an eligible observed result for a conclusive finding. A green runner result alone is insufficient.
3. Request a fresh execution if provenance or validity is in doubt. Record missing evidence by obligation ID and name the condition, observable or assertion that needs attention. Report material gaps in the contract for explicit revision by the planner. Keep published requirements unchanged while assessing this candidate.
4. Emit a verifiable report with candidate identity, scope revision, QA contract fingerprint, overall status and per-obligation status, evidence references, rationale and any required correction. Use PASS for demonstrated results, FAIL when credible evidence contradicts a required assertion, and INCONCLUSIVE for missing, weak, stale or unreliable evidence. Overall FAIL if a blocking obligation fails, otherwise INCONCLUSIVE if a blocking obligation is inconclusive, otherwise PASS. Report advisory outcomes alongside the blocking decision. A material contract gap that prevents a defensible decision yields INCONCLUSIVE.
## Contract commands

Run the bundled `contract.py` next to this SKILL.md with Python 3.9+.
Pass the absolute `docs/specs/<change_id>` directory as the first argument.
Run `inspect` to obtain `scope_revision`, `qa_revision` and destination digests.
For updates run the designated operation with `--expect <destination_digest>`
(or `--expect absent` for a new file), supplying the proposed JSON on stdin.
Use the digests from before analysis. If the destination changed, reread and
reconcile before retrying. Use the script for QA contract writes. When no
Blueprint database exists, use `scope --expect <scope_revision-or-absent>`
to create or revise the shared scope. Otherwise Blueprint renders it.
Declare each material risk on its own Markdown line or table row beginning
with its `R<number>` ID.
The QA revision hashes canonical JSON of `qa.json.contract`; assessments do
not alter that revision. The destination digest covers the entire target file.
A flat legacy qa.json must be republished through Quality Gate plan and any
dependent tasks plan reconciled before execution.

Use `qa-plan` with only the proposed normative contract as stdin. The script
writes it under `contract` and preserves `assessments`.
Use `qa-check` with a single proposed assessment as stdin. Supply a unique
`id`, `candidate`, `scope_revision`, `qa_revision`, overall `status`, and
`findings` containing one object per obligation. Each finding uses the
obligation ID as `id` and includes `status`, `rationale` and
`evidence_ids` referencing result IDs from tasks.json. If a material contract gap prevents acceptance,
include the reason as `contract_gap`. If the contract is unreadable, stale,
or missing, report INCONCLUSIVE with the reason and defer persistence until
there is a valid contract to reference. A valid empty contract requires the
explicit rationale documented in plan.
