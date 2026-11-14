# Software engineering

Load when the delegated prompt asks to design, implement, review, test, integrate, fix or migrate software.

## Context to include

Identify target repo, working directory, affected files, current behavior, desired behavior and scope. For each material component, identify its responsibility, state, runtime and startup conditions. For each integration specify caller, destination, protocol, endpoint or operation, input/output, authentication, source of secrets, timeout, failure behavior and observable evidence. Preserve exact paths, images, versions and configuration keys supplied by the user. Distinguish host, container and CI addresses. Specify configuration source, precedence and validation. Resolve unknowns with a concrete discovery location and verification.

## Adapt to the work

- Boilerplate: supply target tree, ownership of files, dependency versions or selection criteria, startup/readiness/teardown, a representative sample, and commands from a clean checkout.
- Fix: identify reproduction, expected behavior, affected callers, smallest compatible scope and regression proof.
- Migration: map old to new contracts, compatibility of existing state and callers, rollout and rollback, and parity checks.
- Review or tests: encode the chosen balance of execution, coverage and audit. State whether findings, patches or reruns are expected. Separate product failures, harness failures and unavailable dependencies.

## Example

For an E2E review targeting an external `503`, ask the executor to locate the relevant test and mock mapping, trace the API call and verify the public error contract. Check absence of SQL and Redis side effects where required by the contract. If execution was selected, specify the repository runner, fixture readiness and proof in the report. If only review was selected, request evidence-backed findings with file and section locations.
