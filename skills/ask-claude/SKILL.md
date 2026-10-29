---
name: ask-claude
description: Delegate consultations, code reviews, and implementations to the local Claude CLI (claude) through Windows PowerShell with explicit model and effort defaults.
---

# Ask Claude

Delegate to the local `claude` CLI on behalf of the user. Include the objective, relevant paths, acceptance conditions, and authorized scope. Do not send secrets or delegate back to the requesting agent.

## Intent routing

| Intent | Mode | Invocation policy |
| --- | --- | --- |
| Consultation or analysis | `ReadOnly` | Planning mode with only `Read`, `Glob`, and `Grep` tools. |
| Code review | `Review` | Same restrictions; provide the diff or base and target paths in the prompt. |
| Authorized implementation | `WorkspaceWrite` | `acceptEdits` mode in the requested workspace; other permissions remain enforced. |

For isolated implementation, create a Git worktree first and pass its path as `-WorkingDirectory`. Preserve failed work for inspection. These modes are CLI permission policies, not OS sandboxes. ReadOnly and Review exclude shell tools; provide a diff in the prompt when needed.

## Model and effort

Default model: `sonnet-5.5`. Default reasoning effort: `high`. The helper passes both explicitly. Override with `-Model` and `-ReasoningEffort`; combined `-Model sonnet-5.5/extra-high` maps effort to `xhigh`. A separate effort overrides the suffix. Never silently substitute a rejected model.

## Windows PowerShell

Check `Get-Command claude` and `claude --help`. Use existing authentication; report missing login without copying credentials. Resolve `$skillRoot` to this skill's directory.

```powershell
& "$skillRoot\scripts\Invoke-Claude.ps1" `
  -Prompt 'Analyze src/auth.py and report edge cases.' `
  -Mode ReadOnly -WorkingDirectory 'C:\projects\app'

& "$skillRoot\scripts\Invoke-Claude.ps1" `
  -Prompt 'Review the supplied diff for correctness. Do not edit files.' `
  -Mode Review -OutputFile 'C:\projects\review.txt'

& "$skillRoot\scripts\Invoke-Claude.ps1" `
  -Prompt 'Apply the authorized fix and run relevant tests.' `
  -Mode WorkspaceWrite -WorkingDirectory 'C:\projects\app-worktree'
```

The helper pipes the prompt and closes stdin, uses noninteractive JSON output, checks exit status and error results, and cleans its temporary file in `finally`. Stderr remains visible. `-OutputFile` receives only a successful answer as UTF-8. Sessions are not persisted or resumed. No permission bypass flags are used.

Flags were checked against local `claude --help`. Live model availability and authentication still require runtime verification. Report returned findings, changed files, tests, and limitations; inspect changes before integration.
