# Investigation protocol

## JSON export

`python "<mapper>" . export --output map.json` streams the published SQLite tables to a new file inside `.project-mapper/`. It never overwrites an existing file. SQLite remains authoritative; editing the JSON does not change the graph. The export includes snapshot metadata, graph, semantic discoveries, evidence, inventory and coverage. It contains the graph's stored content, including accepted findings; review before sharing.

Add `--dimension NAME` to select matching memberships, all edges incident to those nodes, their endpoints and unresolved candidates, plus supporting evidence. The selection identifies this one-hop scope; inventory, metadata, tasks, coverage and discrepancies remain global. No result for a dimension means the export is rejected. Output is a snapshot; regenerate after changes. JSON-valued SQLite columns are represented as JSON values and other fields retain their SQLite values. The command checks SQLite integrity but does not replay semantic claims against the source; use `verify` separately when needed.

## Multidimensional map

Start with `python "<mapper>" . map --commit HEAD` (or `--worktree`). The command inventories the snapshot and publishes `.project-mapper/graph.sqlite` plus its README. It reads source without running target code. `search` returns structural node candidates as well as discoveries, `node KEY` shows evidence and adjacent relationships, and `trace KEY` traverses them. Start with `coverage --summary` and `dimensions --summary`; use `coverage --area PATH` for details before interpreting missing results.

The JavaScript/TypeScript profile uses lexical recognition, not an AST or type checker: imports, symbol definitions, configuration properties and tool-like objects are candidates, and a resolved file target does not establish runtime execution. It does not resolve calls or construct a complete MCP-to-service flow; investigate those relationships. The configuration profile covers selected package, MCP, Wrangler and GitHub Actions declarations. The existing Python AST profile is also included. The map does not determine deployed state or store arbitrary configuration values. See the recorded profile and coverage for exact limitations and unhandled inputs. A submodule is a boundary, not an indexed repository.

## C# profile

Install the optional parser into the same Python environment that runs the mapper: `python -m pip install -r "<skill>/scripts/requirements-csharp.txt"`. Then run `python "<mapper>" . map --commit HEAD --csharp` (or `--worktree --csharp`). Exact pinned parser versions are part of the recorded profile and are required again for replay and verification. If they are unavailable, this command fails before creating a run; ordinary maps remain available without the optional packages.

The parser reads C# syntax and project XML without building or executing the target. It indexes type and method declarations, constructor type references, syntactic calls, common HTTP attributes and minimal API declarations, selected dependency-injection registrations, configuration-key candidates, test attributes and project/package references. Project inclusion, type binding, calls, dependency injection, routes, MSBuild conditions, conditional compilation, generated code, reflection and deployed behavior are not resolved. HTTP templates are only literal fragments; compose and validate full routes against source. Coverage stays partial and candidate relations are not runtime claims.

Existing static profiles remain readable and verifiable. A C# map cannot replace an active semantic investigation. To retain reviewed work, create a separate checkout of the exact same snapshot, publish its C# static map, and run `python "<mapper>" <new-checkout> import-run --source-repo <old-checkout> --source-run RUN`. The command verifies both maps and replays the old accepted evidence against the source, checks graph identities and composition, then copies the old plan, decisions and shards into a new target run. It adds assignments for newly found C# nodes and leaves the original run and graph untouched. If the source changes while copying, the command rejects the attempt. `check-plan` and review the entire resulting plan, then publish and verify it normally. Imported evidence remains subject to its original semantic limitations. Inspect other unassigned nodes and extend the plan where needed. Do not delete or overwrite the prior run to bypass the active-map protection.

To add reviewed semantic findings, run `investigate --from-graph` on the same snapshot **after** publishing the multidimensional map. Publication composes the static facts and accepted discoveries; `verify` replays both. An investigation started without `--from-graph` retains its original standalone behavior. The mapper protects an active investigation from replacement by a static-only rebuild on the same snapshot.

## Graph-derived plan

