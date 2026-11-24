# Forge planned execution

Read this reference only after selecting planned mode. Apply the common project and procedure rules in SKILL.md.

Sections: task contract, state and DAG, preflight, RED, GREEN, builder audit, evidence handoff, reporting and contract commands.

<task_contract>
When `context.sqlite` exists, obtain Blueprint's `export-forge` JSON for its
current rendered scope and publish that projection through this skill's `plan`
contract operation. It records the Blueprint revision and database SHA-256;
`plan`, `build` and Quality Gate `check` reject a changed source or altered
task definitions. The projection keeps prior evidence and restarts tasks when
replanned. Reconcile a changed scope or QA contract with Blueprint before
execution. Existing `tasks.json` plans without a Blueprint database remain
supported. Each implementation task defines:
```json
{
  "id": "T1",
  "kind": "implementation",
  "project_path": "/absolute/project/root",
  "description": "Expected behavior",
  "technical_steps": ["..."],
  "acceptance_ids": ["A1"],
  "files_allowed": ["src/module.py", "tests/test_module.py"],
  "unit_tests": {
    "files": ["tests/test_module.py"],
    "command": "python -m unittest tests.test_module"
  },
  "depends_on": [],
  "status": "pending",
  "phase": "red_pending"
}
```
- `unit_tests.files` is a nonempty array of project-root-relative paths, each covered by `files_allowed`. `unit_tests.command` is a focused, nonempty runner command executed with cwd=`project_path`; it must target the mapped tests. Do not silently broaden it to full integration/E2E suites.
- At least one production path MUST be authorized separately from tests. A test file may exist or be listed in task `planned_files`; legacy plans may declare it as `[NEW]` in `SCOPE.md`. Neither broad globs nor unspecified paths authorize additional edits.
- Legacy specs without `unit_tests` or `phase` are NOT test-ready: halt before editing and request regeneration/amendment through `blueprint`. Do not silently fabricate tests or widen `files_allowed`.
- For legacy tasks without `kind`, default to implementation. For `kind: "evidence"`, require nonempty `qa_ids` and `evidence_checks` plus explicitly authorized paths for any edits. Evidence tasks begin at `evidence_pending`, bypass RED/GREEN and may edit only mapped test or fixture files. An existing check can run without writes. Production instrumentation must be planned separately as an implementation task.
- Checks on implementation tasks execute after GREEN and may only run existing or mapped checks without editing tests. For both task kinds, ensure `evidence_checks[].qa_ids` resolve to obligations in the current `qa.json.contract`.
- If a plan supplies `scope_revision`, verify it against SHA-256 of the exact `SCOPE.md` bytes. When a QA contract exists or the plan references one, verify the QA contract’s change ID, its scope revision and the plan’s `qa_revision` against the canonical digest of `qa.json.contract`. Require reconciliation if a contract was added after an uncoupled plan was created, or if a QA-coupled plan loses its contract. Verify revisions again before evidence execution and final reporting. Report stale inputs and defer affected execution until reconciled. Legacy plans missing change_id or scope_revision must be reconciled by Blueprint before execution.
</task_contract>

<state_and_dag_tracking>
- Supervisor is the sole writer of state fields; preserve everything else and reparse JSON after each write.
- Phases: `pending/red_pending` -> `in_progress/red_pending` -> `in_progress/green_pending` -> `completed/completed`, or `failed`.
- Persist `green_pending` immediately after verified RED and freeze tests. On crash, reset `in_progress` to `pending` without losing phase or attempts. For `green_pending` resume, rerun tests: expected failure permits GREEN; already green requires code/scope audit and final GREEN verification; unrelated failure blocks.
- Ready tasks are pending with all `depends_on[].task` completed (accept historical `done`). Dispatch sequentially.
</state_and_dag_tracking>

<execution_protocol>

