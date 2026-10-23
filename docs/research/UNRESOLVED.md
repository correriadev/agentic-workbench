# UNRESOLVED

## FULL BASELINE REPRODUCTION IS INCOMPLETE

The core installer is implemented and runtime-tested on Windows x64. The items
below require additional evidence or a user choice; none is silently installed
under an assumed identity.

| Item | Evidence | Required resolution |
|---|---|---|
| Custom Codebase Memory | version `mgh-8dd9f4ec-codex-20261021-relaxed`; source candidate `correriadev/codebase-memory-multigraph-mcp` commit `8dd9f4ec7057e642d9c66d0c8d3619f2700e62a5`; exact binary hash locked | Obtain a private matching artifact, or prove the compiler/build flags and source state. Upstream 0.12.1 is an explicit alternative, not an equivalent replacement. |
| Fresh-home CBM startup | Both inventoried custom binary and separately downloaded upstream binary exited before MCP initialize in the isolated temporary home. Custom stderr: `could not load saved runtime settings`. | Diagnose upstream runtime-settings initialization without copying personal graph databases; repeat protocol checks. |
| Open Graph | local repo `correriadev/open-graph-mcp` commit `5d06ef5a9e7b5100a9cbbff783eb3983ce1ddc41`; installed Antigravity wrapper uses Bun and project cwd | Reconstruct the pinned project with Bun 1.3.14 and its frozen bun.lock; verify wrapper, plugins and required personal data separately. Automatic install is not implemented. |
| Jev skill family | locally installed instructions cite several different upstreams and services; author/source lock unavailable | Match each snapshot to its actual upstream and revision. Snapshots are preserved but disabled; no guessed package is installed. |
| Personal ownership | files exist in agent homes and some related repos; no per-file authorship ledger | Review provenance before public licensing. `skills/authored` means retained local assets, not an authorship assertion. |
| App integrations | Codex distributed browser, desktop, document and runtime plugins are account/app managed | Install the official Codex app and reconnect plugins. Cached runtime paths and credentials are intentionally excluded. |
| Postman plugin | installed 1.1.0; configured marketplace `postmanlabs/postman-plugin` | Reinstall through native marketplace, authenticate, verify current permissions/revision. Do not copy cached server runtime. |
| Custom OpenCode CBM plugin | `cbm-augment.ts` snapshot retained in integrations/opencode/quarantine; upstream mapping uncertain | Match to custom fork version and validate hooks before enabling. |
| Native hook execution | file layouts and RTK plugin validation checked | Trust Codex hooks, confirm per-agent RTK rewrite behavior in a real trusted session. |
| Antigravity GUI | installed product 2.25.0.0 identified; CLI 1.4.6 separately verified | Confirm App vs IDE lineage, installer version, GUI plugin activation and restart behavior. |
| macOS/Linux | exact artifacts resolved; offline cross-platform path tests and CI matrix authored | Execute real native installation, hook, plugin and MCP acceptance tests. |
| Windows arm64 | Node/Antigravity artifacts present; complete RTK stack not locked | Resolve compatible RTK and test full toolchain. |
| Authentication and models | no credentials exported or test login performed | Authenticate agents/providers; confirm retained model IDs and subscriptions. |

The supplied mission attachment ends mid-sentence at architecture principle 4:
“Agent adapters: keep platform”. No unseen continuation or requirements were inferred.

## CAPTURE BOUNDARY

Inspected selected agent-home settings, installed CLI help/version output, relevant
skill trees, agent definitions, plugin manifests, known local source remotes and
revisions. This was not a search of arbitrary personal files or every project on
disk. Project trust paths and permission grants are not exported. Existing user
configuration remains unchanged by repository creation and isolated tests.
