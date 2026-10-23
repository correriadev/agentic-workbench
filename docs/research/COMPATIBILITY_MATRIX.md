# COMPATIBILITY MATRIX

Verified **2026-10-23**. Installed versions are the baseline; current web pages
may describe newer releases. **Observed** means local inspection/runtime probe,
**documented** means official source, and **unverified** is not a support claim.

## AGENTS AND OPERATING SYSTEMS

| Agent | Installed baseline | Upstream OS coverage | Implemented adapter | Runtime evidence |
|---|---|---|---|---|
| Codex CLI | 0.160.0 | Windows, macOS, Linux | npm exact lock, instructions, skills, agents, hooks, optional MCP | Windows x64 version probe; authentication pending |
| Antigravity CLI | agy 1.4.6 | Windows x64/arm64, macOS x64/arm64, Linux x64/arm64 artifacts verified | Hashed official binary, CLI skill root, RTK plugin, optional MCP | Windows x64 version and RTK plugin validation |
| Antigravity installed app | executable product version 2.25.0.0 | Official App/IDE downloads exist for Windows/macOS/Linux; surface differs | Common config skills/rules and MCP; GUI install not automated | Executable inspected, GUI not launched |
| OpenCode | 1.19.4 | Windows, macOS, Linux; npm platform packages pinned | Version-1 `plugin`, global skills, commands, agent Markdown, optional MCP | Windows x64 version and native config debug pass with three plugins |

