# Project Mapper workflow

## Snapshot and artifacts

Run `python "<mapper>" <repo-root> build --commit <revision>` or `build --worktree`. The [scanner](../scripts/scan_files.py) also accepts `<repo-root> --commit <revision>` or `<repo-root> --worktree` and prints JSON.

Committed mode enumerates the full tree and reads Git blobs by object ID. Ignore rules do not affect committed entries. Worktree mode uses the index for tracked paths and Git's standard excludes for untracked paths. Precedence is the nested `.gitignore` chain, then `$GIT_DIR/info/exclude`, then `core.excludesFile`, whose default is `$XDG_CONFIG_HOME/git/ignore` or `~/.config/git/ignore`. Within a Git ignore source, Git applies its usual last-match and re-inclusion semantics. Git may report a pruned ignored directory as a single inventory record. Tracked paths bypass ignores. The scanner records missing tracked files, including absent staged HEAD deletions.

Both modes exclude root `.project-mapper/` from analysis. A tracked entry under that directory receives an excluded inventory row. Links, Git submodules, and embedded repositories are boundaries. Worktree reads check the opened file against the inventoried bytes, with rechecks before publication. Quiesce active worktree changes during a build. A snapshot mismatch requires a fresh prepare.

`prepare` writes `inventory.json`, `plan.json` and local baseline shards under a unique run directory. `publish <run>` validates shards and stages SQLite inside that directory before replacement. The previous graph stays available if validation or replacement fails. The graph contains the plan, task states, sanitized accepted observations, and fingerprints needed for replay. Staging runs remain available for inspection. The generated README follows the database replacement and may lag the authoritative graph if its write fails.

## Frozen profile

`python-static` version 1 uses `ast`, `symtable`, and `tomllib`. The plan records the Python parser version. Use the same Python major/minor to verify or reproduce a build.

| Family | Supported evidence and limits |
| --- | --- |
| Structural | Regular Python packages with `__init__.py`, loose modules at the repository root or under conventional `src/`, and an explicit `[tool.setuptools.package-dir]` empty-key source root. A declared source root overrides the inferred layout. Structural relationships include package/module/function containment, syntax-backed module imports, and declared `project.dependencies` or `build-system.requires`. Relative imports use the importing package. Identified standard-library imports and declared distributions get external nodes. |
| Semantic | Direct calls inside module-level functions to uniquely bound imported top-level functions in other modules. Supports `from x import f as g`, `import x as y; y.f()`, dotted imports, and resolvable relative module aliases. Checks module writes and lexical shadowing. Conditional or repeated alias bindings, wildcard imports, decorated or rebound targets, dynamic dispatch, and unsupported scopes retain unresolved outcomes. Source guards remain attached to calls and imports. A `project.scripts` declaration can register an exact `module:function` target. |
| Membership | Regular package chains provide `source-package` evidence. Checked `project.scripts` and `tool.pytest.ini_options.testpaths` provide `declared-entry-point` and `declared-test-suite` evidence, respectively. A node can have memberships in several dimensions. |
| Other signals | Deployment, event contracts, interface schemas, data ownership, verification beyond declared paths, and other source languages receive coverage outcomes when signaled. Architecture headings are navigation candidates. Missing configured roots and unresolved registrations are recorded as discrepancies with source evidence. |

The profile covers regular packages. Namespace packages, arbitrary import paths, re-exports, implicit runtime imports, monkey-patching and framework dispatch need additional evidence. Treat resolved calls as static relationships in the selected namespace. The plan accounts for repository-wide inventory, including areas with no applicable profile inputs.

## Worker protocol

1. Run `prepare --commit <revision> --agent-review`, or use `--worktree`. The output lists the run ID, inventory and plan paths, and each review task's output and dependencies. The deterministic extractor has already handled the independent baseline areas.
2. Dispatch the independent review tasks concurrently in batches sized to the host. Give each reviewer the repository root, fixed snapshot identity, run and task IDs, plan pointer, inventory pointer, and exact output path. Ask the review question from the task. Source reads use `read-input <run> <task> <repo-relative-path> --start <line> --count <1..120>`. Use file content identities returned by the reader. Reviewers may read their plan and inventory slice and write their own shard only.
3. Accept only the schema below. Use `completed` when all assigned paths were examined. Use `partial` or `blocked` with the paths actually examined when work remains. Findings can flag a material discrepancy or candidate, such as a release pipeline or declared interface that the static profile cannot link. Omit arbitrary text, credentials and excerpts. `check-shard <run> <task>` verifies task ownership, input identity, coverage, and source locators. Retry one recoverable validation or worker failure in the original assignment. `publish <run>` records missing review shards as unexamined and invalid shards as blocked.
4. Publish after the review wave. The supervisor validates shard filenames, recomputes baseline findings, rechecks supplemental loci, and owns all graph and plan state. Text signals remain candidate observations until a relationship's own resolution rule establishes its endpoints.