Run `python "<mapper>" . investigate --commit REV --from-graph` using the published map's exact revision (or `--worktree --from-graph` for its unchanged worktree). The mapper checks and replays that graph once, derives `plan.json` from its node IDs and saves `graph-plan.json` as an informational coverage report. Per-unit limits bound the assigned inputs without imposing a repository-wide task limit. Directory-based areas are scheduling buckets, not architectural claims. Nodes can appear in multiple units; unreadable inputs, submodules and nodes without usable source paths remain explicit boundaries or gaps.

Use `check-plan RUN --summary` for counts and fingerprint, `check-plan RUN --list --offset 0 --limit 50` for paginated units and progress, and `check-plan RUN --question ID` for one complete assignment. Review all authored questions, including unanswered ones, before confirming the fingerprint; the summary alone does not constitute that review. Group independent units by area or another evidence-based work split and use `worker-prompt RUN ID --also ID2` to dispatch them together. Each unit still owns its own shard and review decision.

The worker begins with `graph-unit RUN ID --summary`, then pages its nodes and edges with `--node-offset`, `--node-limit`, `--edge-offset` and `--limit`, and follows `node`/`trace` plus source reads. Pass the first response's graph fingerprint as `--expect-graph` on subsequent pages; if publication changed the graph, restart pagination from the new generation. A graph fingerprint binds the assignment to the verified graph; unexpected graph changes block the assignment. Publishing accepted results can advance the pin for the same run. Review `graph-plan.json` for unassigned inputs and frontier truncation. The plan and previews are not semantic coverage: complete a unit only to the extent supported by its sources.

## Semantic context

Semantic investigation is part of the default mapping workflow. Group related files and symbols into components and concrete flows rather than generating an ungrounded description for every file. Cover the repository's detected entrypoints, major modules, configurations, integrations, infrastructure and tests, and trace their important cross-boundary connections. Dispatch independent assignments in parallel where available. Publish supported results progressively; explicitly report areas without reviewed context.

For each investigated component or flow, create a discovery with a concise title and summary and content appropriate to the evidence: its role, entrypoints or callers, relevant inputs and outputs, dependencies, conditions, related tests and known gaps. Omit fields that cannot be established. Attach source ranges to the supported content fragments. Add an evidenced `describes` claim from that discovery to each relevant structural node, and explicit claims for verified flow relationships. A single flow discovery can contextualize several nodes, but its role is not automatically the role of each node. For node-specific roles, create a discovery with `content.subject_node` equal to the exact node ID and a nonempty `role`, support both fields with source locators, and link it to that node. Do not claim a component's purpose, test coverage or deployed state from path names or imports alone.

Use `node KEY` to find linked context and `open DISCOVERY_ID` for its content and supporting locators. The node projection distinguishes `field_scope=node` from context belonging to a shared discovery, and reports `node_role_status` separately. No linked discovery means context is not available at that node; it does not prove that no information exists elsewhere. `check-plan --summary` and `graph-unit --summary` count published, unconditionally linked node-specific roles separately from assigned nodes without one; accepted but unpublished and conditional roles do not count. Neither those counts nor an answered unit measure semantic completeness. Report structural and semantic coverage separately; do not declare a complete semantic map while planned questions or important areas remain unexamined.

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

When a question needs specific relationships, add an optional `required_relations` list to its plan entry. Describe what must be traced, including direction or conditions that matter. Leave the answer open. The worker's read-only preflight shows proposed claim mappings and any unmapped requirements. During review, reopen each witness and check the correspondence, including any stated gaps. Changing a requirement changes the question fingerprint.

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

Translate a non-English question into English search terms. Use the original spelling for source identifiers and exact names. Search returns compact discovery candidates and, on multidimensional maps, matching structural nodes. Open a discovery by exact ID, or use `node KEY` for a structural node, then follow relations and inspect supporting locators. `dimensions` lists evidenced memberships. On an empty result, inspect coverage before inferring absence.

## Optional Python baseline

`build --commit REV`, `build --worktree` and `prepare [--agent-review]` remain available for static Python analysis of regular packages, supported imports, direct function calls and root pyproject declarations. Legacy review flags signals. Use `hints` inside an investigation to consult this extractor without replacing the graph. Older schema-compatible SQLite files remain inspectable. Static replay requires the recorded profile and a compatible interpreter.
