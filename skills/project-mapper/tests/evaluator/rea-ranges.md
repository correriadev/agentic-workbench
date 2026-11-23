# REA source-read benchmark

On Windows with Python 3.12.10, grouping known source ranges reduced median held-out time through verified SQLite publication from 6.35 s to 4.54 s. An independent sequential run measured 5.71 s and 4.66 s. Fresh model investigators took longer than the fixed-range investigator and showed no end-to-end speedup.

## Baseline investigation and sparring

The existing REA run had 231 accepted decisions, 229 answered questions, two partials, 4,278 of 9,139 eligible files cited, and 5,956 relations. Its full migration-critical relation recall has no independent denominator. Five supervisor/worker rollouts span approximately 27 h 17 min. The 16,052 shells containing a source read or search occupied 21 h 34 min summed and 3 h 16 min in the union of overlapping intervals. Parent waits overlapped child work. The union bounds direct exposure under that schedule. The traces cannot uniquely attribute the residual elapsed time to inference, queueing, repairs or operator pauses. Among 12,905 statically parsed range requests, 1,440 repeated the same path, start and count. Standalone publishes and verifies totaled about five minutes, excluding mixed shell commands.

The CLI inventories the snapshot, fingerprints the supervisor's questions, renders a prompt and starts a fresh process for each source operation. Each committed read reloads the plan and inventory, checks identity, and opens a Git batch reader. A 315 ms profile of a single read spent 178 ms in imports, 44 ms in repository lookup and 41 ms loading the run. The worker returns an owned shard. The supervisor checks the evidence and accepts the current fingerprint under a lock. Publication resolves cross-shard references and writes a candidate database. Verification reconstructs the graph against pinned source.

Three separately briefed Sol high reviewers examined timing, partition/resume, and ranking. In adversarial review, 572 exact locators were shared across shards but only 31 edge signatures repeated across shards. Six observed cross-shard discovery references lacked even a transitive plan prerequisite. Dropping overlapping claims or isolating module partitions could erase distinct conditions and cross-module links. Parallel publication would also expose a pre-existing race: a candidate built from old decisions can reach promotion after a newer same-plan acceptance. Timing did not justify changing the writer, acceptance, scheduling or cache lifetime. Known ranges can share one reader without guessing downstream references. Keep the worker's next investigation step adaptive. A tracked writer and consumer can prove a generated artifact absent from the tree. A missing link remains open.

## Inputs and rubric

REA commit `97f10e8957811bcabd8393d2dd2f2427d7ee9388`, mapper baseline `cfb845f4f2736de7604321c28829dcf8ac334b84`. Each arm starts in a new no-checkout clone with shared Git objects and a fresh output directory. The OS and Git object cache can be warm. Setup excludes cloning. Timing includes inventory, plan, prompt, source reads, shard construction, acceptance, publication, verification and relation comparison. A uses the baseline CLI. B groups only ranges already known at the same stage. C adds a live choice among eight public workflow filenames when the entry workflow is undetermined. All candidates remain available in reserve. Explicit downstream references bypass ranking.

The fixed investigator runs serially. All arms use the same five development or six held evidence ranges, inclusive source assertions and expected edge set. The held slice also allows up to eight one-line filename probes. Development follows the notes page through its script, stored notes and CSV download. Held checks the website workflow's concrete check script, SHA supplier, generated manifest's inclusion in the artifact, and conditional verification on the two hosts. Resume continues after the development decision, adds the held question, and checks the accepted shard bytes and decision. Its timer starts at continuation. Each CLI call starts a fresh process. A separate unittest kills the supervisor at a decision boundary.

| Arm | Development cold | Held cold | Held continuation | Held read calls | Ranking usage per held run |
|---|---:|---:|---:|---:|---|
| A | 4.83 s | 6.35 s | 5.46 s | 7 | Local |
| B | 4.09 s | 4.54 s | 3.79 s | 3 | Local |
| C | 4.04 s | 5.11 s | 4.13 s | 3 | One live request, 464 input and 82 output tokens |

Development ran once per arm. Held order was A/B/C/C/B/A and resume order was C/B/A/A/B/C. The table gives medians. Held read time was 2.93/1.13/1.04 s. Publish plus verify took about 1.29/1.36/1.98 s. C sent 579 bytes and received 233–234 bytes per controlled request. All four decisions were applied, with zero fallback or replay. Each ordering found the publisher on its first probe. Jev skipped development. No provider returned a billed currency amount. C missed its predeclared 15% held time reduction versus B.

