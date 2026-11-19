---
doc_type: adr
domain: testing
stack: [markdown, sqlite]
node_id: "adr:project-mapper-validation"
tags: [project-mapper, validation, incrementality, graph]
edges:
  - relation: references
    target: "adr:project-mapper-research"
  - relation: references
    target: "adr:project-mapper-method"
updated: 2026-11-19
---
# Local Contract and Falsification

## MINIMUM LOCAL GRAPH

Proposed contract, not an implemented CLI. Use an explicit immutable commit input for the first prototype. Build and refresh locally with no application execution or network dependency. The skill can use its own extraction helpers and native agent reasoning where evidence needs interpretation. It must still run without another skill, MCP, REA, CBM or Jev.

| Record | Minimum information and invariant |
|---|---|
| Snapshot | Identity binds repository, commit, scope, inventory, applicable configuration/profile and extraction/schema versions. Reserve a distinct publication generation when rerunning an analysis. Never substitute an older graph under a requested identity. |
| Artifact occurrence | Snapshot, repo-relative path, content fingerprint, applicability and examination outcome. Equal bytes at distinct paths remain distinct occurrences. |
| Node | Logical ID deterministically derived from the supported key in its namespace at this snapshot. A path-derived key may change on rename. Store unique cross-snapshot matches separately; keep ambiguous pairings unresolved. A clean rebuild never depends on history to reproduce snapshot IDs. |
| Relationship | Source/destination or candidate target, typed direction, authority, resolution state and supporting evidence. Evidence may establish a declared or static relation without establishing runtime occurrence. |
| Evidence | Snapshot and occurrence, symbol or location, source kind, relevant extractor/rule version, and optional dependencies. Keep uncertainty and contrary evidence. Do not export credentials or raw repository dumps. |
| View membership | View/group ID and node ID with the evidence or rule of membership; one node may participate more than once. Group names and membership are project-specific. |

Maintain outgoing and incoming relationship indexes, source-to-fact lookup and view membership. Separate reusable analysis values from revision-specific evidence pointers. Stage and validate a new generation before publishing it transactionally. Keep the last successful generation explicit on failure. A partial generation must never appear as complete or silently replace a complete result for the same requested identity.

## REFRESH MODEL

1. Reconcile inventory against the selected revision, including new, moved and removed files, under the same scope. Directory membership and resolver inputs participate even when no previous source file changed.
2. Re-extract only when bytes or the applicable parsing profile changed. If an extraction result depends on location, manifests or language settings, include that context in its key. Bytes alone may be sufficient for a genuinely context-free parse, not for binding dependencies.
3. Re-resolve typed relationships against the current inventory and configuration. For the prototype, recompute these joins rather than trying to predict all invalidation edges. Drop links with no remaining support; retain unresolved candidates and their cause when evidence is incomplete.
4. Refresh locations for every changed occurrence. Reuse a semantic card only if its normalized statements, relevant edges and uncertainty did not change. Attach current pointers during export; a warm cache must not ship yesterday's line number.
5. Compare normalized output at the same revision with a clean rebuild. Normalize ordering and run timestamps, not source locators, evidence scope or unknowns. A human-checked oracle is still necessary because both code paths can share an extraction bug.

## EXPORT AND TRACE

An export binds a revision, query type, examined scope and visited frontier. Each card contains its logical ID, concise claim, source pointer(s), authority, and references to typed neighbors. Include relevant unknowns and omitted counts when known. Bind the continuation to the immutable publication generation, query/filter and export profile. Resume that exact view or return an explicit expired-continuation error; never silently continue on a newer graph. Distinguish `none_in_examined_scope`, `partial` and `not_examined`; no empty result may imply all three.

Send all discovered architectural groups in the initial view, paginated without a semantic prefilter. Expand requested IDs and typed links in later views. Contract-level queries can follow inverse subscriptions outside a visible group. A budget limits the export, never storage. A downstream consumer may filter or score cards; it cannot delete evidence or certify completeness.

## PROTOTYPE TEST MATRIX

Freeze test observations by reviewing the source independently before evaluating the mapper. Use two bounded slices with different architectures and an isolated mutation fixture. For each expected relationship record typed origin/target, scope, authority and a source locator. Freeze required links, forbidden links and expected unknowns. Do not score exact generated group labels.

| Control | Required observation |
|---|---|
| Discovery vs directory labels | A move or folder rename does not alter unchanged logical group relationships; the new path and range are current. Keep unrelated groups unaffected. |
| Cross-boundary consumer and same-name decoy | Retrieve the real consumer through the typed channel/message/registration chain; omit homonyms on another channel or transport namespace (for example a different broker/vhost). Do not flood neighboring containers. |
| Unknown resolution vs actual absence | Remove the supporting config for a dynamic registration. Return partial with the missing input. A separate, supported and fully examined channel with no subscriber can return scoped absence. |
| Presentation budget | Paginate a known set of retained subscriptions. Joined pages equal the unpaginated export for one snapshot; an empty filtered page does not close an unresolved frontier. |
| Concurrent refresh | Start paging snapshot A, then build B or fail during B. Resume pinned A or report an expired continuation; never mix generations or label A as B. |
| Duplicate source bytes | Two packages have identical bytes/symbol names but different resolver context; a third file fails to parse. Preserve separate identities and supported targets, and never resolve the unexamined case by symmetry. |
| New or removed subscriber | Change only a subscriber file (or add one under an unchanged discovery rule). Incremental output contains the new relationship or removes the old one; the producer's unchanged bytes do not prevent it. |
| Alias or manifest retarget | Change configuration, not the caller. The relationship points to the new target, never both old and new as resolved. |
| Locator-only edit | Add a comment above the handler. The current source locator moves; normalized meaning is unchanged; dependent cards need not be regenerated. |
| Source/runtime distinction | Supply a static link and a test definition but no run. Export the static link and intended check; never claim observed execution or a passed test. |

## ACCEPTANCE AND MEASUREMENT

Require standalone operation on the documented supported slices, with all independently verified critical relationships recovered in the supported expansion. Require zero forbidden edges or falsely complete answers in the negative controls, and equal canonical facts, IDs, edges, coverage and evidence locators for incremental vs clean runs. Evaluate cross-snapshot matches separately. Record unsupported constructs instead of narrowing the oracle after the run.

Only after correctness, record cold/warm files inspected and parsed, reused and regenerated semantic cards, queries and tokens per view, and elapsed time. Compare the same task and scope against a plain read/search baseline; report omissions separately from speed or cost. Prior synthetic Jev trials explain why contract neighbors matter; they do not establish a performance or accuracy improvement for Project Mapper.

## REFERENCES

- [Project Mapper Research](PROJECT-MAPPER-RESEARCH.md): recommendation and out-of-scope components.
- [Architecture Recovery Method](PROJECT-MAPPER-METHOD.md): evidence gathering and grouping.
