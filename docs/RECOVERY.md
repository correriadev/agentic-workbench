# RECOVERY

## CONFIGURATION ROLLBACK

Every nontrivial apply prints a transaction ID. Backups and a journal live under
`~/.local/share/ai-dev-environment/transactions/ID`. Journals record before/after
hashes and whether the file originally existed. Backups can contain private
configuration; keep this directory out of Git and protect it with OS permissions.

CORRECT:

```sh
python scripts/environment.py rollback --transaction ID
```

Use the real ID printed by apply. Roll back newest transactions first. A second
rollback is a no-op. A post-install edit or corrupt backup stops the entire
preflight before files are restored. Copy the edited file to a private location,
review the journal and reconcile it; never bypass this check blindly.

Rollback restores file content and removes files created by that transaction.
It leaves directories, dependency downloads, source checkouts, and agent-owned
runtime state in place. Filesystem metadata/ACLs are not reproduced byte-for-byte.

## INTERRUPTED OPERATIONS

The installer rolls back configuration writes on handled failures. After process
termination or power loss, inspect journals with status `applying` and roll them
back before retrying. If `operation.lock` remains, verify its PID is no longer
running before deleting that one lock file. Never remove a live process's lock.

Incomplete binary directories and dirty source trees are refused. Inspect and
move the affected version directory to a private quarantine location within the
same state directory, then retry fetch. Do not delete arbitrary computed paths.
No mutable-source update or automatic cleanup runs during recovery.

## UPDATES

1. Create a Git branch and retain the last known-good repository commit.
2. Read current official release notes and compare the compatibility matrix.
3. Update exact version/commit, release URL and published checksum together.
4. For npm, change `integrations/node/package.json`, regenerate its lock with
   the pinned npm/Node toolchain, and reconcile root lock metadata.
5. Inspect retained assets and regenerate `profiles/assets.sha256.json` only
   after reviewing the exact diff; never use hash refresh to hide drift.
6. Run offline tests and an isolated `install`, doctor, native hook and MCP checks.
7. Apply the new version to the live home only after those checks pass.

To return to an earlier version, restore its Git commit, roll back newer
configuration transactions, then fetch/apply from that lock. Version-addressed
binary/source directories allow coexistence. npm tools use one prefix and may
need `fetch` to reinstall the older lock; configuration rollback alone does not
roll back that npm prefix. Upstream self-updaters can drift; doctor reports it.
