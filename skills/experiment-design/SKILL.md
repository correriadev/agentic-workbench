---
name: experiment-design
description: Design the smallest useful comparison when a decision depends on a measurable claim about quality, time, cost, or behavior. Use to define a falsifiable experiment or interpret its evidence; skip low-stakes, reversible decisions that need no new evidence.
---

# Experiment Design

## Project context

When this skill needs context for an existing project, first check for its
`.project-mapper/graph.sqlite`. With a compatible installed
`project_mapper.py`, query from the project root using
`python "<mapper>" . --offline` followed by `coverage --summary`,
`search "<term>"`, `node <key>`, `open <id>`, or
`trace <key> --direction both --depth 2` as needed. Check graph identity,
snapshot, coverage and gaps; reopen decisive current sources. A map is a lead,
not proof of runtime behavior or permission to write. If the map or compatible
CLI is absent, unreadable or incomplete, consult `docs/README.md` and its
index, then relevant source and tests; if unavailable, use the root README,
manifests and source. Report material gaps. Do not create or update the map
unless requested; preserve this skill's scope and any supplied exact paths.

Begin with the decision the result could change and the options available. Design the smallest experiment capable of distinguishing them in conditions relevant to that decision. Designing a test does not authorize executing it or spending resources. Use the available context; identify material assumptions and ask only for missing information that changes the decision, validity, risk, or authorization.

## Protocol before execution

1. **Hypothesis and comparison:** State a falsifiable, directional claim and what observation would contradict it. Identify a credible baseline representing the current or realistic alternative and a candidate intervention. Select cases representative of the decision where the intervention has a real opportunity to affect the outcome; explain why they discriminate. A case that cannot expose the proposed effect cannot establish equivalence.
2. **Controls and attribution:** Specify the unit of observation, procedure, measurement method, and what stays constant across arms, including relevant inputs and environment. Identify factors that differ. Isolate factors when their individual effects matter to the decision; otherwise compare and report the combined intervention without attributing its effect to a single change. Account for known confounders.
3. **Evidence and uncertainty:** Define how observations and raw evidence will be captured for each arm, including failures and exclusions, and how much evidence is needed to distinguish the decision-relevant effect from uncertainty. Justify repetitions, balanced ordering, or blinded scoring only when they address a concrete source of variability, order effect, or scoring bias; otherwise omit them. Identify the uncertainty the design cannot resolve within its budget.
4. **Precommit criteria:** Before observing results, record the primary metric, direction, units and aggregation; a minimum acceptable quality floor and how it is measured; the smallest decision-relevant difference and equivalence tolerance; sample or evidence sufficiency; and a stop rule. Record the authorized time, cost, and other resource limits, or label a proposed budget as unapproved. Define non-overlapping criteria and the resulting action for **better**, **worse**, **equivalent within tolerance**, and **inconclusive**. A quality-floor violation makes the candidate unacceptable even if its primary metric improves. Equivalence requires evidence sufficiently precise to support the tolerance, not merely a failure to find a difference. Insufficient evidence, a nondiscriminating case, or an invalid comparison is inconclusive.
5. **Calibrate when needed:** If the available baseline does not justify a floor, tolerance, threshold, or evidence requirement, define a separate, bounded calibration round to estimate what is needed. Do not claim a comparative verdict from calibration. Set and record the comparison criteria after calibration and before its results are observed.

Return a short protocol containing the decision, hypothesis, comparison and discriminating cases, controls, evidence to capture, budget, stop rule, and all decision criteria. Identify any proposed choices needing user authorization; do not run the experiment unless execution is independently authorized.

## Results after execution

Report the observations by arm against the precommitted metric and quality floor, the evidence and exclusions, deviations from the protocol, the verdict and decision it supports, and limitations on generalizing the result. If evidence is insufficient or the comparison cannot discriminate, report **inconclusive** and state what additional evidence or revised design could resolve it; do not call it equivalent.

If the scenario, hypothesis, or scoring changes after results are known, preserve the original protocol and results, label the change, and treat the revised test as a new round with criteria recorded before observing its results. Do not present post hoc findings as confirmation of the original hypothesis.