The installed executable name does not distinguish Google's evolving App versus
IDE branding reliably. CLI and common configuration adapters are explicit;
GUI-only behavior remains unverified. Official [Antigravity getting started](https://antigravity.google/docs/getting-started)
documents the distinct surfaces and installers. [Codex quickstart](https://developers.openai.com/codex/quickstart/)
and [OpenCode installation](https://docs.opencode.ai/docs/) establish their official install channels.

The installer locks artifacts for Windows x64, macOS x64/arm64 and Linux
x64/arm64. Windows arm64 Antigravity/Node exist, but RTK is not locked for that
platform, so complete core installation fails explicitly. Linux musl compatibility
is not claimed for the whole stack. Only Windows x64 has been executed here.

## SKILLS, RULES AND CONFIGURATION

| Capability | Codex 0.160 baseline | Antigravity | OpenCode 1.19 baseline |
|---|---|---|---|
| Global config | `~/.codex/config.toml`, or `CODEX_HOME` | observed `~/.gemini/config/config.json`; CLI-specific settings also exist | `~/.config/opencode/opencode.jsonc` |
| Project config | `.codex/config.toml` under trust policy | `.agents/` customization files | `opencode.json`/`opencode.jsonc`, `.opencode/` |
| Global skill adapter | `~/.codex/skills/` observed and legacy documented | App/IDE: `~/.gemini/config/skills/`; current CLI docs: `~/.gemini/antigravity-cli/skills/` | `~/.config/opencode/skills/` |
| Project skills | `.agents/skills/` in current ecosystem; legacy `.codex/skills/` | `.agents/skills/` | `.opencode/skills/`, `.agents/skills/` compatibility |
| Rules | global/project `AGENTS.md`; nested instructions specialize | global `~/.gemini/GEMINI.md`; directory `AGENTS.md`/`GEMINI.md`; `.agents/rules/` | global `~/.config/opencode/AGENTS.md`, project `AGENTS.md` |
| Agent definitions | retained `.codex/agents/*.toml` | CLI skill commands supported; no automatic conversion of Codex agents | retained global `agents/*.md`; Cavecrew transformed by pinned upstream helper |
| Custom commands | skills; no invented cross-agent slash-command format | skills become CLI slash commands; legacy workflows need review | global `commands/*.md`, plugin-provided commands |
| Safe configuration automation | owned files + checked optional TOML append | checked JSON MCP merges + generated plugin files | JSON-compatible JSONC merges; commented JSONC refused |

Skill-path sources: [Codex workflow examples](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex),
[Antigravity skills by surface](https://antigravity.google/docs/skills/),
and [OpenCode skills](https://docs.opencode.ai/docs/skills/).
Rule sources: [Antigravity rules](https://antigravity.google/docs/rules),
[OpenCode rules](https://docs.opencode.ai/docs/rules/),
and [Codex configuration](https://developers.openai.com/codex/config-basic/).

## MCP, PLUGINS AND HOOKS

| Capability | Codex | Antigravity | OpenCode |
|---|---|---|---|
| MCP format | `[mcp_servers.NAME]`, `command`, `args`; HTTP supported officially | `mcp_config.json`, `mcpServers`, command/args or remote definition | `mcp.NAME`, `type: local`, command array; remote supported officially |
| Global MCP path | `~/.codex/config.toml` | `~/.gemini/config/mcp_config.json`; workspace `.agents/mcp_config.json` | global `opencode.json[c]` |
| Plugin mechanism | marketplace + plugin add; local/Git marketplace ref supported by installed help | plugin install/import/validate/enable in installed CLI | npm/local plugin references, JS/TS plugin hooks |
| Hook mechanism | `~/.codex/hooks.json`; trust required; RTK `PreToolUse`, Caveman `SessionStart` | named event map in hooks.json; RTK plugin uses `PreToolUse` + `run_command` | JS plugin callbacks; no assumed Codex hooks.json support |
| Implemented hook behavior | exact pinned upstream commands/layout; trust still manual | generated RTK plugin passes strict CLI validation | RTK upstream TS shim; Caveman layout and command assets; Ponytail local pinned plugin |
| Plugin restoration limit | app-bundled tools need app/account; no cache copying | App and CLI paths differ by generation; inspect activation | baseline 1 uses `plugin`; version 2 changes to `plugins` and directory references |

Sources: [Codex MCP](https://developers.openai.com/codex/mcp/),
[Codex hooks](https://developers.openai.com/codex/hooks/),
[Antigravity MCP](https://antigravity.google/docs/mcp),
[Antigravity hooks](https://antigravity.google/docs/hooks),
[Antigravity plugins](https://antigravity.google/docs/plugins),
[OpenCode MCP](https://docs.opencode.ai/docs/mcp-servers/),
[OpenCode plugins](https://docs.opencode.ai/docs/plugins/), and the pinned
[Ponytail installation guide](https://github.com/DietrichGebert/ponytail/blob/16352ac229eb08a9598dcae48fe9f2b342567d86/INSTALL.md).

## PRECEDENCE, VARIABLES AND UPDATES

- **Codex:** command-line overrides outrank profile/user/project configuration;
  managed policy can constrain it. `CODEX_HOME` relocates user config. Do not
  import trust grants or app-generated MCP runtime paths. Review
  [config reference](https://developers.openai.com/codex/config-reference/).
- **Antigravity:** current rules are cumulative; more specific directory rules
  take priority. Global MCP and workspace MCP are distinct. Legacy CLI/App
  installation paths differ from current documentation; the adapter writes both
  documented skill roots but does not promise every GUI version uses both.
- **OpenCode:** documented configuration merges in increasing priority from
  remote/global to custom `OPENCODE_CONFIG`, project and directory settings, then
  inline `OPENCODE_CONFIG_CONTENT`. `OPENCODE_CONFIG_DIR` and XDG settings can
  relocate paths; this personal adapter targets the observed default layout.
  See [config locations](https://docs.opencode.ai/docs/config/).
- **Runtime:** pinned Node 24.18.0 supplies npm; Python 3.12+ runs the installer.
  `DO_NOT_TRACK=1` applies to shell-launched tools. Provider credentials remain
  external; access and model availability require authenticated verification.

Newer releases are a separate migration. Native capability documentation is
not proof that a retained older executable implements the newest schema.
