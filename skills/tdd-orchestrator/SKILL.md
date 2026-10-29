---
name: tdd-orchestrator
description: Supervise the tasks.json DAG through tdd-maker batches, candidate diff validation, and adversarial-qa gates in persistent detached worktree slots. Own task state and bounded rework; never implement production code.
---

# TDD Orchestrator

Coordinate `tdd-orchestrator -> tdd-maker -> adversarial-qa`. Maker owns construction; QA owns verdicts. Supervisor owns scheduling, Git handoffs, and `tasks.json`.

## 1. Inputs and authority

1. Read `docs/README.md`, `docs/adr/ARCHITECTURE.md`, and `docs/adr/TESTS.md`. Route relevant features through `docs/.graph.json` and their micrograph's `entrypoints`, `registration_files`, `reference_files`, `code_files`, and `test_files`. Check stale paths against source. If docs are absent, inspect build/test configuration and report the fallback.
2. Resolve `${change_id}` and canonical `docs/specs/${change_id}/{SCOPE.md,tasks.json,qa.json}`. Require all three; never invent a missing DAG or verification contract.
3. Validate change IDs, SCOPE SHA-256 hashes, single-repository `project_path` target, unique task IDs, acyclic dependencies with reasons, acceptance links, allowed construction/test paths, and discovered commands. Stop on multi-repo or incompatible contracts.
4. Read `qa.json` for gates and budgets. Never author or weaken its invariants, metrics, budgets, findings, or verdicts. Import only validated QA output as described below.

**PROHIBITED:** Write production code, construction tests, or QA harnesses. Delegate construction to `tdd-maker`. Stop if isolated agent execution is unavailable.

## 2. Two persistent worktree slots

Use exactly two persistent worktrees per change: `maker-slot` and `qa-slot`. Keep canonical control artifacts outside slots. Allow one active batch and one owner per slot; never run competing supervisors.

1. Record named target branch and `accepted_oid`. Require no unrelated changes. Preserve existing specification edits outside Maker commits.
2. Resolve the absolute common directory with `git rev-parse --path-format=absolute --git-common-dir`. Place slots under its `triad/${change_id}/` directory, outside tracked sources. Inspect `git worktree list --porcelain` before creating or reusing paths.
3. Create missing slots with `git worktree add --detach <slot-path> <oid>`. Before reuse, stop/join the previous worker and its known processes; verify resolved path, repository identity, and exclusive ownership.
4. Before `git switch --detach <oid>`, preserve evidence and require a clean slot. Remove only generated artifacts recorded by that run. Use `git reset --hard <previous-oid>` only for verified run-owned tracked edits in that slot. Stop on unknown edits/files. Never clean the operator's worktree, kill unrelated processes, or use blanket `git clean -fdx`; retain ignored dependency caches.
5. Verify `git rev-parse HEAD` equals the requested OID and `git symbolic-ref -q HEAD` reports no branch. Retain slots and candidate refs after success or exhaustion.

Persist `execution` in `tasks.json` (`{target_branch, accepted_oid, batch_id, batch_base_oid, dispatch_base_oid, task_ids, candidate_oid, candidate_ref, phase: "planning|making|evaluating|checking|rework|integrated|blocked", retry_limit, retries_used}`) before every state transition or dispatch. Resume by checking OIDs, refs, tasks, and slot ownership; never reset counters. Recover interrupted integration by checking whether `candidate_oid` has a persisted QA PASS and target HEAD already equals `candidate_oid` before marking batch tasks `completed` and updating `accepted_oid`; if target HEAD advanced past `candidate_oid`, stop on external branch movement rather than silently adopting untested commits.

## 3. Batch dispatch to tdd-maker

1. Default to one batch containing all remaining DAG tasks in topological order, executed sequentially in Maker slot. QA runs its full global contract: use a smaller batch only if it can already satisfy every required gate. Never report pending functionality as a defect or filter away mandatory gates to approve a partial batch.
2. Set `batch_base_oid = accepted_oid`. Rework starts from the previous candidate, retaining the batch base for cumulative checks. Mark dispatched tasks `in_progress`; reserve `completed` for integrated, QA-approved tasks.
3. Invoke fresh isolated `tdd-maker` with change/batch IDs, slot path, dispatch base OID, relevant SCOPE, selected tasks, architecture/test guidance, and construction commands. Include `files_allowed`, `red`, `contract_delta`, acceptance IDs, and dependencies. Never inherit supervisor conversation containing `qa.json` or pass its contents. Translate defects into construction tasks without exposing the Judge's contract.
4. Require one commit per task, final immutable `candidate_oid`, ordered task-to-commit mapping, RED/GREEN/REFACTOR commands with exit codes, and blockers. Workers never edit canonical task state.

## 4. Candidate validation and QA handoff

