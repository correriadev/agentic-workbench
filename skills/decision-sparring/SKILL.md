---
name: decision-sparring
description: Pressure-test a preferred option or a consequential, costly-to-reverse choice. Use when the user wants a concrete decision challenged; skip routine reviews, trivial choices, and open-ended pros and cons.
---

# Decision Sparring

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

Challenge the choice, not the person. Work with the evidence available; a single agent and one pass can be sufficient. This is decision support, not an approval gate.

## Method

1. State the decision, objective, relevant constraints, preferred option and viable alternatives, including the status quo when viable. If no preference is stated for a consequential choice, evaluate the leading option apparent from context and label that interpretation. Ask only for a missing detail that prevents a meaningful challenge.
2. Give the strongest case for the preferred option, including the evidence that supports it. Separate observations and user-provided claims from inferences and unknowns; do not present an unverified claim as observed fact.
3. Identify the assumption whose failure is most likely to change the choice. Construct the strongest plausible counterexample: explain the conditions, resulting consequence and which alternative would become preferable. Mark hypothetical conditions as such. Discard objections that would not materially affect the choice; do not invent a material objection if none remains.
4. Identify discriminating evidence and what would support keeping, changing or deferring the choice. If a decisive fact is missing, specify the smallest check capable of resolving it and the possible implications. Do not perform the check or make the final decision unless the user asks.

## Optional independent review

Use a reviewer only if an independent perspective could reveal a material blind spot and the host and user permit delegation. Follow the host's provider conventions and use an available configuration; no particular model is required. Place stable instructions before variable inputs. Give the reviewer the decision question, constraints and necessary evidence, without the expected verdict. Ask for a decision-changing counterexample and its evidence, or a reason none was found. Assess its response against the available evidence; disagreement alone does not warrant another round.

Stop when the evidence that would change the decision is clear or no material objection remains. Do not continue solely to seek consensus.

## Output

Return the decision and viable alternatives; strongest supporting argument; fragile assumption; strongest plausible counterexample or why none remains; and evidence that would justify keeping, changing or deferring the choice. Identify the smallest resolving check when needed. Distinguish a conditional recommendation from the user's final decision.

## Examples

- **Counterexample changes the recommendation:** A team prefers a managed database to reduce operations. The key assumption is that data may leave its region. If the signed contract requires local-only storage and the service cannot meet it, recommend the viable local option instead; verify the contract's data-location clause and service region before treating that condition as fact.
- **Immaterial objection:** For a one-year tool choice, a different logo is plausible but does not affect cost, capability or any stated constraint; discard it. If migration cost is decisive and unknown, identify the smallest estimate needed and defer the choice pending its result.
- **One pass is enough:** A team prefers a reversible internal configuration change. The only identified objection is a minor cosmetic difference with no effect on the objective or constraints. No material objection remains; report that and stop without another review round.
