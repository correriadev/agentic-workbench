# Worker preflight on pinned REA

Keep the read-only preflight as an investigator aid. Three controls submitted ineligible file endpoints; all three candidates passed the same endpoint checks on first submission. All three candidate investigators took longer to reach first submission than their paired controls. There is no demonstrated general speedup. Next test questions with multiple inputs to one verification step on another repository before expanding the preflight.

## Frozen protocol

REA `97f10e8957811bcabd8393d2dd2f2427d7ee9388`. A is the previous batched working tree, mapper SHA-256 `754040e521cbbaeeddcba730926ad81c85e5b6935dbe77b1de4e368b32ccb262`. B adds the optional plan list, worker guidance, diagnostics and preflight. The comparison measures that package. Each run used a fresh no-checkout clone, byte-identical inventory, empty decisions, one fresh native Sol high investigator, one question, 12 pages of up to 120 lines, and at most one worker-owned resubmission. Searches, external calls and target execution were disabled by instruction. The proxy recorded pages; review verified the budget. Shared Git objects and OS caches could be warm. Model cache state and token costs were unavailable. Paired repeats shared the host. Dispatch order for held-out repeats was A1/B1, then B2/A2.

The manifest is a regression. Inspection of the previous three original shards confirmed 2/1/2 uses of the ineligible manifest endpoint. Before implementation, a separate reviewer froze the Notes Electron ZIP question, four neutral facets and private source witnesses. A received the facets as question text and B as an ordered list. Workers saw identical seed paths and semantic requirements. The private scoring key was withheld. The reviewer challenged prerequisite handling and stale fingerprints. The resulting preflight runs source validation before prerequisite decisions, and supplies no acceptance fingerprint.

The held-out scoring key requires these directed, evidenced relationships and conditions:

1. Both website workflows invoke the check. The Python command runs preparation before verification and propagates failures. See `.github/workflows/website-check.yml:34–35`, `website-pages.yml:67–68`, `scripts/website.py:268–270,330–334`.
2. Selected staged files supply the generated ZIP. Distinguish its six byte payloads from writer-set metadata. See `scripts/prepare-website.py:13–20,60–92`, `scripts/website_i18n.py:621–639,667–672`.
3. Both ZIP and comparison files feed verification. Check name multiplicity and member bytes, including missing, malformed and stale cases. Metadata is outside this comparison. See `scripts/verify-website.py:410–455`.
4. The checked ZIP goes into the site artifact. Pages receives it and Cloudflare additionally receives it under `both`. Live checks compare the revision and a **different** skill archive's digest. Actual hosted Notes bytes remain unobserved. See `website-pages.yml:67–97,120–146,167–217`.

## Individual outcomes

Times are seconds from dispatch. “Accept / verify” is the first complete four-facet outcome with worker-authored bytes. A budget-exhausted partial or rejected shard does not qualify. Keep partial results when supported. Facet scores below isolate semantic coverage from invalid endpoint types.

| Case | Pages | First submission | First / final facets | Accept / verify | Final disposition |
|---|---:|---|---|---|---|
| Manifest A | 11 | Invalid generated-file kind | 4/4 → 4/4 | 208.6 / 210.6 | Worker repaired two references |
| Manifest B | 5 | Accepted | 4/4 → 4/4 | 162.7 / 165.1 | Correct kind and direct archive edge |
| ZIP A1 | 12 | Invalid generated-file kind and missing input link | 2/4 → 3/4 | Unreached | Worker repaired kinds and links. Second workflow absent, still marked answered; supervisor rejected at 353.2 |
| ZIP B1 | 12 | Structural pass, semantic rejection | 2/4 → 4/4 | 327.0 / 329.1 | Worker added source and comparison-input links |
| ZIP B2 | 12 | Accepted on all required facets | 4/4 → 4/4 | 236.3 / 238.5 | Post-publication audit found an ancillary citation error; corrected graph accepted at 416.5 and verified at 418.5 |
| ZIP A2 | 12 | Invalid directory/file kinds and missing ZIP-to-archive link | 2/4 → 3/4 | Unreached | Worker repaired kinds, added the packaging edge and recorded a gap. Partial accepted at 297.1 and verified at 299.1 |

A's first structural pass rate was 0/3. B's was 3/3. First-pass supervisor acceptance on required relations was 0/3 and 2/3. With every ancillary citation included, only manifest B survived first submission and independent audit unchanged. All B preflight calls returned success. None of these live workers corrected a validator-reported error during preflight. The data favor earlier guidance for endpoint identity; they cannot isolate the effect of the CLI. A missing-evidence fixture and an invalid-endpoint fixture exercise actual preflight feedback.

