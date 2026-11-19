# Investigation protocol

## Orient on the snapshot

Use the path to `scripts/project_mapper.py` in place of `<mapper>`. Commands accept the target Git root as their first argument.

```text
python "<mapper>" . investigate --commit HEAD
python "<mapper>" . read-input RUN @ package.json --start 1 --count 30
python "<mapper>" . search-input RUN "dotnet test" --glob "*.ps1" --limit 10
```

`investigate` creates an unpublished run and returns the paths of its inventory, plan, decisions and shards directory. `@` allows orientation before any questions exist. Search returns literal, case-sensitive matches in snapshot text, their line and content IDs, skipped unreadable files, and a truncation flag. Repeat `--glob` for multiple patterns. Read individual matches before using them. `hints RUN path.py` returns optional Python extraction candidates for that input. Use the same reader for unfamiliar languages and manifests.

Commit mode reads Git blobs. Worktree mode uses tracked files and Git standard excludes for untracked paths, records deletions and fingerprints eligible bytes. Both modes exclude mapper output and keep links and submodules as boundaries. A worker read checks the requested file. Publication checks the complete inventory again. If the worktree changes, prepare a fresh run. Retain the run ID to resume a fixed snapshot.

## Write and extend the plan

The supervisor owns `plan.json`. Preserve the initial snapshot identity. Use a lowercase slug for each stable question ID. Each question has one owner and an independent output at `shards/<id>.json`. Use seed paths from the eligible inventory. A worker can inspect any eligible path relevant to its question. Use `depends_on` when a question's acceptance relies on another answer. Definitions and dependencies can be revised between waves.

```json
{"snapshot":"<identity>","questions":[{"id":"launch","question":"Which executable does the public E2E command invoke?","seeds":["package.json"],"depends_on":[]}]}
```

Use repository-specific questions, such as which adapter a setting selects, how a consumer binds to a particular channel, or what enables report generation. Give a worker the question, pointers, and the expected output path. Independent workers can read overlapping sources. The supervisor alone decides when to expand the plan, reconcile names across shards or close a question. On resumption inspect existing questions, shards and decisions to avoid repeating accepted work.

## Write one worker shard

```json
{
  "snapshot": "<identity>",
  "question": "launch",
  "status": "answered",
  "claims": [{
    "source": "command:npm:e2e",
    "relation": "invokes",
    "target": "file:scripts/e2e.ps1",
    "condition": "",
    "evidence": [{"path":"package.json","content_id":"<ID from read-input>","start":4,"end":4}]
  }],
  "gap": ""
}
```

Read further sources with `read-input RUN launch PATH --start LINE --count COUNT` (1–120 lines per read). Cite the smallest ranges establishing identity, direction and conditions. A literal declaration may establish an edge with one locator. A cross-service registration typically needs the producer, the binding configuration and the consumer. Capture conditions in `condition` and include their source locations. Use vocabulary consistent across the run, such as `invokes`, `consumes`, `writes` and `member-of`. Use distinct namespaces for homonyms. A `file:<path>` endpoint must exist in the eligible snapshot. A `member-of` claim also populates the membership view grouped by target kind and key.

Use `answered` for supported claims. For an examined negative answer, use an empty `claims` array and add `"absence":{"statement":"<what is absent under which conditions>","evidence":[...]}` with the locators that bound the search. Use `partial` for supported facts with a concrete missing link, or `blocked` with no claims and an explicit gap. Leave a question without an accepted shard as unexamined. Record uncertainty or conflict in the gap. Keep credentials and raw payloads out of names, conditions and findings.

## Review and publish

```text
python "<mapper>" . check-shard RUN launch
python "<mapper>" . accept RUN launch FINGERPRINT
python "<mapper>" . publish RUN
python "<mapper>" . verify
python "<mapper>" . coverage --family investigation
python "<mapper>" . trace "command:npm:e2e" --type invokes --direction out
```

`check-shard` checks structure, endpoints, snapshot identity and source ranges. The supervisor inspects the claim and its sources, tests an alternative interpretation, then passes the **exact fingerprint reviewed** to `accept`. Request a corrected shard when the source does not support the proposed relationship. A worker writes only its shard. The acceptance command atomically updates the supervisor's decisions. Accept prerequisites before their dependents. A changed answer, question definition or prerequisite decision requires fresh review. Adding an independent question preserves existing decisions.

`publish` compiles accepted shards, records open questions and atomically promotes the checked database. A previous complete graph for the same snapshot and plan survives a partial retry. `verify` reopens the snapshot, rechecks the locators and replays the accepted records. The semantic judgment belongs to the reviewer. Independent investigations may discover additional relationships in the same revision.

`graph.sqlite` holds the plan, decisions embodied in accepted shards, question outcomes, nodes, typed edges, evidence and gaps. Inspect `coverage`, `dimensions`, `node KEY` and `trace KEY`. Trace accepts repeated types, direction, depth and size bounds. Coverage reports cite eligible and uncited file counts separately. **Complete** describes the questions in that plan. Record material boundaries omitted from an investigation as open questions.

## Optional Python baseline

Existing `build --commit REV`, `build --worktree` and `prepare [--agent-review]` commands run a separate static Python profile. It handles regular packages, imports, supported direct calls inside module-level functions, and selected root pyproject declarations. The optional legacy review marks signals for follow-up. Use `investigate` for supervisor-authored plans and relationships that cross technologies. Use `hints` inside an investigation to consult an extractor without replacing the active graph.

Old schema-compatible SQLite files remain inspectable. Static replay requires the recorded profile version, built-in module set and compatible Python parser. Rebuild with the current version to apply changes in binding or coverage.