### 0. Preflight
1. Validate `SCOPE.md`, parseable tasks JSON, unique IDs, acyclic DAG, absolute existing project roots, test mappings, allowed paths and states. Verify `blocked_tasks` IDs are disjoint from executable tasks and absent from their dependency lists; execute only the ready tasks and report outstanding blockers. Never edit QA or scope files.
   For a Blueprint-bound plan, verify its source binding and inspect affected
   task nodes, blockers and source references. The contract checks identity and
   task fields, not whether the assertions or source interpretation are correct.
2. Read `<project_context>`, verify targeted unit runner command and optional build/typecheck `smoke_command`; reject unavailable/unsafe commands.
3. Check mapped existing tests for preexisting failures and halt if found; missing-file errors for planned `[NEW]` tests do not count as RED.
4. Snapshot working-tree files (paths, mtimes, optionally hashes) excluding `.git`, dependencies and caches to audit actual writes, not only builder claims.
5. Resolve provider dispatch rules from skill sync; never guess missing placeholders:
Use the provider dispatch policy supplied in SKILL.md.

### 1. RED: Test-first dispatch
For `phase=red_pending`, mark `in_progress`, then dispatch a RED-only builder with task, context and mapped test paths/command. It inspects task-specific source and tests first, writes ONLY `unit_tests.files`, and runs the exact focused command from `project_path`.
Supervisor must inspect results and filesystem changes. RED passes only if tests fail due to a missing acceptance behavior (assertion failure), NOT syntax/import, collection, tool, or baseline failures. Validate all writes against both test paths and `files_allowed`; if failed or unexpectedly green, do not dispatch GREEN. Persist `phase=green_pending` upon verified RED; tests become frozen.

### 2. GREEN: Minimal production implementation
Dispatch GREEN-only builder after verified RED; edit ONLY allowed production files, never tests. Run SAME `unit_tests.command` (must exit 0), then `smoke_command` if non-null (must exit 0). Audit before/after paths and outputs; execute any mapped evidence checks before setting `phase=completed`, `status=completed`, clearing `error`.
On failure retry GREEN once, changing production only. Second failure or RED/scope/environment blockers mark `failed` and halt; preserve disk state and report paths without rollback.

### 3. Inline builder contract
Use a prefix-stable prompt: (A) static rules below, (B) project context and full task definition, including `unit_tests`, `files_allowed`, `smoke_command`, (C) current phase and previous diagnostic only on retry.

```text
You are the forge builder for ONE task and ONE phase in the user's working tree.
ZERO GIT: no git commands. Use the supplied project orientation and inspect task-specific source/tests. If orientation is missing, stale or contradicted, reopen project docs starting at docs/README.md when available.
STRICT WRITES: only files_allowed may change; in RED only unit_tests.files may change; in GREEN never change unit_tests.files. Reject absolute/parent-traversal/symlink paths and stop if more files are necessary.
RED: write meaningful unit tests first, run exactly unit_tests.command, and report the expected behavior/assertion failure (nonzero). Do not edit production code.
GREEN: do not edit tests. Apply the smallest production change, run exactly unit_tests.command to pass, then the specified smoke_command if provided.
Never weaken assertions, skip tests, ignore exit codes or create QA artifacts.
Return ONLY a JSON object inside <fast_result> tags:
<fast_result>
{
  "protocol": "fast.builder.result.v2",
  "task_id": "<id>",
  "phase": "RED | GREEN",
  "status": "COMPLETED | BLOCKED",
  "files_touched": ["relative/path"],
  "unit_test": {"command": "<exact command>", "exit_code": 1, "diagnostic": "<concise result>"},
  "smoke": null,
  "blocker": null
}
</fast_result>
In RED unit_test.exit_code MUST be nonzero due to expected behavior; smoke is null.
In GREEN unit_test.exit_code MUST be 0; smoke is null or {"command":"...","exit_code":0}.
For BLOCKED include blocker {"code":"OUT_OF_SCOPE|TEST_FAILURE|ENVIRONMENT_ERROR|SMOKE_FAILURE","diagnostic":"...","attempted_path":null}.
```

