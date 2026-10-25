# VALIDATION

Executed **2026-10-23**, Windows x64. This is evidence of the implemented core,
not a claim that the original full workstation is reproducible yet.

## PASSING CHECKS

| Check | Observed result |
|---|---|
| Offline safety suite | 20 tests pass; no skips in the executed Windows run |
| Real isolated install | Official pinned binaries and Git sources fetched; npm lock installed; 468 managed files converged |
| Repeat install/apply | `No changes`; plan reports 468 identical files, zero conflicts and no unavailable sources |
| Doctor | No core version/integrity/configuration failures; explicitly reports `full_baseline_complete: false` |
| Codex native config | `mcp list --json` succeeds under isolated CODEX_HOME; zero servers in the default core profile |
| OpenCode native config | `debug config` succeeds with three plugins (Ponytail, Caveman, RTK) and 16 agent definitions |
| Antigravity plugin | `plugin validate ... --strict --json` succeeds with no findings for RTK |
| Optional upstream CBM | Pinned 0.12.1 archive fetched and verified; three native agent registrations applied |
| Real rollback | Optional upstream registration transaction rolled back successfully; subsequent core install is unchanged |
| Windows bootstrap | PowerShell plan wrapper succeeds; pinned embeddable Python runs the planner successfully |
| Dependency references | Source commits and release digests resolved; npm entries integrity-locked; CI action commit IDs verified against exact tags |
| Repository checks | Asset hash manifest, source pins, npm lock consistency, TOML syntax, document size and limited credential-pattern scan pass |

The machine-readable runtime summary is [core-acceptance.json](core-acceptance.json).
Safety tests cover conflict preservation, idempotence, byte restoration, created
file removal, post-install edit protection, corrupt backup rejection, partial
write recovery, exclusive locking, traversal, symlinks, zip-slip, bad downloads,
JSONC refusal, native MCP schemas, process-home isolation and protocol-probe bounds.

## FAILURES AND LIMITS

- Preference capture exposed invalid nested TOML serialization during sandbox
  testing. The writer now uses TOML inline-table syntax and validates generated
  TOML before deployment. The affected sandbox transaction was rolled back; the
  new preference regression and final runtime checks pass.


- Both the custom CBM and separately downloaded upstream CBM exited before
  initialize in an empty temporary home. The custom diagnostic was
  `could not load saved runtime settings`. No graph database was copied to mask it.
- An early OpenCode debug probe timed out with incomplete environment isolation.
  The final check explicitly overrides HOME, USERPROFILE, XDG roots, CODEX_HOME
  and OPENCODE_CONFIG_DIR and passes. The initial timeout's cause is not proven.
- An initial long source-checkout path failed for RTK fixtures on Windows.
  The fetcher now sets repository-local `core.longpaths=true`; the repeated
  checkout and acceptance pass. System Git configuration was not changed.
- GUI behavior, authenticated model requests, actual hook execution, app plugin
  reconnection, Open Graph setup and Jev network tools were not validated.
- CI workflows were authored, not submitted to a remote runner. macOS/Linux
  runtime execution and the no-Python PowerShell fallback branch remain untested
  end-to-end; the fallback's downloaded Python itself was executed successfully.

## SHARED SKILL CATALOG FOLLOW-UP

Removed 13 provider-specific `agents/openai.yaml` files and consolidated ten
otherwise identical skill trees into 39 canonical skills. All supported agents
now consume the same profile catalog; Jev quarantine remains in place.
The follow-up offline suite passes 21 tests, including shared deployment roots;
repository integrity checks pass. The earlier runtime counts above describe the
initial acceptance run, before this catalog normalization.

## REPRODUCE THE CHECKS

CORRECT, from the repository root:

```powershell
python scripts/verify_repository.py
python -m unittest discover -s tests -v
python scripts/acceptance.py --home "$PWD/.work/acceptance-home"
```

The acceptance command downloads and installs into the supplied disposable home;
it refuses the real home or any ancestor. It captures only summarized results,
not full native configuration output. It does not authenticate accounts or
claim MCP readiness. Run the standalone protocol probe for each selected server.
