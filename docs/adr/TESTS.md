---
doc_type: adr
domain: testing
stack: [python, powershell, unittest]
node_id: "adr:tests"
tags: [testing, validation, ontology]
edges:
  - relation: references
    target: "adr:architecture"
updated: 2026-10-28
---
# Testing Protocol

## OVERVIEW

Verification covers documentation ontology integrity (`project-memory` scripts), unit tests for graph generation and validation, and PowerShell CLI wrapper tests.

## COMMANDS

| Type | Command | Purpose |
|---|---|---|
| Ontology Validation | `python skills/project-memory/scripts/validate_ontology.py docs` | Validates ADR frontmatter, `.digest.md`, `.graph.json`, and size limits |
| Graph Generation | `python skills/project-memory/scripts/generate_docs_graph.py docs` | Rebuilds `docs/.graph.json` from ADR/feature frontmatter |
| CLI Wrapper Tests | `powershell -NoProfile -File skills/ask-antigravity/scripts/Test-Invoke-Antigravity.ps1` | Tests argument normalization and headless CLI invocation |

## MINIMUM COVERAGE

Verification requires 100% pass rate for the `project-memory` unit test suite and zero ontology validation errors in `docs/`.

## PATTERNS & BEST PRACTICES

- **REQUIRED:** Run `generate_docs_graph.py` and `validate_ontology.py` after modifying any file under `docs/`.
- **REQUIRED:** Keep unit tests deterministic and isolated using temporary directories.
- **PROHIBITED:** Depend on live external API keys or active LLM sessions in automated tests.

## TOOLING

- **Framework:** Python 3.12+ `unittest` and PowerShell test assertions.
- **CI:** None (local verification commands only).

## TROUBLESHOOTING

If `validate_ontology.py` reports a stale graph, run `python skills/project-memory/scripts/generate_docs_graph.py --root docs` first, then re-run validation.

## REFERENCES

- [Architecture](ARCHITECTURE.md): Repository structure and skill layers.
