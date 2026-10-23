# ai-dev-environment

A versioned personal AI workstation: pinned tools, preserved skills, agent
adapters, a safe installer, and recovery instructions.

On a new machine, install Git and one supported agent, clone this repository,
then ask: **"Read AGENTS.md and install my development environment."**

The implemented core installs Codex 0.160.0, OpenCode 1.19.4, Antigravity CLI
1.4.6, Node 24.18.0, RTK 1.0.1, Caveman 4.0.1 skills, and Ponytail 5.3.2.
Windows x64 has an isolated runtime acceptance test. Other platforms remain
unverified at runtime. See [installation](docs/INSTALL.md) and
[compatibility](docs/research/COMPATIBILITY_MATRIX.md).

**Full workstation reproduction still has explicit gaps:** the custom Codebase
Memory build, Open Graph setup, Jev provenance, app-managed integrations, and
authentication. See [unresolved items](docs/research/UNRESOLVED.md).

- [Installer instructions](AGENTS.md)
- [Inventory](docs/INVENTORY.md)
- [Recovery](docs/RECOVERY.md)
- [Security](docs/SECURITY.md)
- [Validation evidence](docs/research/VALIDATION.md)
- [Documentation index](docs/README.md)
