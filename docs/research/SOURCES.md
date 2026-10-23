# RESEARCH SOURCES

Verified **2026-10-23**. Local help/version output is the baseline for installed
syntax. Documentation describes advertised capabilities and can be newer.
Immutable source checkouts and lock digests provide reproducible references.

| Subject | Primary sources inspected |
|---|---|
| Codex | [Quickstart](https://developers.openai.com/codex/quickstart/), [config basics](https://developers.openai.com/codex/config-basic/), [reference](https://developers.openai.com/codex/config-reference/), [skills](https://developers.openai.com/codex/skills/), [MCP](https://developers.openai.com/codex/mcp/), [hooks](https://developers.openai.com/codex/hooks/) |
| Codex identity | OpenAI; [upstream](https://github.com/openai/codex); exact [npm 0.160.0 metadata](https://registry.npmjs.org/@openai%2fcodex/0.160.0) |
| Antigravity | Google; [getting started](https://antigravity.google/docs/getting-started), [skills](https://antigravity.google/docs/skills/), [rules](https://antigravity.google/docs/rules), [MCP](https://antigravity.google/docs/mcp), [hooks](https://antigravity.google/docs/hooks), [plugins](https://antigravity.google/docs/plugins) |
| Antigravity artifacts | [Official PowerShell installer](https://antigravity.google/cli/install.ps1), its Google-hosted updater manifests; versioned payload URLs and SHA-512 values captured in the lock |
| OpenCode | Anomaly; [upstream](https://github.com/anomalyco/opencode), [installation](https://docs.opencode.ai/docs/), [config](https://docs.opencode.ai/docs/config/), [skills](https://docs.opencode.ai/docs/skills/), [MCP](https://docs.opencode.ai/docs/mcp-servers/), [plugins](https://docs.opencode.ai/docs/plugins/), [rules](https://docs.opencode.ai/docs/rules/) |
| OpenCode baseline | [Exact npm 1.19.4 metadata](https://registry.npmjs.org/opencode-ai/1.19.4), installed package/postinstall entrypoint and native CLI help |
| RTK | [rtk-ai upstream](https://github.com/rtk-ai/rtk), [1.0.1 release](https://github.com/rtk-ai/rtk/releases/tag/v1.0.1), pinned hooks documentation and adapter source |
| Caveman | [JuliusBrussee upstream](https://github.com/JuliusBrussee/caveman), pinned 4.0.1 README, installer adapter, Codex session hook and OpenCode plugin layout |
| Ponytail | [DietrichGebert upstream](https://github.com/DietrichGebert/ponytail), pinned [5.3.2 installation guide](https://github.com/DietrichGebert/ponytail/blob/16352ac229eb08a9598dcae48fe9f2b342567d86/INSTALL.md), plugin manifests and exact npm metadata |
| Codebase Memory | [DeusData upstream](https://github.com/DeusData/codebase-memory-mcp), release 0.12.1 API asset digests, local CLI help and custom fork source candidate |
| Node | [Official 24.18.0 checksums](https://nodejs.org/dist/v24.18.0/SHASUMS256.txt), official platform archives |
| Python | [Official 3.12.10 archive](https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip); digest computed from downloaded official artifact, not an independent publisher checksum |
| Local companion projects | Exact remotes/revisions of Harness Kit, Open Graph, CBM fork and Ponytail recorded in INVENTORY.md and environment.lock.yaml |

No tutorial was used to substitute for a missing configuration contract.
Uncertain identities, build flags and per-file ownership stay unresolved.