1. Verify returned OID exists, equals Maker HEAD, and descends from dispatch base. Require a clean slot, no merges, and task mapping for every new commit.
2. Inspect each task commit with `git diff-tree --no-commit-id --name-status -r -z --no-renames <commit>` and cumulative `git diff --name-status -z --no-renames <batch-base-oid> <candidate-oid>`. Parse NUL-separated paths. Check additions, deletions, type changes, and both sides of moves. Check each commit against its task's `files_allowed`, then cumulative changes against the batch's authorized scopes; a union-only check cannot prove per-task confinement.
3. Match repository-relative, slash-normalized, case-sensitive globs: `*`/`?` stay within a segment; `**` spans segments. Reject absolute paths, `..`, symlink escapes, Git internals, SCOPE/task/QA control files, and QA-owned harnesses. On a partial batch or scope violation at commit $k$, quarantine invalid commits, reset the owned Maker slot to the last valid ancestor (`commit_{k-1}` or `dispatch_base_oid`), update `dispatch_base_oid`, and redispatch only remaining unbuilt tasks, charging a retry. Never extend an invalid chain or expand permissions.
4. Pin each candidate using `git update-ref refs/triad/candidates/<change_id>/<batch_id>-<attempt> <candidate-oid>`. Never move an existing candidate ref to a different OID. Record the ref before switching QA to that OID.
5. Prepare `qa-slot` detached at the candidate. Copy canonical `SCOPE.md`, `qa.json` (including prior findings/verdicts), and any preserved QA harnesses/reproducers from `<git-common-dir>/triad/${change_id}/qa-harnesses/` into `qa-slot` at their recorded relative paths as controlled overlays. Do not overlay task state. Record all overlay paths for cleanup; never commit them into the candidate.
6. Invoke independent `adversarial-qa` with QA slot, change ID, candidate OID, batch base OID, and `git diff <batch-base-oid> <candidate-oid>` as attack surface; detached working-tree diffs are empty. Supply an execution checklist: rerun or verify recorded gate evidence for all prior `rework_queue` items (`open` and `resolved`), run every invariant/metric `eval_command`, check exit codes, `assert_regex` and targets, honor budgets/mock policies, and record evidence or an explicit unavailable metric reason. Manual gates need recorded acceptance evidence. Require the evidence with the verdict; unexecuted required gates block integration. QA owns harness/QA-overlay writes, never production, task, or SCOPE writes.
7. Collect verdict and QA overlay. Verify QA HEAD still equals the candidate, production/SCOPE/task files remain unchanged from handoff, and QA contract fields match the supplied input. Accept only `snapshot_ref`, appended `verdicts`, and evidence-backed `rework_queue` changes. Import those QA-authored results into canonical `qa.json`, preserving history and all other fields. Archive new or updated QA harnesses, reproducers, and manifest paths into `<git-common-dir>/triad/${change_id}/qa-harnesses/` before slot cleanup so subsequent runs restore them cleanly.
8. Require matching snapshot OID, new run ID, required gate evidence, and zero open blocking findings for PASS. Stale/missing output or timeout blocks integration. Never manufacture PASS or resolve findings.

## 5. Rework and retry budget

- For each open blocking code/metric `RW-*`, append one task with next unused `T*` ID, exact finding ID as `origin`, acceptance IDs, description, `contract_delta`, dependency reasons, allowed paths, and unit/narrow integration `red`. Redispatch only open-finding repair tasks over the validated candidate; leave original batch tasks out. Dependencies present in that candidate satisfy dispatch while original tasks remain `in_progress`. For non-code blockers (missing `manual_gate` acceptance or external QA runner failure without a code defect), do not fabricate a Maker RED task: request operator acceptance or re-run QA on the same candidate OID, keeping integration blocked until QA resolves the finding. Reuse repair tasks; only QA resolves findings by rerunning reproducers or verifying recorded gate evidence.
- Keep repairs inside original authorized scope; otherwise stop for scope refinement. Keep QA harnesses separate from Maker regressions.
- Freeze the batch retry limit before initial dispatch: use top-level `qa.json` `budget.max_retries` if present; otherwise take the minimum `budget.max_retries` among blocking invariants, defaulting missing values to 2. Require nonnegative integers. The limit counts additional Maker attempts after the initial attempt; `0` permits only the initial attempt.
- Persist `retries_used` before every redispatch, including construction failures and rejected diffs. QA retries never replenish Maker attempts. On exhaustion, missing evidence, or unsafe state, stop with blocked tasks and exact unresolved findings/refs.
- Failed candidates stay outside the target branch. Rework extends the latest candidate and repeats cumulative scope validation and QA on the new OID. An earlier PASS never approves later commits.

## 6. Integration and completion

1. After PASS, recheck candidate ref/OID and target branch HEAD equals `batch_base_oid`. If target advanced, stop and rebuild/revalidate from its new base; never rebase, cherry-pick, or merge an untested result.
2. Require no unrelated changes in the target worktree. Integrate on the recorded branch using `git merge --ff-only <candidate-oid>`. Never auto-stash, force-update branches, or commit unrelated specification edits.
3. Confirm target HEAD equals the approved OID, then mark batch and verified rework tasks `completed` in canonical `tasks.json`. Persist `accepted_oid` and integration phase. Keep supervisor metadata out of candidate commits; never advance target HEAD with metadata commits during a batch.
4. Repeat for remaining DAG tasks. Finish only when all tasks are completed and the latest integrated candidate has a matching QA PASS with no open blocking findings. Report OIDs, construction evidence, verdict, advisories, and blockers without claiming unexecuted checks.