An independent reviewer compared SQLite endpoints, conditions and source spans across arms and recomputed their excerpt hashes from pinned Git blobs. Each graph answered 1/1 development or held questions and 2/2 on resume. Development cited three files and yielded 3/3 expected relations, held cited two and yielded 4/4, and resume cited five and yielded 7/7. Each had zero extra relations. Fixed ranges and expected claims measure transport and validation. They do not independently estimate discovery recall.

## Live investigator check

Fresh Sol high workers received the same expanded held question, ordered candidate paths, one worker per arm and 12 pages of at most 120 lines each. C made one additional live decision (464/82 tokens, 0.23 s). The first candidate was correct in every arm. Workers returned JSON read-only for lead review. The standalone Codex CLI rejected the requested Sol model on this account, so all three used the native Sol subagent runner.

| Arm | Setup through verification | Worker elapsed | Pages attempted | Worker tokens in / out | Published relations |
|---|---:|---:|---:|---:|---:|
| A | 196.6 s | 134.0 s | 11 | 316624 / 5266 | 15 |
| B | 198.0 s | 144.5 s | 12 | 317204 / 5973 | 15 |
| C | 234.2 s | 133.0 s | 12 | 368285 / 5173 | 14 |

These single observations include scheduling and review delays. A/B workers overlapped. C waited for a worker slot. A attempted one ineligible path. Input counts include cached tokens (267008/299136/328192). Dollar cost was unavailable. All first submissions failed the same validator: each used a tracked-file endpoint for generated `website/_site/deployment.json`. The lead changed only its kind to `artifact:` (2/1/2 endpoint occurrences), then checked, accepted, published and verified. The independent reviewer confirmed all four semantic outcomes and the retained source hashes. Every live graph lacked a direct manifest-to-archive edge, although the cited content established inclusion. B's description attached the main-branch restriction to dispatch; the workflow guards the prepare job. Count this wording defect when comparing quality.

## Reproduce from the workbench root

PowerShell commands below retain clones, SQLite graphs and timing JSON under a new temporary directory. Set `TYPESAFE_API_KEY` through the environment for arm C. Without it the evaluator records a fallback on eligible cases. No credentials belong in commands, fixtures or reports.

```powershell
$source = (Resolve-Path ../rea).Path
$out = Join-Path $env:TEMP ("rea-ranges-" + [guid]::NewGuid())
New-Item -ItemType Directory $out | Out-Null
git archive -o "$out/base.tar" cfb845f4f2736de7604321c28829dcf8ac334b84 skills/project-mapper
tar -xf "$out/base.tar" -C $out
$driver = "skills/project-mapper/tests/evaluator/rea_ranges.py"
$base = "$out/skills/project-mapper/scripts/project_mapper.py"
$candidate = (Resolve-Path skills/project-mapper/scripts/project_mapper.py).Path
foreach ($id in "devA","devB","devC","heldA1","heldB1","heldC1","heldC2","heldB2","heldA2","resumeC1","resumeB1","resumeA1","resumeA2","resumeB2","resumeC2") {
    $slice = $id -creplace '[ABC].*$',''
    $arm = $id -creplace '^[a-z]+|[0-9]+$',''
    $mapper = if ($arm -eq "A") { $base } else { $candidate }
    python -B $driver $source $mapper "$out/$id" $arm $slice
    if ($LASTEXITCODE) { throw "Failed run $id" }
}
python $candidate "$out/heldB1" trace env:GITHUB_SHA --direction out --depth 2
$env:PROJECT_MAPPER_CLICK = "$out/click"
git init -q $env:PROJECT_MAPPER_CLICK
git -C $env:PROJECT_MAPPER_CLICK fetch --depth=1 https://github.com/pallets/click.git 934813e4d421071a1b3db3973c02fe2721359a6e
git -C $env:PROJECT_MAPPER_CLICK checkout -q --detach FETCH_HEAD
python -B -m unittest discover -s skills/project-mapper/tests
```

For a new live B assignment use the following commands. Substitute A with the baseline mapper or C with the candidate to repeat the other arms.

```powershell
$repo = "$out/liveB"
$setup = python -B $driver $source $candidate $repo B live | ConvertFrom-Json
Get-Content $setup.assignment
```

Pass that assignment to a fresh Sol high investigator. Start at the ordered seeds, follow explicit references, and allow up to 12 pinned read pages of at most 120 lines. Disable searches and secondary workers. Have the worker return its JSON shard. Review its English, claims, conditions and sources, then save it at `$setup.shard`. For exact CLI validation and publication:

```powershell
$checked = python $candidate $repo check-shard $setup.run revision | ConvertFrom-Json
python $candidate $repo accept $setup.run revision $checked.fingerprint --reviewed-english
$review = python $candidate $repo check-plan $setup.run | ConvertFrom-Json
python $candidate $repo publish $setup.run --reviewed-english-plan $review.fingerprint
python $candidate $repo verify
```
