# Project Mapper acceptance

Historical static-profile v1 run. Validated with Python 3.12.10 and Git 2.55.0.windows.3. The five acceptance tests passed with the public checkout enabled. Each mapper invocation opens a new process. The test oracles come from fixture source and Git tree enumeration independently of mapper output.

## Run the complete suite

From the Agentic Workbench repository root, prepare an isolated checkout of [Click 8.1.8](https://github.com/pallets/click/tree/934813e4d421071a1b3db3973c02fe2721359a6e). The fetch is a test prerequisite. The mapper itself uses local Git objects.

```powershell
$checkout = '<absolute path to a new isolated Click checkout>'
git -c core.hooksPath=NUL clone --depth 1 --branch 8.1.8 https://github.com/pallets/click.git $checkout
git -C $checkout rev-parse HEAD
$env:PROJECT_MAPPER_CLICK = $checkout
python -B -m unittest discover -s skills/project-mapper/tests -v
```

Use `PROJECT_MAPPER_TEST_TEMP` to select an existing writable scratch directory for the controlled repositories. Omit `PROJECT_MAPPER_CLICK` to run the controlled checks with the public test reported as blocked. The public test asserts the exact 40-character commit.

## Supervisor-led investigation checks

The investigation tests drive the public CLI using temporary Git repositories and independently specified expected edges. They exercise source reads across directories, editable questions, verified decisions, conditions, open questions and stale evidence. A polyglot fixture traces an npm command through PowerShell to the test runner and the conditional report path. Its separate report alias is a forbidden edge. A successful check establishes the mapped static flow; generating a report requires a separate execution.

The baseline regressions cover lexical scope, built-in module precedence, delegated dependencies, unexamined inputs and scoped traces. Click is an optional pinned checkout for the static profile. Controlled tests do not need network access.

## Evaluate the prompts

The CLI suite checks the dispatch contract byte-for-byte. It compares two questions, a repair suffix, a path with spaces and an unknown question. The semantic checks below need independent workers. Freeze the expected outcome before dispatch; give each worker only its rendered prompt. Judge the accepted claims, directions, conditions, cited ranges and open questions. Record first-pass mistakes separately from successful repairs.

| Probe | Required observation |
| --- | --- |
| An empty default registry includes a plugin that subscribes to an event on the partner bus. Another plugin handles the same event name on an internal bus. | Follow the include to the configured handler. Keep the buses distinct in entity identities. Reject a claim of absence based on the empty inline list. |
| A diagnostic profile selects a registry using an environment variable whose value is unavailable. | Preserve the configuration dependency and the missing value as a gap. No resolved diagnostic-to-handler edge, including one conditional on a hypothetical registration. |
| Batch configuration has an empty observer list; the loader returns that list directly. Another mode has an observer. | Publish an evidenced absence for batch. Verify the empty graph and inspect question coverage and discrepancies. |

In the first blind trial, one worker omitted the bus namespace and another proposed a handler conditional on an unseen registry. After the prompt revision, fresh workers found `event:partner:receipt.created` and traced the diagnostic profile only as far as `env:SETTLEMENT_PLUGIN_REGISTRY`. The verified graph had five nodes and three edges, with one of two questions answered. In the separate batch trial, the worker established absence from configuration and loader evidence. The verified graph had one answered question and zero edges.

## Blind evaluation of open discoveries

Calibrate the reading budget on one repository. Reserve a different domain for the decision. Freeze source revisions, questions, required assertions and locators, forbidden associations and one unknowable answer before mapping. Give investigators only their assigned questions about the domain. A fresh reader receives only the held-out user question, without IDs or author vocabulary.

| Probe | Observation to record |
| --- | --- |
| In a content-addressed archive, two names refer to the same bytes. One expires while another reference may protect the content. | Starting from an operation, recover the exact local conditions for visibility and physical removal, then trace back to affected callers. Include same-name rules in unrelated subsystems as distractors. |
| Change one local convention in a second revision. Keep an unrelated rule unchanged. | Ground the changed answer in the correct revision, preserve the other answer and acknowledge questions beyond the evidence, such as when a rule was first introduced. |
| Two investigators describe overlapping behavior with different terms. A third finding shares a title only. | Retrieve the correct finding without a known ID. Accept alternate JSON structures and partitions supported by evidence. Count false joins and wrong-revision citations. |

Compare the open map and the previous graph under the same reader settings and returned-content budget. For decisive questions, include direct source search. Score the map-only answer before allowing source access, then record what that access rescued. Include search results in bytes/tokens, count distractors and opens, and separate build cost from query latency. A pilot can start with 12 distractors, three opened discoveries and 4,000 returned tokens per question. Freeze limits after calibration.

For a pilot pass, require correct, grounded answers to all critical held-out questions, the expected abstention, zero forbidden associations and a predefined gain over the previous graph. Regression controls include exact key versus a matching alias and a fixed one-edge trace with 1k, 10k and 100k unrelated edges. Compare fresh-process p50/p95 by direction and bytes read internally versus bytes returned. Report actual results separately from these procedures.

## Historical static-profile v1 oracles and results

| Test | Expected | Observed |
| --- | --- | --- |
| Flat regular package, `dedd72d151e80921d7d4d751c1c3593c331d932e` | Git tree accounts for every entry. Three static calls bind to `flat.worker:run` including a caller in another shard. The shadowed alias stays unresolved, and the identical symbol name in `flat.other` is forbidden. Dirty checkout bytes cannot alter pinned results. Nested re-inclusion, Git's extra ignore sources, tracked files matching ignore, and staged and unstaged deletions follow Git semantics. | Pass. Both directions returned the committed edge and evidence. Worktree rebuild removed the old targets. Ignored files contributed no facts. Repointing a stored edge to a valid same-named function failed verification. The source sentinel, Git index and Git revision checks passed. |
| Declared source root, `20dba2df3f504f7bdb0759dafb0c3b36f98e1d77` | Two static calls bind to `wheelhouse.impl:work`. `wheelhouse.cli:main` has source-package and declared-entry-point memberships. Identical `impl.py` and `twin.py` keep separate occurrences. Unsupported events, invalid syntax and examined absence remain distinct. | Pass. Removing one call invalidated its assertion while both endpoints survived. Restoring the call restored the edge. Changing only the configured source root removed the obsolete bindings. A bounded trace left coverage unchanged and an upward containment hop skipped siblings. An unpublished prepare and a rejected stale run preserved the previous graph. |
| Output safety, flat fixture | Reject an output directory symlink or Windows junction. | Pass. The redirected directory stayed empty. |
| Supplemental validation and replay, declared-root fixture | Equivalent baseline runs reproduce logical rows. Reject an unowned output and a review outside its task. Preserve the previous graph on rejection. Record a verified supplemental signal, blocked review and unexamined review without adding unsupported edges. | Pass. The accepted observation has a supplemental fingerprint and replays from its assigned source. The resulting typed edge set matches the baseline. |
| Click, `934813e4d421071a1b3db3973c02fe2721359a6e` | `click.termui` imports `click.utils`. `click.termui:secho` calls `click.utils:echo`. `click.termui` belongs to the `click` source package. A same-module target is forbidden and incomplete analysis remains visible. | Pass. The committed inventory matched the independent tree. The import, directed call and membership exist. The forbidden target is absent. The incoming call trace and source replay passed. |

Unsupported deployment, contracts and dynamic dispatch remain coverage outcomes.

## Historical Click demonstration

The published graph for the pinned checkout had 147 inventory entries, 226 nodes and 2,145 relationships, including unresolved candidates. Fresh-process verification returned `integrity=ok`. Tracing `function:click.termui:secho` outgoing and `function:click.utils:echo` incoming retained the call at `src/click/termui.py:634` and the definition at `src/click/utils.py:219`. The incoming trace correctly reported incomplete analysis. The `.github` deployment area remained unsupported. Four supplemental tasks completed their assigned scope, three reported partial coverage and nine source signals passed the gate. Git index bytes and HEAD matched before and after publication. [Call site](https://github.com/pallets/click/blob/934813e4d421071a1b3db3973c02fe2721359a6e/src/click/termui.py#L634), [definition](https://github.com/pallets/click/blob/934813e4d421071a1b3db3973c02fe2721359a6e/src/click/utils.py#L219).
