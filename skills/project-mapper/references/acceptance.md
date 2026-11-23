# Project Mapper acceptance

## Run the complete suite

From the repository root, prepare the pinned [Click 8.1.8](https://github.com/pallets/click/tree/934813e4d421071a1b3db3973c02fe2721359a6e) checkout. Mapping uses local Git objects.

```powershell
$checkout = '<absolute path to a new isolated Click checkout>'
git -c core.hooksPath=NUL clone --depth 1 --branch 8.1.8 https://github.com/pallets/click.git $checkout
git -C $checkout rev-parse HEAD
$env:PROJECT_MAPPER_CLICK = $checkout
python -B -m unittest discover -s skills/project-mapper/tests -v
```

Optionally set `PROJECT_MAPPER_TEST_TEMP` to a writable scratch directory. Without `PROJECT_MAPPER_CLICK` the controlled checks still run. The public test requires the exact commit.

## Supervisor-led investigation checks

Blind trials use separate contexts.

- The evaluator receives the pinned target, historical records and scoring rubric. Freeze the source-based key and held-out questions before either publication.
- Each investigator receives the skill, pinned target, neutral request and identical reading budget. Keep evaluation files, expected paths, answer keys and prior outcomes out of its context. Dispatch workers with only their rendered assignments and target access.
- Each fresh reader receives one first publication, the held-out questions and the query interface. Score answers, decisive locators and unsupported claims before giving the reader source access or repairing any shard.

The credential regression checks that a searchable finding can retain the symbolic reference and consumer while omitting the synthetic value from query responses and generated artifacts. Source reads expose the original lines.

Baseline regressions cover lexical scope, built-in module precedence, delegated dependencies, unexamined inputs and scoped traces.

## Multidimensional profile

`test_multidimensional.py` covers lexical candidates, paths, configuration, coverage and bounded token scanning; `test_multidimensional_cli.py` covers publication, Python coexistence, semantic enrichment, preservation and replay; `test_multidimensional_credentials.py` checks representative secrets across generated artifacts. `test_node_context.py` checks linked discovery previews and context counts. Treat candidates as leads, not validated calls or runtime behavior. For a real-repository evaluation pin a snapshot, inspect representative cross-dimensional links and report unresolved or unsupported inputs. Report build, verification and query costs separately; a successful static map alone does not demonstrate semantic completeness.

`test_semantic_planner.py` covers graph-derived assignments, shared nodes, bounded units, source boundaries and snapshot checks. `test_graph_investigation_contract.py` exercises graph-pinned plans, batches, paginated inspection, tampering and progressive publication. The `test_semantic_node_*` suites check node-specific roles, shared flow context and bounded evidence projections. A count of assigned or linked nodes is not a semantic completeness metric; report unexamined units and missing node-specific roles separately.

## Evaluate the prompts

CLI tests compare dispatch prompts byte-for-byte across two questions, a repair suffix, paths with spaces and an unknown question. For semantic checks, freeze expectations before giving independent workers only their prompts. Judge claims, directions, conditions, locators and open questions. Record first-pass mistakes and repairs separately.

## Cross-language acceptance

Map a non-English request and repository with an isolated worker. Inspect English in the plan, shard, graph, export (including embedded records) and report. Check nested keys, terms, conditions and gaps. Resolve source identifiers and citations against the snapshot. Query by English paraphrase. Change an unexamined question after plan review. Publication must reject the stale fingerprint and accept the corrected, freshly reviewed partial plan. Re-review legacy findings before migration.

## Blind evaluation of open discoveries

Calibrate the reading budget on one repository and evaluate in another domain. Freeze revisions, questions, assertions, locators, forbidden associations and one unknowable answer. Investigators receive only their assignments. Give a fresh reader the held-out question without IDs or author vocabulary.

Compare the open map and the previous graph under the same reader settings and returned-content budget. For decisive questions, include direct source search. Score the map-only answer before allowing source access, then record what that access rescued. Include search results in bytes/tokens, count distractors and opens, and separate build cost from query latency. A pilot can start with 12 distractors, three opened discoveries and 4,000 returned tokens per question. Freeze limits after calibration.

For a pilot pass, require correct, grounded answers to all critical held-out questions, the expected abstention, zero forbidden associations and a predefined gain over the previous graph. Regression controls include exact key versus a matching alias and a fixed one-edge trace with 1k, 10k and 100k unrelated edges. Compare fresh-process p50/p95 by direction and bytes read internally versus bytes returned. Report actual results separately from these procedures.
