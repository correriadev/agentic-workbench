# Planning contract

## Bind the scope to evidence

- For a checkout, inspect local changes and pin the revision. Check for `.project-mapper/graph.sqlite`. With a compatible installed `project_mapper.py`, use `python "<mapper>" . --offline` from the project root with `coverage --summary`, `search "<term>"`, `node <key>`, `open <id>` or `trace <key> --direction both --depth 2` as needed. Check graph identity, snapshot and coverage, then reopen decisive current sources. Update the map only when requested.
- If the map or CLI is absent, unreadable or incomplete, follow `docs/README.md` and its index. Fall back to the root README, manifests and source. Respect supplied paths and access boundaries, and record material gaps. Read applicable requirements, tests, fixtures, effective configuration and past runs. Establish runtime behavior from execution evidence.
- For a REA handoff, pin the bundle digest, graph revision, case and claim IDs, and decisive Evidence IDs or locators. Reopen the selected records with the supported query in a fresh process. If only a retained export is available, continue with its supported facts and record that independent reopening is unverified. Keep references to artifacts and narrow views instead of duplicating entire graphs, sources or logs.
  For the supported investigation-graph CLI, run `rea inspect-analysis-view REQUEST.json --evidence-bundle BUNDLE --json` with the retained scenario request.
- Bind each expectation to its authority and applicability. Keep observed behavior, static derivation, hypothesis and human decision distinguishable. Treat legacy facts as characterizations until an applicable decision or requirement establishes what to preserve. Use source-system governance when available. Apply migration governance only to the cases it governs. Carry existing obligation and decision IDs forward. A divergence remains observable even when an owner accepts it.
- To reconstruct a suite, inventory actual and configured discovery modes, cases and skips, setup/teardown, assertions, evidence links, runner exits and in-scope CI stages. Require evidence from the suite and its artifacts for those claims. Application evidence alone supports behavior tests where sufficient.

## Record the case and the gap

Keep one concise row per materially distinct scenario or variant. Reuse the project's existing plan and result formats if they carry these fields.

| Record | Minimum facts |
|---|---|
| Case | Stable ID, source and obligation refs, preconditions and build applicability, fixture identity, trigger/input, expected response and side effects, independent observer and correlation, assertion and cleanup boundary. |
| Dependency | Consumer and effective destination, role and mode (real, simulated, recorded or absent), versions and result-affecting configuration or schema, caller reachability, readiness and reset, observation and owner. Cite the evidence behind simulated behavior and name assumptions. |
| Gap | Affected cases and exact missing, stale or contradictory fact, evidence and why it is insufficient, impact on execution or verdict, smallest resolving probe, responsible role and current status. |

Route missing behavioral, schema or configuration facts back to their evidence owner. Resolve host/toolchain, isolation and dependency setup in the harness. Route policy choices to the human owner. A gap blocks the claims and cases that depend on it, including an owned-setup claim when an attached run succeeds. Keep untested, skipped, excluded and blocked cases visible with different reasons.

## Design the smallest discriminating checks

- For each material risk, name a plausible incorrect implementation, the assertion it should trip and the independent observation that would expose it. Use nominal, negative and boundary cases where they distinguish outcomes. Select dependency, data, timing, cleanup and retry cases from observed behavior and material risks. Avoid a cross-product of equivalent variants.
- Verify pure fixture, parser and report-selection logic locally. Use contract or integration checks for provider semantics. Keep E2E for obligations that require the real journey or an effect across components. An equivalent cheaper assertion can replace a redundant check after its consumers and coverage are confirmed. Preserve meaningful original cases in a reconstruction comparison.
- Freeze case IDs, expectations, fault controls and proof boundaries before giving feedback on a candidate. Use review independent of implementation for material obligations. The reviewer checks a plausible false pass, the assertion reached, and the observations supporting the verdict. For example, a `201` with a missing row should fail the persistence assertion while the HTTP assertion passes.
- Keep stable regression cases. Add focused probes when build changes, escaped defects or recurring gaps reveal missing discrimination. Fix shared causes in the owning fixture or adapter. Record any deferred workaround with its impact, owner and revisit trigger.
- In a blind reconstruction, hand over only the scoped Evidence, toolchain and authorized test endpoints. Keep reference source, builds outside the allowed input, hidden cases and the verifier private. Use enforceable access boundaries when available and record the actual isolation. Version any enrichment. Preserve the first candidate, results and gap before sending a revised handoff.
