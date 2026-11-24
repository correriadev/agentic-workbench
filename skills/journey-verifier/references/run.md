# Run contract

## Admit and qualify the run

- Use the smallest authorized isolated environment exercising the required mechanisms. Separate an attached environment, an environment provisioned on the same host, a fresh process and a separately provisioned worker in the receipt. Reuse a stack only after verifying its effective configuration, ports, state, observer reachability and cleanup authority.
- Pin result-affecting inputs before execution. Include the artifact bytes, effective runtime and shell, dependency builds, settings and schema, fixture and check revisions, and real/simulated modes. Check them from the process that will use them. Record incomplete preparation as a gap. A new digest or changed condition invalidates the affected proof. Reuse a verified setup only while those inputs and ownership match and reset is observed.
- Run a bounded smoke test before the broad suite. Verify each material dependency's readiness through its consumer, the target's public entry, and the observer's connection to the expected store or equivalent authority. Validate required schema/fixture facts there. Observe an expected initial state and one correlated effect or controlled absence, then verify cleanup. A healthy port or successful response alone cannot qualify the run.

## Observe and challenge

- Give each attempt its own identity and evidence location. Use distinct business and observation IDs where conflation could hide a defect. Invoke the actual entry and observe dependency inputs and effects independently of the response. Check observer availability and initial state before interpreting missing data. Wait for an explicit completion predicate within a deadline.
- In a disposable environment, inject the scoped defect without changing unrelated inputs. Prove the defect actually occurred and check an unaffected control. Require the intended assertion to fail, preserve its raw exit and evidence, and rerun on restored state. Compare baseline and candidate with equivalent inputs, resets, fault activation and observers. Treat runner, environment or observer failures as incomplete proof of behavioral detection.
- Diagnose the earliest failing stage. Distinguish input/discovery, provisioning/readiness, fixture/observer, behavior/assertion, cleanup, and report/publication. Preserve partial evidence and record actual stages separately when multiple fail. Before retrying an uncertain side effect, reconcile it through its correlation key and owning observer. Retain attempts when a retry or repair changes the result.

## Clean up and retain

- Record ownership before acquisition. Use finally-style cleanup on success, failure and cancellation, and attempt all independently owned resources. Touch only run-owned effects. Retain the primary failure and record cleanup failures and remaining resources separately. Exercise partial startup and cleanup failure or retry when material to the lifecycle.
- Write artifacts under the current attempt and preserve the smallest complete proof. Redact secrets, personal data and live endpoints at capture. Verify report links and generated output when required by the [report contract](report.md).
