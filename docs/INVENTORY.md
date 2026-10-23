# INVENTORY

Inspected **2026-10-23**. Paths below use `~` for the original home. No credential
values or account sessions are included. The machine-readable asset ledger is
[local-assets.json](research/local-assets.json).

## EXECUTABLES

| Component | Observed version | Original executable |
|---|---|---|
| Codex CLI | 0.160.0 | `~/AppData/Local/Programs/OpenAI/Codex/bin/codex.exe` |
| Antigravity CLI | 1.4.6 | `~/.gemini/bin/agy.exe` (not resolved as `antigravity` on PATH) |
| Antigravity app | product 2.25.0.0 | `~/AppData/Local/Programs/antigravity/Antigravity.exe` |
| OpenCode | 1.19.4 | `~/AppData/Roaming/npm/opencode.ps1` |
| RTK | 1.0.1 | `~/AppData/Local/Microsoft/WinGet/Links/rtk.exe` |
| Codebase Memory | custom mgh-8dd9f4ec-codex-20261021-relaxed | `~/AppData/Local/Programs/codebase-memory-mcp/codebase-memory-mcp.exe` |
| Node | 24.18.0 | `C:/Program Files/nodejs/node.exe` |
| Python | 3.12.10 | `~/AppData/Local/Programs/Python/Python312/python.exe` |
| Git | 2.55.0.windows.3 | `C:/Program Files/Git/cmd/git.exe` |
| Bun | 1.3.14 | resolved through PATH; required by Open Graph |

Additional installed application directories include Ollama, VS Code and OpenCode
Desktop. Their individual configuration was outside this capture boundary; they
are not silently installed as mandatory dependencies.

## SKILLS AND AUTHORITY

| Root | Skill installations | Treatment |
|---|---:|---|
| `~/.codex/skills` | 37 | Retain variants; known community sources referenced |
| `~/.agents/skills` | 22 | Retain variants; known community sources referenced |
| `~/.gemini/config/skills` | 14 | Retain variants; known community sources referenced |
| `~/.config/opencode/skills` | 34 | Retain variants; known community sources referenced |
| `~/.gemini/antigravity-cli/skills` | 12 | Retain variants; known community sources referenced |

There are **119 observed skill installations**, including duplicates, and **49
canonical retained local trees**. Shared Caveman skills are reinstalled from
4.0.1; Ponytail is pinned to 5.3.2. Built-in `.system` and cached plugin skills
remain product-distributed. Tree hashes identify exact duplicates; different
metadata/reference files keep a tree distinct. No claim of author ownership is
inferred solely from its installed location.

The Codex version is the observed authoritative deployment copy for its own
profile. Antigravity and OpenCode differences remain mapped independently.
`__HOME__` substitution, UTF-8 BOM removal and LF normalization are declared
capture transformations. Original tree hashes precede those transformations.
Jev snapshots retain uncertain third-party provenance and remain disabled.

## INSTRUCTIONS, AGENTS AND AUTOMATION

Global Codex AGENTS includes the CBM skill preference and RTK awareness file.
OpenCode AGENTS includes CBM and Caveman instruction blocks. Antigravity GEMINI
contains CBM rules. These are retained as explicit agent-specific templates.
Allowlisted model/reasoning/service-tier/TUI preferences and Antigravity visual
preferences are retained separately. Existing preferences take priority; security
grants and app runtime settings are excluded.
Custom agent definitions are retained in Codex TOML and OpenCode Markdown forms;
Cavecrew definitions use the pinned upstream conversion helper for OpenCode.

Codex `hooks.json` contains Caveman SessionStart and RTK PreToolUse. The
`notify` command is an app-owned computer-use binary, so it is documented but
not transplanted. Codex hook trust hashes, project trust paths, desktop behavior
and Windows sandbox settings are not exported as installation policy.

OpenCode has RTK and CBM local plugins plus Caveman and an unversioned Ponytail
reference. The new core pins Ponytail and RTK/Caveman source; the custom CBM
augmentation plugin is preserved in `integrations/opencode/quarantine/` and
requires separate source/build review before activation. OpenCode package
manifest uses `@opencode-ai/plugin` 1.18.9 despite CLI 1.19.4; that old generated
node_modules tree is not copied.

Antigravity has Harness Kit, Open Graph, Ponytail, Caveman and RTK plugin
registrations across common and legacy paths. CLI skills are duplicated in the
common configuration on this machine; the new adapter explicitly serves both
roots. Plugin activation and old import manifests are not assumed portable.

## MCP AND PLUGINS

| Surface | Configuration | Observed servers |
|---|---|---|
| Codex | `~/.codex/config.toml` | custom CBM; app-owned node_repl |
| Antigravity | `~/.gemini/config/mcp_config.json` | custom CBM; Bun Open Graph wrapper with project cwd |
| OpenCode | `~/.config/opencode/opencode.jsonc` | custom CBM |

Codex app plugin identifiers and marketplace provenance are retained in
`integrations/codex/plugins.json`. App-distributed browser/document/computer-use
runtimes are not copied. Postman 1.1.0 and Ponytail 5.3.2 are observed; Postman's
installed exact source revision remains unresolved. Authenticated plugin
connections must be recreated per machine.

## LOCAL SOURCE PROVENANCE

| Repository | Observed revision/state |
|---|---|
| `correriadev/agents-skills` | initialized repository without a HEAD commit; no tracked author baseline |
| `correriadev/harness-kit` | `06fb2a9bebfd4c6d8a9f924674b6ccc68d68cf01` |
| installed `romabeckman/harness-kit` plugin | `2a61195ec5ddee36762c378e8a0a132105b0a537` |
| `correriadev/codebase-memory-multigraph-mcp` | HEAD `14446dfcc00294edfebe8cf4afd482e565fdf095`, local modifications; binary reports earlier 8dd9f4ec source candidate |
| `DeusData/codebase-memory-mcp` local clone | `3457b21b0a3d75960c07ed3ec666a9e684985ef9` |
| `correriadev/open-graph-mcp` | `5d06ef5a9e7b5100a9cbbff783eb3983ce1ddc41` |
| installed Ponytail Antigravity checkout | `09c434ab73ca43761c5d8b0c5d341926c2fba710`; differs from pinned 5.3.2 tag |

## EXCLUDED DATA

Credential files, OAuth/account stores, sessions, histories, private graph and
horizon databases, logs, generated caches, node_modules, app runtime binaries,
permission grants and project trust records are excluded. Machine-specific
MCP environment names were inspected, but their values were not exported.
Project-scoped discovery was limited to this initially empty workspace and
selected known source manifests; this is not an inventory of every project.
