# Tool identities and lifecycle

Verified 2026-10-23. Source revisions and artifact digests are in
`environment.lock.yaml`; this table explains the selection.

| Tool and maintainer | Role and exact upstream | Installed/locked | Integration and runtime | Security/update/rollback |
|---|---|---|---|---|
| RTK, rtk-ai | command-output proxy; https://github.com/rtk-ai/rtk | 1.0.1, commit `4ef8730cf3a0dea11c8d64a9b90bc0616fe52100` | self-contained binary; native Codex/Antigravity hooks, OpenCode TS shim | command rewriting affects permission matching; pin release digests, test each hook, restore transaction and old version PATH |
| Caveman, Julius Brussee | concise instructions and optional broader tool suite; https://github.com/JuliusBrussee/caveman | 4.0.1, commit `d262ab3882952a59312ff3537cd86d894523c5ab` | SKILL.md, Node session hook, OpenCode plugin/commands; pinned upstream agent transform helper | installer deploys text/hooks only; cloud/proxy/routing not enabled; update source commit, rollback configuration |
| Ponytail, Dietrich Gebert | coding discipline and review skills; https://github.com/DietrichGebert/ponytail | 5.3.2, commit `16352ac229eb08a9598dcae48fe9f2b342567d86` | portable skills; pinned OpenCode 1 native plugin; Node lifecycle hooks available upstream | native Codex mode requires separate plugin trust; update lock and adapter together; rollback owned files/native uninstall as applicable |
| Codebase Memory, DeusData | persistent local code intelligence; https://github.com/DeusData/codebase-memory-mcp | optional upstream 0.12.1; installed executable is a custom fork | stdio MCP; independent JSON/TOML registration adapters | indexing writes local databases; do not transfer personal graph caches; optional upstream is not custom-fork equivalence |
| Custom CBM, correriadev fork | multigraph/governance extensions; https://github.com/correriadev/codebase-memory-multigraph-mcp | custom version and binary hash recorded; source candidate at `8dd9f4ec...` | source build uses Makefile.cbm with C/C++ compiler and vendored libraries; exact build unverified | preserve original private artifact; do not publish binary or overwrite with upstream |
| Harness Kit, romabeckman upstream / correriadev local fork | workflow skills and agent definitions; https://github.com/romabeckman/harness-kit and https://github.com/correriadev/harness-kit | local fork `06fb2a9bebfd4c6d8a9f924674b6ccc68d68cf01`; installed Antigravity plugin upstream `2a61195e...` | retained per-agent variants, not a new daemon installation | variants differ; local snapshot preserves customization without claiming all are pristine upstream |
| Open Graph, correriadev | governed knowledge-graph MCP; https://github.com/correriadev/open-graph-mcp | `5d06ef5a9e7b5100a9cbbff783eb3983ce1ddc41` | Bun 1.3.14, frozen bun.lock, Antigravity wrapper/project cwd | dependency and data restoration pending; no guessed substitute installed |
| Jev family | routing/search/UI research skills; multiple cited repositories | unresolved upstream mapping | external services/credentials vary by skill | preserve quarantined local text; no automatic network activation or invented install command |

The original RTK WinGet executable location and Codex app-owned binary are
documented in the inventory. This repository installs its own versioned copies
instead of modifying those package-manager installations. Native integration
procedures remain available from each pinned upstream checkout; review their
mutation scope before running them against an existing workstation.
