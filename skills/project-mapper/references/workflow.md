# Investigation protocol

## Orient

Set `<mapper>` to the absolute path of `scripts/project_mapper.py`. Pass the target Git root as its first argument. The initial `investigate` command returns the run ID and paths of the inventory, plan, decisions and shards directory. Before adding questions, use `@` as the reader's question ID.

```text
python "<mapper>" . read-input RUN @ package.json --start 1 --count 30
python "<mapper>" . search-input RUN "dotnet test" --glob "*.ps1" --limit 10
```

Search is case-sensitive and returns locators, skipped unreadable inputs and a truncation flag. Repeat `--glob` to search multiple patterns. Open a match to see its meaning. Consult optional `hints RUN path.py` when an AST would help.

Commit mode reads Git blobs. Worktree mode includes tracked files and eligible untracked files under Git's standard excludes, records deletions and fingerprints bytes. Both modes exclude mapper output and treat links and submodules as boundaries. When worktree bytes change, start a new run.

## Plan and resume

Preserve the initial snapshot identity in `plan.json`. Record the question this repository raises, its seed paths and any prerequisites. Use the smallest set of questions that can explain the requested behavior. Give each question a stable lowercase slug and use `depends_on` where acceptance relies on an earlier finding. Inspect existing questions, shards and decisions before resuming the same run.

```json
{"snapshot":"<identity>","questions":[{"id":"launch","question":"Which executable does the E2E command invoke?","seeds":["package.json"],"depends_on":[]}]}
```

## Dispatch

```text
python "<mapper>" . worker-prompt RUN launch
python "<mapper>" . worker-prompt RUN launch --repair "The cited condition includes backend B. Recheck its registration."
```

Pass the returned `prompt` string verbatim to a worker with access to those paths. The [worker contract](worker.md) is the reusable prefix. The command appends the active assignment in deterministic key order and a diagnostic only on repair. Use the same skill version for retries. The same assignment can run locally. A worker returns a pointer and any follow-up lead. A missing shard remains unexamined. For a recoverable failure, retry the same assignment with the specific diagnostic. If the same blocker persists, record the gap and continue the independent questions.

## Review and publish

```text
python "<mapper>" . check-shard RUN launch
python "<mapper>" . accept RUN launch FINGERPRINT
python "<mapper>" . publish RUN
python "<mapper>" . verify
python "<mapper>" . coverage --family investigation
python "<mapper>" . trace "command:npm:e2e" --type invokes --direction out
```

`check-shard` validates ownership, endpoints, snapshot bytes and ranges. Before `accept`, reopen decisive lines. Check that they establish origin, destination, direction and the stated condition. A literal command can support an edge at one site. Across services, verify that producer, registration and consumer refer to the same channel **and** transport namespace. Look for a same-name alternative, override or feature flag that would reverse the conclusion. For an absence, identify what closes the search within its stated scope. Two documents repeating one source count as one basis.

Reconcile qualified names and types across workers. The `member-of` relationship also populates `dimensions`. Accept prerequisite decisions before dependents. An accepted partial prerequisite still has a gap: corroborate the dependent claim separately or carry that gap forward. A changed question, shard or prerequisite decision requires fresh review. Adding an independent question preserves existing decisions.

`publish` compiles accepted shards and records open questions in `.project-mapper/graph.sqlite`. A complete graph for the same snapshot and plan survives a partial retry. `verify` replays accepted records and checks locators. The supervisor is responsible for semantic judgment. Inspect `coverage --area QUESTION_ID` for the question outcome and discrepancies. `complete` describes the questions in this plan. File counts distinguish cited and uncited inputs. Use `node KEY`, `trace KEY` or `dimensions` for navigation.

## Optional Python baseline

`build --commit REV`, `build --worktree` and `prepare [--agent-review]` remain available for static Python analysis of regular packages, supported imports, direct function calls and root pyproject declarations. Legacy review flags signals. Use `hints` inside an investigation to consult this extractor without replacing the graph. Older schema-compatible SQLite files remain inspectable. Static replay requires the recorded profile and a compatible interpreter.
