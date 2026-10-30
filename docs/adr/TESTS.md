---
doc_type: adr
domain: testing
stack: [python, powershell, bash, unittest]
node_id: "adr:tests"
tags: [testing, unit-tests, validation, scripts]
edges:
  - relation: references
    target: "adr:architecture"
updated: 2026-10-29
---
# Testing Protocol

## OVERVIEW
Repository verification strategy combining structural ontology validation, graph generation checks, dry-run agent distribution testing, and offline CLI wrapper assertion suites.

## COMMANDS
| Type | Command | Description |
|------|---------|-------------|
| Unit | `powershell -File skills/ask-antigravity/scripts/Test-Invoke-Antigravity.ps1` | Runs offline contract tests for the Antigravity delegation wrapper |
| Integration | `python skills/project-memory/scripts/generate_docs_graph.py docs` | Generates and verifies integrity of the documentation relation graph |
| E2E | `python scripts/sync_skills.py --dry-run` | Validates skill mirroring plans across all 4 coding agent targets |
| E2E | `python scripts/test_triad_slots_e2e.py` | Validates Triad Git worktree slot lifecycle, isolation, and recovery end-to-end |
| Coverage | `python skills/project-memory/scripts/validate_ontology.py docs` | Validates document frontmatter, node references, and structural schemas |

## MINIMUM COVERAGE
REQUIRED: Maintain the following minimum coverage levels:

| Layer | Coverage | Description |
|-------|----------|-------------|
| Documentation Graph | 100% | Zero unresolved node references or broken edges in docs/.graph.json |
| Skill Specifications | 100% | Valid frontmatter and self-contained structure for all 15 skills |
| CLI Delegation Wrappers | 100% | All offline argument parsing, mode switching, and error paths verified |
| Repository Synchronization | 100% | Clean dry-run execution across Antigravity, Codex, OpenCode, and Claude |

## MOCK MATRIX
| Dependency Type | Unit Tests | Integration Tests | NEVER Mock |
|---|---|---|---|
| CLI Executables (`agy`, `codex`, `opencode`) | In-memory function stub (`global:agy`) | Headless dry-run CLI invocation | Direct production execution in test suites |
| Filesystem Paths | Temporary test directories (`tempfile`) | Real workspace paths with validation | Arbitrary external directories |
| Documentation State | Isolated temporary Markdown fixtures | Real `docs/` repository tree | Uncommitted candidate files during validation |

## NEGATIVE ORACLES & ANTI-PATTERNS
| Smell / Anti-Pattern | WRONG Example | Why it fails | Correct Fix |
|---|---|---|---|
| Direct CLI invocation in unit test | `& agy -Prompt 'Test'` | Requires authentication, network, and live model tokens | Mock CLI via test function stub |
| Missing dry-run flag in sync test | `python scripts/sync_skills.py` | Mutates local agent skill directories unexpectedly | Pass `--dry-run` to test synchronization safely |
| Skipping graph regeneration | Manual edit of `docs/.graph.json` | Causes drift, indentation discrepancies, and stale edges | Rebuild via `generate_docs_graph.py` |

## PATTERNS & BEST PRACTICES
- REQUIRED: Run `python skills/project-memory/scripts/validate_ontology.py docs` after updating any documentation.
- REQUIRED: Test CLI delegation wrappers offline without network access or live tokens.
- PROHIBITED: Hardcoding target machine paths in verification scripts.
- PROHIBITED: Bypassing `--dry-run` when validating agent synchronization logic.

## FAILURE PROTOCOL (RED-GREEN-REFACTOR)
- REQUIRED: In RED phase, a test must fail strictly due to an unmet invariant or schema mismatch — never due to unhandled syntax errors or script crashes.
- PROHIBITED: Modifying test assertions or ignoring validation exit codes to force green verification status.

## TOOLING
- **Framework:** Python `unittest`, PowerShell native assertion scripts
- **Assertions:** Built-in PowerShell `Assert`, Python `self.assertEqual` / custom validators
- **Mocks/Stubs:** In-memory PowerShell function mock (`global:agy`), Python `tempfile.TemporaryDirectory`
- **Coverage:** Deterministic validation scripts (`validate_ontology.py`, `generate_docs_graph.py`)
- **CI Integration:** Local pre-commit verification and dry-run execution commands

## TROUBLESHOOTING
- **Flaky tests:** Verify environment PATH contains Python 3.12+ and PowerShell 5.1/7+.
- **Debug mode:** Run PowerShell scripts with `$VerbosePreference = 'Continue'` or inspect validation stdout.

<!-- DOCUMENT MAP: omitted — this baseline ADR has exactly 1 edge. The ## REFERENCES section below carries the relation. Add a DOCUMENT MAP only when it explains relationships beyond existing references. -->

## REFERENCES

- [**README.md**](../README.md): Main documentation index.
- [**ARCHITECTURE.md**](./ARCHITECTURE.md): System architecture and patterns.
