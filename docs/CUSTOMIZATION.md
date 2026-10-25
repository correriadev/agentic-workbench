# CUSTOMIZATION

## PERSONAL ASSETS

Use the shared `skills` catalog in `profiles/personal.json` for every supported agent.
`docs/research/local-assets.json` records original installation locations and
hashes. Equal local trees share one repository source. Provider-specific `agents/openai.yaml`
metadata is removed; skills with identical remaining files are consolidated.

`skills/authored/` includes local customizations of uncertain authorship and
quarantined Jev snapshots. It is not a licensing declaration. Jev is skipped by
the installer until provenance review. Preserve portable instructions and references when
editing a skill; do not modify a downloaded source cache as the canonical copy.

Home prefixes are stored as `__HOME__` and rendered to the target home. Other
Windows assumptions and references to external projects remain visible. A
cross-platform installer does not make every captured skill cross-platform.

After reviewing intentional asset edits, refresh `profiles/assets.sha256.json`
from the SHA-256 of every file under `skills/authored` and agent integration
folders. Run repository validation; commit the asset and hash change together.

## NATIVE PLUGINS

The core uses skills for portable behavior, with OpenCode's pinned native
Ponytail plugin and RTK/Caveman adapters. It does not install Caveman Cloud or
proxy routing. Avoid stacking a native plugin and a copied equivalent skill set.

Codex native Ponytail is preferred if maintaining the existing plugin-based
configuration. Installed CLI help verifies pinned marketplace refs. CORRECT:

```sh
codex plugin marketplace add DietrichGebert/ponytail --ref 16352ac229eb08a9598dcae48fe9f2b342567d86
codex plugin add ponytail@ponytail
```

Before switching to that mode, remove Ponytail entries from the skill-only
deployment selection, back up config and inspect native plugin files. The
generic deployment list is currently hardcoded in `Environment.desired`; edit
that list and test the adapter as part of a native-plugin migration. Native
plugin commands mutate agent-managed state outside installer transactions.
Use native `codex plugin remove ponytail` to remove it; rollback alone is not enough.

For Antigravity, inspect `agy plugin help` and installed plugin schemas first.
Common App/IDE plugin roots and current CLI plugin roots differ. Use native
validation and UI activation; do not copy Codex hooks.json into Antigravity.
Ponytail's Gemini extension is not automatically assumed identical to every
Antigravity version.

## MCP AND EXTERNAL PROJECTS

Use `mcp/profiles.json` for the canonical desired server identities and dependency
boundaries. The adapters render different JSON/TOML shapes for each agent.
Do not put keys in that manifest; supply credentials through the official secret
store or environment as appropriate. Existing unrelated MCP servers are preserved.

Open Graph and the custom CBM source candidates are pinned in the root lock.
Their existence does not establish a reproducible build. See unresolved items
before enabling them. Keep graph data and personal project memory outside Git.

## PROFILES AND UPDATES

Currently one personal profile is implemented. `--agents` chooses which agents
receive configuration; arbitrary profile composition is not implemented.
Adding a tool requires a locked source/artifact, explicit adapter behavior,
recovery implications, upstream references and a relevant acceptance check.
