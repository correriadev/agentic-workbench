---
doc_type: adr
domain: architecture
stack: [markdown, typescript]
node_id: "adr:project-mapper-rea"
tags: [project-mapper, reverse-engineering, evidence, graph]
edges:
  - relation: references
    target: "adr:project-mapper-research"
updated: 2026-11-19
---
# REA Evidence, Traversal and Versioning

## SCOPE AND EVIDENCE

Reviewed [morluto/rea at d865c776](https://github.com/morluto/rea/commit/d865c776463d3095b623b15a9cf6bb20793de228). The evidence envelope below was inspected in source; application tracing and comparison behavior are described by the maintained contracts. The Notes data is a published maintainer fixture, not our execution or an accuracy benchmark. Map ordinary source checkouts without inheriting REA's providers, MCP, capture, decompilation, or reconstruction.

## 1. EVIDENCE IDENTITY

The [Evidence implementation](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/src/domain/evidence.ts#L393-L421) commits canonical content: subject identity, provider/profile, operation, parameters, raw and normalized result, authority, environment, limits, coverage, locations and evidence links. Its ID excludes local request/display metadata, not all logical source locations. Parsing checks the commitment. This is content integrity, not a guarantee that the analysis is true.

**Transfer:** use three identities, with a distinct revision binding. A logical entity addresses a concept such as a registered handler within a particular namespace. An occurrence places that entity in a path and symbol range at a snapshot. An observation records the asserted fact and the evidence/extractor that produced it. A source edit can produce a new occurrence and observation without a new entity. Cross-snapshot matching is separate from computing IDs an independent rebuild can reproduce. Identical bytes at two paths are not a license to merge entities. Normalize observations for comparison without discarding provenance.

The [historical source CLI](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/getting-started/cli.md#import-historical-source) treats the filesystem inventory as the observed source; a discovered Git HEAD does not assert equality with the working tree. For the mapper, start with explicit commit-snapshot mode; if worktree support is added, give it its own inventory identity and never publish it under HEAD alone.

## 2. EXAMINATION, RETENTION AND PROJECTION

[Application workflows](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L1-L47) keep structural and semantic graphs separate and bound to the same analyzed artifact. Shared evidence context is stored once; each fact retains its exact locator. A missing semantic graph is unavailable, not an empty graph. A summary can point to the full parent analysis rather than repeating extraction. [Paging](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L126-L155) preserves both page position and source coverage.

Keep three limits separate in Project Mapper:

| Limit | Meaning | Example |
|---|---|---|
| Inventory | Which files were included or could not be examined? | A referenced deployment manifest lies outside the checkout. |
| Extraction/resolution | Which relevant facts were understood inside that inventory? | The registration exists, but the channel is chosen dynamically. |
| Projection | Which already retained facts were omitted from this answer? | Ten consumers are indexed; the current page shows five. |

The [partial-analysis guide](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-artifact-reconstruction.md#recover-partial-analysis) distinguishes interruption after a phase began from a phase that never started. Adopt enough state to avoid silently discarding recovered facts or claiming completeness after a failed parse. Do not import REA's phase engine. Smaller summaries save reader context; that alone does not reduce the initial extraction work.

## 3. TYPED TRAVERSAL

[Feature tracing](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L145-L175) starts from a typed seed. In bidirectional tracing, arriving at a container through a child's containment edge does not expand all siblings. Candidate starting points discovered heuristically are not confirmed trace matches. A relevant unknown can make a trace partial despite a successful seed match. [Semantic tracing](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#semantic-relation-tracing)

In the [published Notes Electron example](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/website/evidence/guide-examples.md#L9-L28), four JS files parsed; one exposed API, one literal IPC channel, one invocation and one main-process handler were linked. The demonstrated relationship crosses files/process boundaries via the channel. The project describes the edges as static inferences and does not claim the complete click-to-file path ran. This is an example of attribution, not a measured recall rate.

For a source checkout, walk `publishes` then inverse `consumes` using normalized contract identity. Traversing to the consumer's service gives ownership, not permission to pull every sibling. Never turn “unique static target under these resolver rules” into “executed.” A model-generated summary is not independent evidence.

The Notes project also [published a later run](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/website/evidence/guide-examples.md#L85-L100) after an HTML-only update: different artifact and Evidence IDs, unchanged JS/data digests and the same reported IPC counts. That shows why a graph should distinguish artifact revision and a resolved relation. It does not prove that all behavioral facts were unchanged or that the re-analysis was incremental.

## 4. COMPARISON IS NOT INCREMENTAL INDEXING

[Version comparison](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#L385-L429) attempts unique matches in tiers, from exact digest and identities to structural fingerprints and semantic keys. Duplicate matches remain ambiguous; a weaker guess cannot override a stronger unique match. A relocation alone counts as unchanged only under the contract's coverage and resolved-neighbor conditions; it still retains previous and current coordinates. A one-sided result denotes removal or addition only if the corresponding search coverage is complete.

**Transfer:** separate path relocation, changed facts and changed edge targets in the mapper's diff; record unknown when scope is missing. Cache extraction by bytes plus the applicable parsing profile. Resolve references separately using the current inventory and config, since byte identity cannot prove graph identity. REA's comparison proves neither that its analyses were produced incrementally nor that our refresh will match a clean rebuild.

## REFERENCES

- [Project Mapper Research](PROJECT-MAPPER-RESEARCH.md): conclusions and guide index.