```json
{
  "plan": "<plan.id>",
  "task": "<task.id>",
  "snapshot": "<plan.snapshot>",
  "status": "partial",
  "inputs": ["architecture.md"],
  "findings": [
    {"path": "architecture.md", "content_id": "<content_id>", "line": 4, "kind": "runtime-deployment"}
  ]
}
```

The checked kinds are `runtime-deployment`, `event-contract`, `interfaces`, `data-ownership`, `verification`, and `architecture-declaration`. Each has a narrow term check in [pipeline.py](../scripts/pipeline.py). Host dispatch is optional for a deterministic build. An explicitly prepared review can publish partial coverage when agent capacity is unavailable.

## Inspect

```text
python "<mapper>" . coverage --family semantic
python "<mapper>" . dimensions
python "<mapper>" . node "function:package.module:handler"
python "<mapper>" . trace "function:package.module:handler" --direction out --type calls --depth 4
python "<mapper>" . trace "function:package.backend:helper" --direction in --type calls
python "<mapper>" . verify
```

`node` accepts a typed key or exact name and returns evidence plus incoming and outgoing edges. Candidate endpoints remain queryable. `trace` accepts repeated `--type`, direction, depth, node, and edge bounds. Traversal uses cycle protection. Following containment upward leads through ancestors and skips sibling expansion. `truncated` means a requested bound stopped part of the traversal. `analysis_incomplete` means recorded coverage gaps or unresolved candidates remain. They can vary independently. Coverage includes analysis outcomes, reasons, and planned assignments. `scoped_absence` applies to the examined family and area where the profile found zero relationships.

Use any SQLite reader with read-only access. `inventory` accounts for inputs. `nodes` stores logical identities. `occurrences` holds paths, content IDs, exact AST byte spans or TOML keys, and excerpt digests. `observations` and `provenance` record claim basis, authority, shared extraction method and limitations. Join claims to observations through `relationship_observations` or `membership_observations`. `coverage`, `tasks` and `discrepancies` show where to investigate. `verify` checks schema and all logical rows by reopening the named source and replaying the admitted claims. Commit verification requires the original Git objects. Worktree verification requires the recorded bytes and inventory policy.

## Design references

- Logical entities, byte-bound occurrences, normalized provenance, separate structural and semantic coverage, and typed traversal with containment controls. [REA evidence envelope](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/src/domain/evidence.ts#L393-L421), [REA application workflows](https://github.com/morluto/rea/blob/d865c776463d3095b623b15a9cf6bb20793de228/docs/guides/javascript/javascript-application-workflows.md#semantic-relation-tracing)
- Persisted macro-to-micro assignments, isolated outputs, deterministic supervisor checks, and parallel independent work. [Researcher](https://github.com/correriadev/agentic-workbench/blob/main/skills/researcher/SKILL.md)
- Inventory passes and evidence-backed comparison of declared and observed architecture. [DiUS deep recon](https://github.com/DiUS/agent-toolkit/blob/main/skills/codebase-discovery/playbooks/01-deep-recon.md)
- Source definitions and references separate from display limits. Resolver metadata is an input to binding. [Aider repository map](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py), [Nx project graph](https://github.com/nrwl/nx/blob/master/packages/nx/src/project-graph/build-project-graph.ts)
- Memberships derived after fact extraction and independent of dependency edges. The event contract gap remains explicit. A future AsyncAPI profile needs application-relative send/receive direction and channel/message/context qualifiers. [ARCADE Core](https://github.com/usc-softarch/arcade_core/blob/master/scripts/run_clustering.py), [AsyncAPI operation object](https://github.com/asyncapi/spec/blob/master/spec/asyncapi.md#operationObject)
- Summaries navigate retained source evidence and steer a reader to independently checkable claims. [ArchMapper](https://github.com/yannick-leguennec/archmapper), [Reverse Spec](https://github.com/sinedied/agent-skills/blob/main/.agents/skills/reverse-spec/SKILL.md)
