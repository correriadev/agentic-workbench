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

Run the same unittest discovery command above from the repository root. The investigation tests drive the public CLI using temporary Git repositories and independently specified expected edges. They exercise source reads across directories, editable questions, verified decisions, conditions, open questions and stale evidence. A polyglot fixture traces an npm command through PowerShell to the test runner and the conditional report path. Its separate report alias is a forbidden edge. A successful check establishes the mapped static flow; generating a report requires a separate execution.

The baseline regressions cover lexical scope, built-in module precedence, delegated dependencies, unexamined inputs and scoped traces. Click is an optional pinned checkout for the static profile. Controlled tests do not need network access.

## Evaluate the prompts

The CLI suite checks the dispatch contract byte-for-byte. It compares two questions, a repair suffix, a path with spaces and an unknown question. The semantic checks below need independent workers. Freeze the expected outcome before dispatch; give each worker only its rendered prompt. Judge the accepted claims, directions, conditions, cited ranges and open questions. Record first-pass mistakes separately from successful repairs.

| Probe | Required observation |
| --- | --- |
| An empty default registry includes a plugin that subscribes to an event on the partner bus. Another plugin handles the same event name on an internal bus. | Follow the include to the configured handler. Keep the buses distinct in entity identities. Reject a claim of absence based on the empty inline list. |
| A diagnostic profile selects a registry using an environment variable whose value is unavailable. | Preserve the configuration dependency and the missing value as a gap. No resolved diagnostic-to-handler edge, including one conditional on a hypothetical registration. |
| Batch configuration has an empty observer list; the loader returns that list directly. Another mode has an observer. | Publish an evidenced absence for batch. Verify the empty graph and inspect question coverage and discrepancies. |

In the first blind trial, one worker omitted the bus namespace and another proposed a handler conditional on an unseen registry. After the prompt revision, fresh workers found `event:partner:receipt.created` and traced the diagnostic profile only as far as `env:SETTLEMENT_PLUGIN_REGISTRY`. The verified graph had five nodes and three edges, with one of two questions answered. In the separate batch trial, the worker established absence from configuration and loader evidence. The verified graph had one answered question and zero edges.

## Historical static-profile v1 oracles and results

| Test | Expected | Observed |
| --- | --- | --- |
| Flat regular package, `dedd72d151e80921d7d4d751c1c3593c331d932e` | Git tree accounts for every entry. Three static calls bind to `flat.worker:run` including a caller in another shard. The shadowed alias stays unresolved, and the identical symbol name in `flat.other` is forbidden. Dirty checkout bytes cannot alter pinned results. Nested re-inclusion, Git's extra ignore sources, tracked files matching ignore, and staged and unstaged deletions follow Git semantics. | Pass. Both directions returned the committed edge and evidence. Worktree rebuild removed the old targets. Ignored files contributed no facts. Repointing a stored edge to a valid same-named function failed verification. The source sentinel, Git index and Git revision checks passed. |
| Declared source root, `20dba2df3f504f7bdb0759dafb0c3b36f98e1d77` | Two static calls bind to `wheelhouse.impl:work`. `wheelhouse.cli:main` has source-package and declared-entry-point memberships. Identical `impl.py` and `twin.py` keep separate occurrences. Unsupported events, invalid syntax and examined absence remain distinct. | Pass. Removing one call invalidated its assertion while both endpoints survived. Restoring the call restored the edge. Changing only the configured source root removed the obsolete bindings. A bounded trace left coverage unchanged and an upward containment hop skipped siblings. An unpublished prepare and a rejected stale run preserved the previous graph. |
| Output safety, flat fixture | Reject an output directory symlink or Windows junction. | Pass. The redirected directory stayed empty. |
| Supplemental validation and replay, declared-root fixture | Equivalent baseline runs reproduce logical rows. Reject an unowned output and a review outside its task. Preserve the previous graph on rejection. Record a verified supplemental signal, blocked review and unexamined review without adding unsupported edges. | Pass. The accepted observation has a supplemental fingerprint and replays from its assigned source. The resulting typed edge set matches the baseline. |
| Click, `934813e4d421071a1b3db3973c02fe2721359a6e` | `click.termui` imports `click.utils`. `click.termui:secho` calls `click.utils:echo`. `click.termui` belongs to the `click` source package. A same-module target is forbidden and incomplete analysis remains visible. | Pass. The committed inventory matched the independent tree. The import, directed call and membership exist. The forbidden target is absent. The incoming call trace and source replay passed. |

No acceptance check was blocked in the run with Click enabled. Unsupported deployment, contracts, dynamic dispatch, and incomplete supplemental reviews remain graph coverage outcomes.

## Published demonstration

Commands run from Agentic Workbench with `$checkout` set to the same pinned Click root and `$mapper` set to the local entry point. The suite also invoked `build --commit` and `build --worktree` as standalone public commands.

```powershell
$mapper = (Resolve-Path 'skills/project-mapper/scripts/project_mapper.py').Path
$rev = '934813e4d421071a1b3db3973c02fe2721359a6e'
python -B $mapper $checkout prepare --commit $rev --agent-review
$runId = 'run-c9a31bd4210f4796bb2511748d872335'
# For a new prepare, substitute the run ID printed by that command.
# Dispatch the task IDs printed by prepare and check each result before publishing.
python -B $mapper $checkout check-shard $runId review-7299b59de0b5dad3
python -B $mapper $checkout publish $runId
python -B $mapper $checkout verify
python -B $mapper $checkout trace 'function:click.termui:secho' --type calls --direction out --depth 1
python -B $mapper $checkout trace 'function:click.utils:echo' --type calls --direction in --depth 1
python -B $mapper $checkout dimensions
python -B $mapper $checkout coverage --area '.github' --family runtime-deployment
```

- Published `$checkout/.project-mapper/graph.sqlite`. Fresh-process verification returned `integrity=ok`, 147 inventory entries, 226 nodes and 2,145 relationship records, including unresolved candidates.
- Both directions retained the import at `src/click/termui.py:16`, call at `src/click/termui.py:634` and destination definition at `src/click/utils.py:219`. The one-hop outgoing result reported traversal truncation. The incoming result reached the requested extent with `analysis_incomplete=true`. [Call site](https://github.com/pallets/click/blob/934813e4d421071a1b3db3973c02fe2721359a6e/src/click/termui.py#L634), [definition](https://github.com/pallets/click/blob/934813e4d421071a1b3db3973c02fe2721359a6e/src/click/utils.py#L219)
- The `.github` area recorded `runtime-deployment=unsupported`. Four supplemental tasks completed their assigned scope. Three recorded partial coverage. Nine source signals passed the gate and produced supplemental fingerprint `31ad207fe295699158c7496e8a059be5b4cd8c3f2179c450afc03446905eb59b`.
- Git status outside `.project-mapper/` was empty before and after publication. Git index bytes and HEAD matched.