### 4. Independent supervisor audit
Validate result protocol, task ID, phase, command equality and exit codes; malformed response gets JSON-only re-emission without rerunning changes. Diff pre/post filesystem inventories (including deleted/generated files), independent of `files_touched`. Enforce phase-specific writes, inspect RED diagnostic rather than trusting nonzero, and require GREEN test and smoke success. Record blockers/path breaches in `error`, mark failed and halt without rollback.

### 5. Evidence tasks and handoff

Resolve each check's QA IDs and compare the procedure with the obligation. Use dependency-ready evidence tasks at `in_progress/evidence_pending`; transition to completed only after their checks succeed. Preserve failed state and partial observations. Reconcile legacy checks without IDs through Blueprint before formal execution.

For every check, persist a start event before executing it. Capture the actual target candidate (verified artifact or content fingerprint including relevant code, tests, fixtures and configuration) and effective environment identity (running version, configuration and fixture identity where material, with no secrets). On timeout or restart, reconcile external effects using the original correlation reference before considering any retry. Reconcile an unfinished attempt with its eventual observation or an inconclusive result before repeating a procedure with effects.

After execution, verify candidate and environment again, and append the result regardless of sibling checks. After all candidate-changing writes, run the formal checks on the final candidate. Reuse an observed result from the current execution or its resume only with matching check definition, candidate, QA revision and effective environment, and applicable scenario isolation. If any identity or observation is unavailable, report the gap; require a fresh run when appropriate. Route missing check mappings to Blueprint and ambiguous obligations to Quality Gate plan. Leave the verdict to Quality Gate check.

### 6. Final report
Report overall completion as partial whenever `blocked_tasks` or unresolved QA evidence remains. Report per-task `ID`, title, status, phase, mapped unit test files, RED diagnostic, GREEN test result and optional smoke result; list all touched paths including partial edits. Report the execution mode and any evidence produced with its candidate identity. Describe only work that actually completed. Do not claim tests passed on a halted task.
</execution_protocol>

## Contract commands

Run the bundled `contract.py` next to this SKILL.md with Python 3.9+.
Pass the absolute `docs/specs/<change_id>` directory as the first argument.
Run `inspect` to obtain `scope_revision`, `qa_revision` and destination digests.
For updates run the designated operation with `--expect <destination_digest>`
(or `--expect absent` for a new file), supplying the proposed JSON on stdin.
Use the digests from before analysis. If the destination changed, reread and
reconcile before retrying. Use the script for every task or QA contract write.
When no Blueprint database exists, Quality Gate plan may use `scope --expect
<scope_revision-or-absent>` to create or revise the shared scope. Otherwise
Blueprint renders the scope from its own database.
Declare each material risk on its own Markdown line or table row beginning
with its `R<number>` ID.
The QA revision hashes canonical JSON of `qa.json.contract`; assessments do
not alter that revision. The destination digest covers the entire target file.
A flat legacy qa.json must be republished through Quality Gate plan and any
dependent tasks plan reconciled before execution.

Use `build` with the proposed full tasks document. Preserve prior evidence and task definitions. Append events under `evidence` using separate writes:

- **Before execution:** append `event: "started"` with unique `id` (the attempt ID), `task_id`, `check_id` (the check's `id`), `definition: {"cwd": "<project_path>", "check": <exact planned check>}`, `definition_digest`, `qa_revision`, `candidate` and `environment`. Compute the definition digest using the same canonical JSON hash as the QA revision (`contract_digest` in the helper). Include the operation correlation reference when external effects are possible. The task must already be in progress or completed for a final-candidate rerun.
- **After execution or reconciliation:** append `event: "result"` with its own unique `id`, `attempt_id` referencing the stored start, `status` (`observed` or `inconclusive`), `candidate_after`, `environment_after`, `artifact_ref` and the observations. For observed results, include integer `exit_code`, `test_refs`, `assertions` and `observed_values`; before/after candidate and environment must match. For inconclusive results, record the diagnostic and reference the timeout log, reconciliation trace or other available artifact. Cite result IDs in the handoff.
