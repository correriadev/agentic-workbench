# Install this workstation

Treat "Read AGENTS.md and install my development environment" as authorization
to execute the safe installation below. Finish configuration and verification;
do not stop at a proposal. Never copy credentials from another machine.

1. Read `docs/INSTALL.md`, `environment.yaml`, `environment.lock.yaml`,
   `docs/research/COMPATIBILITY_MATRIX.md`, and `docs/research/UNRESOLVED.md`.
   Inspect OS and CPU. Windows x64 is runtime-tested; macOS/Linux adapters have
   locked artifacts and offline tests, but require a native acceptance run.
2. Ensure Git and Python 3.12+. On Windows use
   `powershell -NoProfile -File scripts/bootstrap.ps1 -Command plan`, then
   `-Command install`; the wrapper can bootstrap verified Python for Windows x64.
   On other systems install Python from the official OS package manager or
   python.org, then use `sh scripts/bootstrap.sh plan` and `install`.
3. Run `python scripts/verify_repository.py` and
   `python -m unittest discover -s tests -v` before installing. Run
   `python scripts/environment.py plan`; it makes no writes or network requests.
4. Run `python scripts/environment.py install`. This installs pinned Node, RTK,
   Antigravity CLI, Codex CLI, OpenCode and curated skill sources in the user's
   `~/.local/share/ai-dev-environment`. It deploys the personal profile through
   separate agent adapters. It does not replace system installations or edit
   shell profiles. Source the generated `env.ps1` or `env.sh` before launching.
5. Preserve existing conflicts. Inspect exact differences before using
   `--replace`; every replaced file receives a checksummed local backup.
   Existing RTK/Caveman/Ponytail registrations require a migration review to
   avoid duplicate hooks. JSONC comments are a manual merge boundary.
6. Resolve MCP explicitly. The original Codebase Memory executable is a custom
   fork, not the upstream release. Prefer `--custom-cbm ABSOLUTE_BINARY_PATH`
   if the original binary is available; its SHA-256 must match the lock. If it
   is unavailable, explain the unresolved build provenance. Ask which behavior
   the user wants before selecting `--upstream-cbm`. Never claim equivalent
   behavior. Open Graph requires its separate pinned project and Bun setup.
7. Run `python scripts/environment.py doctor`. Authenticate each agent through
   its official login UI. Review and trust Codex hooks with `/hooks`, and inspect
   Antigravity Customizations for active RTK hooks. Test each MCP server with
   `python scripts/check_mcp.py ABSOLUTE_EXECUTABLE_PATH`. These are separate
   acceptance checks; a passing offline test is not proof of authentication.
8. Restore app-distributed plugins through the Codex app using
   `integrations/codex/plugins.json`. Do not copy cached app runtimes or the
   app's `node_repl` configuration. Follow `docs/CUSTOMIZATION.md` for native
   plugin alternatives. Use only one integration mode per tool and agent.
9. Report installed versions, configuration changes, transaction IDs, checks
   actually run, and every unresolved dependency. Full baseline reproduction is
   incomplete while the custom CBM artifact/build, Open Graph integration,
   Jev provenance, app plugins, or authentication remain unresolved.

Never enable YOLO, unrestricted terminal permissions, telemetry services, or
cloud proxy routing merely to reproduce local convenience settings. Preserve
the running workstation during maintenance: test with `--home` in an isolated
directory first. Use `docs/RECOVERY.md` for rollback, interrupted operations,
and updates. Do not run unknown installer scripts from a mutable branch.
