---
doc_type: adr
domain: workstation
stack: [python, powershell, git]
node_id: "adr:architecture"
tags: [architecture, provisioning, adapters]
edges:
  - relation: references
    target: "adr:tests"
updated: 2026-10-23
---
# Workstation Architecture

## FOLDER STRUCTURE

```text
ai-dev-environment/
  skills/authored/   # canonical local skill trees, with ownership qualifications
  integrations/     # agent instructions, definitions, plugin inventory, npm lock
  profiles/         # deployment mapping and asset integrity hashes
  scripts/          # installer, bootstrap, validation, MCP probe
  tests/            # isolated filesystem and trust-boundary tests
  docs/             # procedures, evidence, compatibility and unresolved items
```

## LAYERS

- **Intent:** `environment.yaml` selects the core packages and profile.
- **Resolution:** `environment.lock.yaml` pins immutable commits and artifact hashes.
- **Adapters:** `scripts/environment.py` renders per-agent files.
- **Transactions:** the local state directory records prior bytes and ownership.

Both `.yaml` manifests use JSON syntax, a YAML 1.2 subset, to avoid bootstrap dependencies.

## MODULES

| Module | Responsibility | Location |
|---|---|---|
| Environment | Fetch, render, plan, apply, doctor and rollback | `scripts/environment.py` |
| Profile | Share canonical skills across all agents; exclude unresolved Jev at deployment | `profiles/personal.json` |
| Local assets | Preserve personal or locally customized content | `skills/authored/`, `integrations/` |
| Dependency locks | Pin Git revisions, binary digests, npm transitive dependencies | root manifests, `integrations/node/` |

## PATTERNS

REQUIRED: Keep one provider-neutral canonical copy of each skill; exclude `agents/openai.yaml` metadata and consolidate identical trees.
REQUIRED: Treat `authored` as a local-asset namespace, not proof of copyright ownership.
REQUIRED: Template only the discovered home prefix as `__HOME__`; preserve other asset content.
REQUIRED: Deploy copies where agent discovery roots differ; hashes track those deployment copies.
REQUIRED: Preflight all configuration conflicts; journal backups before writes.
PROHIBITED: Overwrite user edits during rollback or copy credential stores into Git.
PROHIBITED: Infer custom-fork equivalence from an upstream project name.

## INTEGRATIONS

| Component | Purpose | Connection |
|---|---|---|
| GitHub | Pinned Caveman, Ponytail and RTK source | HTTPS Git; no credentials stored |
| npm | Codex and OpenCode with exact optional platform packages | `npm ci`, integrity-locked |
| Official release hosts | Node, Antigravity, RTK, optional upstream CBM | HTTPS + recorded digest |
| MCP | Optional code intelligence | Native stdio configuration per agent |

No dependency injection framework or daemon is introduced. Dependencies remain
version-addressed in a user-owned state directory. Configuration rollback does
not delete cached binaries, source checkouts, authentication, or directories.

## REFERENCES

- [Tests](TESTS.md): executable verification strategy.
- [Install](../INSTALL.md): deployment and bootstrap.
- [Research](../research/COMPATIBILITY_MATRIX.md): capability boundaries.
