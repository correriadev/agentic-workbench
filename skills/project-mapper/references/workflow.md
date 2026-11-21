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

Preserve the initial snapshot identity in `plan.json`. Keep `output_language` set to `en`. Write each question in English, including questions suggested by local-language documentation. Record the question this repository raises, its seed paths and any prerequisites. Use the smallest set of questions that can explain the requested behavior. Give each question a stable lowercase slug and use `depends_on` where acceptance relies on an earlier finding. Inspect existing questions, shards and decisions before resuming the same run.

```json
{"snapshot":"<identity>","output_language":"en","questions":[{"id":"launch","question":"Which executable does the E2E command invoke?","seeds":["package.json"],"depends_on":[]}]}
```

## Dispatch

```text
python "<mapper>" . worker-prompt RUN launch
python "<mapper>" . worker-prompt RUN launch --repair "The cited condition includes backend B. Recheck its registration."
```

Pass the returned `prompt` string verbatim to a worker with access to those paths. The [worker contract](worker.md) is the reusable prefix. The command appends the active assignment in deterministic key order and a diagnostic only on repair. Use the same skill version for retries. The same assignment can run locally. A worker returns a pointer and any follow-up lead. A missing shard remains unexamined. For a recoverable failure, retry the same assignment with the specific diagnostic. If the same blocker persists, record the gap and continue the independent questions.

## Review and publish

For operational findings, reopen the producer and consumer under each material entry point. Check whether a deployment claim has evidence beyond a runnable command. Review the entire plan and shard for credential values before acceptance: the database embeds the accepted records. After publication inspect the embedded records and generated files as well as the reader-facing discoveries. Source readers can return raw lines; use credential names and locators in review messages.

```text
python "<mapper>" . check-shard RUN launch
python "<mapper>" . accept RUN launch FINGERPRINT --reviewed-english
python "<mapper>" . check-plan RUN
python "<mapper>" . publish RUN --reviewed-english-plan PLAN_FINGERPRINT
python "<mapper>" . verify
python "<mapper>" . coverage --family investigation
python "<mapper>" . trace "command:npm:e2e" --type invokes --direction out
```

`check-shard` checks the envelope, pointers and source ranges. The supervisor checks the assigned question and shard for English before using `--reviewed-english`. Inspect nested keys and values, relationship conditions, terms and gap messages. Return mixed-language authored material to the worker with an English repair. When translating an authored key or ID, update every JSON Pointer and cross-shard link that refers to it. Preserve exact source identifiers and their original locators. Reopen each decisive range. Ask what would change the answer if a value were absent, an override applied or a different consumer ran. For a field transformation, follow origin, conversion and destination. For a cross-service link, check producer, registration, consumer and transport namespace. Two documents repeating one source count as one basis.

Judge the content against the question. For example, a subtitle discovery might contain `{"missing_translation":"use original","null_translation":"suppress"}` with separate support for each branch. Another node might hold a complete wire contract. Use the content structure that preserves each finding. Group facts under one pointer when the same lines support them all. For keys containing `/` or `~`, encode them as `~1` or `~0` in a JSON Pointer. An array index identifies an element in this revision.

Reserve colon-qualified keys for existing endpoints. Give each discovery one defining shard and an ID independent of its title. Workers can describe the same evidence differently. Compare scope, conditions and consequences before consolidating overlapping findings. Retain separate identities for homonyms. When the manual and implementation differ, preserve both attributed statements and their locators. Identify what would resolve the disagreement. For a scoped absence, inspect the places that could supply an exception.

Use claims for evidenced links between findings, including across shards. A referenced opaque ID needs an accepted defining shard by publication. `member-of` indexes the target ID as the group in `dimensions` under `discovery` for a discovery target or the endpoint kind for a legacy target. Accept prerequisites before dependents. A partial prerequisite still has a gap. Corroborate the dependent finding or carry the gap forward. Recheck any changed question, shard or prerequisite decision. An independent new question preserves existing shard decisions.

`check-plan` returns the full plan and its fingerprint. Before publication, the supervisor reads every question and authored ID, including those without a shard. Translate any remaining authored text into English and preserve exact source names. After any edit, check the plan again. Pass the reviewed fingerprint to `publish`, which compiles accepted shards and records open questions in `.project-mapper/graph.sqlite`. A complete graph for the same snapshot survives a partial retry, including when the plan changes. `verify` replays the recorded evidence. `coverage --area QUESTION_ID` reports the outcome and discrepancies. “Complete” applies to planned questions. For a changed snapshot, rebuild and review affected findings against the new sources. Use separate checkouts to retain and compare published revisions. To upgrade an older map, review its findings and rebuild from the pinned sources. An English export must include English headings, field names and descriptions throughout, including embedded plans and accepted shards. Verify the rebuilt database and re-open the export before delivery.

## Query a published map

From the target Git root, with the same mapper path:

```text
python "<mapper>" . search "missing subtitle translation" --limit 5
python "<mapper>" . open ID
python "<mapper>" . trace ID --direction both --depth 2
```

Translate a non-English question into English search terms. Use the original spelling for source-literal searches and exact identifiers. Search returns compact candidates from discovery routing text. If nothing fits, reformulate with a project term. Open a candidate by exact ID, read the pertinent content and its supporting locators, then follow a specific relation to check scope or downstream effects. `node KEY` inspects a graph node and its links, including legacy endpoints. `dimensions` lists evidenced memberships. On an empty result, inspect coverage before inferring absence.

## Optional Python baseline

`build --commit REV`, `build --worktree` and `prepare [--agent-review]` remain available for static Python analysis of regular packages, supported imports, direct function calls and root pyproject declarations. Legacy review flags signals. Use `hints` inside an investigation to consult this extractor without replacing the graph. Older schema-compatible SQLite files remain inspectable. Static replay requires the recorded profile and a compatible interpreter.
