# New Scope graph CLI

Use Python 3.12+ and its standard-library SQLite. From the target project root,
run `python /path/to/new-scope/contract.py docs/specs/<change-id> <operation>`.

| Operation | Arguments and result |
|---|---|
| `init` | Create or reopen revision 0 or later |
| `inspect` | Identity, current revision and whether the summary matches |
| `apply` | `--expect N` and one JSON object on stdin, committed atomically |
| `get ID` | Full node, adjacent edges, provenance, operational mappings and observations |
| `source-ref ID` | Read current file evidence and print a row for `sources` |
| `trace ID` | Bounded traversal in both directions, using `--depth` and `--limit` |
| `impact ID` | Directed traversal of downstream planning dependencies |
| `coverage [ID]` | Planned assertions, observables and recorded execution references |
| `gaps` | Deterministic findings and task readiness |
| `validate` | Integrity and planning findings, with a nonzero exit on a blocked plan |
| `render-scope` | Atomically regenerate the human summary for the current revision |
| `export-execute-scope` | Print a version-bound Execute Scope task projection; writes nothing |

`export-forge` remains a compatibility alias with the same output. The
persisted `blueprint_source` field retains its existing name and meaning so
plans created before the skill rename remain readable.

## Apply format

Use `request_id` and a meaningful `reason`, followed by arrays named for the
tables being changed. Each record is a full row. Optional columns may be omitted.
See [schema.sql](../schema.sql) for field names. Use the same request ID and
payload for a retry. If the expected revision is stale, inspect and reconcile
before issuing a new request. Use `remove_edges` with `src`, `relation` and
`dst` to remove a relationship. Each accepted change records old and new rows.

```json
{
  "request_id": "capture-intent",
  "reason": "Capture the user's cancellation goal",
  "nodes": [
    {
      "id": "I1",
      "kind": "intent",
      "title": "Cancel a scheduled boleto",
      "content": "An authorized owner can request cancellation before execution.",
      "state": "confirmed",
      "origin": "human"
    }
  ]
}
```

## Current source references

`source-ref` reads a project-relative file and returns a `sources` row with its
raw SHA-256. It works before `init`. Paths default to the project containing the
specification. Use `--project-root` for evidence from another target root.

```text
python "<contract>" docs/specs/<change-id> source-ref SRC1 --path "<source path>" --symbol "<symbol>" --lines 20 34 --expect-content-id "<locator content_id>" --excerpt
```

Copy the inclusive line numbers from the locator and choose an exact symbol when
known. The optional content ID accepts Project Mapper's raw SHA-256 or Git blob
hash, computed locally from the same bytes as the raw SHA-256. Use `--excerpt`
with a focused range to see those verified bytes as text. Omit it when the
reference alone suffices. Submit the row through `apply` and add the corresponding
`node_sources` link. `apply` checks the raw hash again before storing a new source.
For a changed file or a documentation lead without a map, inspect the current
file and create its reference from the current lines.

## Relationship conventions

- `criterion requires behavior`, `task implements criterion or behavior`,
  `behavior requires method`, and `task implements planned method`. Link
  affected APIs and components with `requires` and `references`.
- `task depends_on prerequisite`. Map scope to the task with `implements`.
  Use `task mitigates risk` and `task requires obligation` to propagate blockers.
- `risk threatens behavior`, `risk requires obligation` and optionally
  `obligation covers behavior`. Link requirements, behavior, tasks and
  obligations to scenarios with `verified_by`.
- `api_contract has_request request_field`, `has_response response_field`,
  and `has_error error_contract`. When a facet is inapplicable, use
  `details.facet_exemptions.<facet>` with the reason. Use
  `details.method_required: true` on behavior requiring a method.
- `scenario has_assertion assertion`. Declare matching stable observable IDs
  in `details.observables` on obligations and assertions. Add
  `details.artifacts` to obligations. Describe the real observation point in
  the assertion and the setup, triggering action, and outcome in the case.
  By default one scenario must cover all required observables. Set
  `details.observation_mode: independent` only when separate runs provide valid coverage.
- For explicit blockers, link affected tasks to a blocked node through
  `requires`. Record non-applicability and technical justification in
  `details.rationale`. Record source provenance via `node_sources`.
- Use `new decision supersedes old decision` with rationale. Decisions,
  source snapshots and observations are append-only. Use new source IDs for
  changed content. The verification record references the exact planned
  command at the observed revision. Use `evidence supports test_scenario`
  for graph traversal in addition to the evidence record's scenario ID.

The implementation task's `task_files` entries are the file allowlist and
`role: unit` denotes its RED/GREEN files. Map the task to its unit scenario
directly, including the same focused command. Use `runner_source` for
configuration or an inspected example that grounds that command.

## Handoff to Execute Scope

After reviewing `gaps`, `coverage` and `validate`, run `render-scope`, then
`export-execute-scope`. This prints JSON for Execute Scope's existing `plan` operation; it does
not publish `tasks.json`. Give the JSON and the current Execute Scope `inspect` digest
to Execute Scope, which publishes it with its own contract script. The projection binds
the exact New Scope database revision and SHA-256, current scope and QA revision.
Reconcile any rejection; do not remove the binding. Existing execution evidence
is retained, while projected tasks return to pending when replanned.

The projection copies task `content` into `description` and `technical_steps`.
Include the rationale and priority the executor needs there, with decisions linked
for supporting context. Arbitrary `details` fields are not automatically exported.
Tasks are exported in ID order; priority text guides selection among ready tasks,
not an automatic scheduler. Keep `depends_on` reserved for real prerequisites.

For explicit formal QA mapping, put `qa_ids` and `evidence_checks` on the task
node's `details`. Each check needs an `id`, `command`, `qa_ids`, and `files`
as project-relative references; all QA IDs must identify ready obligations in the
current `qa.json.contract`. Evidence tasks require at least one mapped check.
Reading or running an existing check does not authorize editing its files.
The exporter leaves an unready task and its dependents in `blocked_tasks`,
including missing production paths, missing QA mappings or pending obligations;
it never invents a mapping. If recording these mappings changes the scope
revision, rerender and reconcile QA before exporting. Legacy plans remain
readable without this projection when no New Scope database exists.

Planning readiness is a structural result. The validator compares declared
observable IDs and checks task mappings, but cannot prove that a test body,
its assertions or the command actually implement those claims. Evidence rows
are attributed observations about a candidate and a prior plan revision.
Coverage lists their IDs without treating them as a delivery verdict.

## Read-only SQL

```sql
SELECT obligation.id, scenario.id, assertion.id, assertion.details
FROM nodes AS obligation
JOIN edges AS verification ON verification.src = obligation.id
     AND verification.relation = 'verified_by'
JOIN nodes AS scenario ON scenario.id = verification.dst
JOIN edges AS assertion_link ON assertion_link.src = scenario.id
     AND assertion_link.relation = 'has_assertion'
JOIN nodes AS assertion ON assertion.id = assertion_link.dst
WHERE obligation.id = 'O-NO-DISPATCH';
```
