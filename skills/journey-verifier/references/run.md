# Run contract

Choose the smallest environment that exercises the real public entry and the mechanisms under test. A process and temporary directory may suffice. Reuse an existing stack only after checking its resource names, published ports, readiness contract and destructive cleanup scope.

- Assign each run its own identity, disposable resources and evidence directory. Record ownership before starting resources that can partially initialize. Use unique business and observation identifiers when conflating their roles could hide a defect.
- Check readiness through the caller's path, including consequential configuration or provider behavior. Verify initial state through the authority that owns it. Scope fault controls to the test request and retain a control observation for unaffected traffic.
- Invoke the real executable through the public interface. Wait against an explicit completion predicate with a deadline. Assert independent state or external effects using a channel separate from the response being verified. Establish what an empty observation means and whether the observer itself was available.
- Save sanitized, per-assertion expected/actual values, relevant before/after state, build identity and failure stage. Missing required evidence is inconclusive and gives CI a nonzero exit. An observed contradiction fails. Preserve partial evidence on exceptions.
- In a finally block or equivalent teardown, revert only run-owned resources. Record cleanup errors separately and retain the first behavioral failure. A cleanup failure also prevents a successful exit. Exercise a failed run and a fresh retry.
- Document prerequisites, fixture provenance, simulator assumptions, pending decisions and how to inspect the artifacts. Keep credentials, personal data and live destinations out of fixtures and evidence.
