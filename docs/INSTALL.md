# INSTALL

## PREREQUISITES

Install Git and one supported agent. The installer also needs Python 3.12+,
HTTPS access to official release hosts/GitHub/npm, and sufficient user-owned
disk space (several GB during downloads and source checkout). Node is installed
privately; a preinstalled Node is not required by the Python installer.

Windows x64 bootstrap, CORRECT:

```powershell
powershell -NoProfile -File scripts/bootstrap.ps1 -Command plan
powershell -NoProfile -File scripts/bootstrap.ps1 -Command install
. "$env:USERPROFILE/.local/share/ai-dev-environment/env.ps1"
```

On macOS/Linux install Python 3.12+ from python.org or the native package manager.
CORRECT:

```sh
sh scripts/bootstrap.sh plan
sh scripts/bootstrap.sh install
. "$HOME/.local/share/ai-dev-environment/env.sh"
```

The generated environment applies only to that shell and its child processes.
Launch agents from that shell. GUI launchers do not inherit it automatically.
No shell profile, system PATH, existing agent binary, or machine policy is changed.

## PHASES

| Command | Behavior |
|---|---|
| `plan` | Offline, read-only inspection of desired configuration and conflicts |
| `fetch` | Download/hash-check versioned artifacts, checkout pinned source and run locked npm installation |
| `apply` | Deploy available assets using backups and a journal; no downloads |
| `install` | Fetch then apply |
| `doctor` | Check core versions, binary markers and managed-file hashes |
| `rollback --transaction ID` | Restore prior file bytes if no later edits exist |

Use `python scripts/environment.py COMMAND --home ABSOLUTE_DIRECTORY` for a
disposable home. `--agents codex` limits deployed configuration, while dependency
fetch still installs the shared core toolchain. Test credentials are never copied.

Review reported conflicts. `--replace` authorizes backing up and replacing
unmanaged or edited files; it does not resolve conflicting tool registrations.
Manually reconcile old hooks/plugin references first. Preserve commented JSONC
with a manual merge: the installer deliberately refuses to parse it as JSON.

## MCP SELECTION

No MCP implementation is selected implicitly. The source workstation's custom
CBM and Open Graph are tracked as unresolved baseline dependencies.

To restore the exact existing Windows CBM binary, CORRECT:

```powershell
python scripts/environment.py apply --custom-cbm "$env:LOCALAPPDATA/Programs/codebase-memory-mcp/codebase-memory-mcp.exe"
```

Its hash must equal the lock; this references the existing executable and does
not archive it. Keep a separately encrypted/private artifact backup for migration.
To deliberately use upstream instead, run `install --upstream-cbm`. That downloads
upstream 0.12.1 and registers it for all selected agents. It changes capabilities.
An existing conflicting Codex server registration requires manual migration.

## ACCEPTANCE

Run repository verification, unit tests, and doctor. Authenticate Codex, OpenCode
providers and Google through their supported flows. In Codex open `/hooks` and
trust the installed definitions. Confirm Antigravity RTK activation in
Customizations. Confirm one real shell command uses RTK before relying on savings.

Probe each chosen MCP executable with `scripts/check_mcp.py`, then check native
agent MCP discovery. Do not index projects automatically. Restore app plugins
from the inventory and record unresolved source/build provenance.

Full reproduction is not complete until `research/UNRESOLVED.md` is resolved.
Doctor verifies the implemented core; it does not validate GUI, auth, model access,
the disabled Jev tools, or every imported plugin.
