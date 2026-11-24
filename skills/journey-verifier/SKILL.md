---
name: journey-verifier
description: Plan, generate and verify a versioned end-to-end suite from a target checkout or an evidence handoff such as a REA bundle. Use for behavior verification, suite reconstruction, isolated environment setup and independent proof of side effects.
---

# Journey Verifier

Take a requested scope, evidence and a separate suite directory. Initialize or
resume it from this skill directory.

- Checkout — `python scripts/init_suite.py TARGET SUITE`
- Evidence handoff — `python scripts/init_suite.py --bundle BUNDLE SUITE`

The bundle initializer fingerprints the file. Verify its records through the evidence tool.

1. **Choose the task.** Derive tests for mapped behavior, or reconstruct an existing suite from evidence of its discovery, assertions, fixtures and reporting. Use the [planning contract](references/plan.md) to bind scenarios, revisions, governance and gaps. Keep runnable build identity separate from source revision.
2. **Qualify the environment.** Map runtime, configuration, dependencies, owned state, observers and teardown. Prove the smallest real path from readiness through independent observation and cleanup before broad execution. Continue with cases whose prerequisites hold.
3. **Build and challenge the suite.** Reuse pinned launchers, fixtures and tools. Put each assertion at the cheapest layer retaining its signal. Freeze acceptance before candidate feedback. Prove material assertions detect a controlled defect at the intended boundary. For blind work, keep reference inputs and verification cases with the verifier.
4. **Run and report.** Follow the [run contract](references/run.md). Deliver one documented noninteractive command, scenario and gap records, retained observations and a verdict matrix using the [report contract](references/report.md). Preserve the first candidate and run before enriching its handoff.
