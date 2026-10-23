# SECURITY

## TRUST AND STORAGE

REQUIRED: Keep credentials, API keys, OAuth tokens, app sessions, history,
databases, logs, generated caches and private binary backups outside Git.
REQUIRED: Authenticate on each new machine through the official agent flow.
REQUIRED: Review source and installer changes before execution; a checksum proves
the recorded artifact identity, not publisher trust or harmless behavior.

The initial inspection read selected configuration and manifests, not credential
stores. Exports include environment-variable names where useful, never values.
Personal asset home prefixes use `__HOME__`. Source hashes preserve audit evidence;
templates intentionally differ only by prefix substitution, BOM removal and LF.

`verify_repository.py` checks common credential patterns and forbidden filenames.
This is a limited pattern scanner, not proof that arbitrary personal data is absent.
Review all captured skills and plugin identifiers before publishing this repository.
The repository has no remote and has not been uploaded.

## EXECUTION

Git sources use pinned commits. Official binaries use SHA-256/SHA-512 checks.
npm uses a transitive integrity lock; package installation code is third-party
code and executes in the private prefix under the current user. No elevation is
requested. Python bootstrap downloads a pinned official embeddable distribution.
The installer does not pipe mutable remote scripts into a shell.

Archive extraction rejects traversal, symlinks and devices; known Node npm/npx
symlinks are skipped because npm is invoked through `npm-cli.js` directly.
Managed configuration paths reject symlinks and Windows junctions. Concurrent
writes are excluded by a local operation lock. Backups precede configuration writes.

Hooks and MCP servers execute as the user. Review Codex trust in `/hooks`.
Do not import trust hashes or permission grants from the original workstation.
The captured Codex/browser runtime was app-owned and intentionally excluded.

## DATA FLOWS

Caveman skill text is installed without its cloud proxy, login, optimizer service,
or automatic model routing. `DO_NOT_TRACK=1` is set in the launch environment.
Jev skills reference external services and require provenance/credential review;
they remain disabled. Open Graph is a separate local MCP application and remains
pending a verified dependency/setup workflow. No cloud account is provisioned.

Protect backups with account ACLs and disk encryption. Unix transaction directories
are created with mode 0700; Windows relies on inherited account ACLs. Rollback
restores file bytes, not prior ownership, ACLs or timestamps. Do not grant other
users write access to the state directory.