The independent post-run reviewer checked the copied submissions against pinned sources. ZIP B1 mapped every checklist item even though two input links existed only in prose. ZIP B2's fixture-exclusion citation ended at line 19, one line before the declaration. Its investigator changed that locator to line 20 without changing any claim or reading another page. A1’s initial workflow claim missed the invoking line. A2 omitted the name-match guard on a comparison edge and called the unexamined alternate entry a PR workflow. Its PR route has independent source support, but the submitted witnesses do not establish it. No arm attributed the live skill digest to the Notes ZIP. The lead never edited a shard.

## Timing and overlap

| Case | Dispatch to worker marker | Dispatch to first later-valid locator | First investigation | Waiting for review | Supervisor review | Waiting for repair | Worker rework | Preflight inside worker time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Manifest A | 17.9 | 29.3 | 89.5 | 31.0 | 15.0 | 44.9 | 10.3 | 0 |
| Manifest B | 17.6 | 31.2 | 92.1 | 14.4 | 38.6 | 0 | 0 | 1.0 |
| ZIP A1 | 24.3 | 38.3 | 127.6 | 52.7 | 27.3 | 20.6 | 100.7 | 0 |
| ZIP B1 | 17.4 | 24.5 | 134.1 | 29.7 | 40.5 | 45.6 | 59.6 | 0.9 |
| ZIP B2 | 17.8 | 43.2 | 193.0 | 29.3 | 14.8 | 19.1 | 4.7 | 1.2 |
| ZIP A2 | 18.6 | 29.9 | 190.7 | 24.4 | 16.3 | 16.8 | 30.3 | 0 |

The first investigation was the largest phase in each trial. B2 additionally spent 135.8 s between initial verification and audit reopening. Parent workload, concurrent workers, audit queues and duplicate supervisor checks affect these wall times. “Queue” ends at the worker's first instrumented command, which includes startup and initial reasoning. A later-valid locator is the first returned page containing a locator from a structurally validated submission, identified retrospectively. It can precede a rejected semantic review. Preflight durations include the mapper subprocess; separate investigator reasoning and proxy startup cannot be attributed exactly.

The [UTC event ledger](preflight-events.csv) preserves dispatch, worker start, first later-valid evidence, every submission, review, rejection, repair, acceptance, publication and verification. The overlapping experiment spanned about 11 minutes from first dispatch to last verification. Summing six worker wall times would double-count overlapping intervals.

## Reproduction

From the workbench root in PowerShell, use the preserved byte-exact control and a fresh trial directory. The control is also archived as `batched-baseline.zip` beside the raw logs. Its previous batching changes were uncommitted.

```powershell
$prior = Join-Path $env:TEMP pm-preflight-20261122
$A = "$prior/baseline/scripts/project_mapper.py"
$B = (Resolve-Path skills/project-mapper/scripts/project_mapper.py).Path
$t = (Resolve-Path skills/project-mapper/tests/evaluator/preflight_trial.py).Path
$out = Join-Path $env:TEMP ("preflight-" + [guid]::NewGuid())
foreach ($id in 'manifest-A1','zip-A1','zip-B1','manifest-B1','zip-B2','zip-A2') {
    $case,$trial = $id.Split('-')
    $arm = $trial.Substring(0,1)
    $mapper = if ($arm -eq 'A') { $A } else { $B }
    python -B $t setup ../rea $mapper "$out/$id" $case $arm
    if ($LASTEXITCODE) { throw "Setup failed for $id" }
}
```

For each run set `$r="$out/$id"` and mark dispatch immediately before spawning a fresh Sol high worker. Its first command marks start. Give it only `$r/assignment.txt`, the stated budget and permission to write its shard. Use the assignment's proxy for all reads and preflights. Preserve each submitted draft with `mark submit`. The lead reviews the original English, source, directions, conditions and gaps. Run these commands only as their corresponding events occur:

```powershell
python -B $t $r mark dispatch
python -B $t $r mark start
Get-Content "$r/assignment.txt"
# After worker writes its shard
python -B $t $r mark submit
python -B $t $r mark review
$s = Get-Content "$r/trial.json" -Raw | ConvertFrom-Json
$checked = python -B $t $r check-shard $s.run $s.question | ConvertFrom-Json
# On rejection: mark reject, return a diagnostic, worker marks repair-start, then submit and review again.
# After successful source and English review of these exact bytes
python -B $t $r accept $s.run $s.question $checked.fingerprint --reviewed-english
$plan = python -B $t $r check-plan $s.run | ConvertFrom-Json
python -B $t $r publish $s.run --reviewed-english-plan $plan.fingerprint
python -B $t $r verify
python -B $t summary $r
```

Use `python -B -m unittest discover -s skills/project-mapper/tests` for regressions. Configure the pinned Click checkout as in [the batching benchmark](rea-ranges.md) to include its optional integration case.
