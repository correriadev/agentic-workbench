---
doc_type: adr
domain: testing
stack: [python, unittest]
node_id: "adr:tests"
tags: [testing, recovery, security]
edges: []
updated: 2026-10-23
---
# Testing Protocol

## OVERVIEW

Use Python standard-library unittest with temporary homes. Separate filesystem
safety proof from real downloaded CLI validation and authenticated agent use.

## COMMANDS

| Type | Command | Evidence |
|---|---|---|
| Offline | `python -m unittest discover -s tests -v` | Conflict, recovery, integrity and path boundaries |
| Repository | `python scripts/verify_repository.py` | Source pins, npm lock, asset hashes and credential patterns |
| Runtime | `python scripts/environment.py doctor` | Installed executable versions and deployed-file hashes |
| MCP | `python scripts/check_mcp.py ABSOLUTE_EXECUTABLE_PATH` | Initialize and tools/list only |

## MINIMUM COVERAGE

No percentage coverage threshold is configured. CI gates on all offline tests
and repository validation passing. Native runtime evidence exists only for
Windows x64; CI configuration alone is not evidence that remote jobs ran.

## PATTERNS & BEST PRACTICES

REQUIRED: Run filesystem changes inside disposable homes.
REQUIRED: Test failed writes, corrupt backups, edited files, traversal and checksums.
REQUIRED: Mock network only at the download boundary.
PROHIBITED: Treat a version probe as proof of model access or plugin execution.

## TOOLING

- **Framework:** Python 3.12+ unittest.
- **Assertions:** standard unittest assertions.
- **Mocks:** unittest.mock for download failures and simulated write failures.
- **Coverage:** no percentage collection configured.
- **CI:** GitHub Actions matrix for Windows, Linux and macOS offline checks.

## TROUBLESHOOTING

Use `-v` for the failing test name. Retain failed install transaction IDs and
inspect the journal before recovery. See runtime results in the validation log.

## REFERENCES

- [Validation](../research/VALIDATION.md): checks actually executed.
- [Recovery](../RECOVERY.md): safe rollback and update procedures.
