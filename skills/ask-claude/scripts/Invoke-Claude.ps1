<#
.SYNOPSIS
    Invoke Claude noninteractively with explicit permissions, model, and effort.
.DESCRIPTION
    Pipes the prompt to close stdin, validates JSON results, and removes temporary output.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Prompt,
    [ValidateSet('ReadOnly', 'Review', 'WorkspaceWrite')]
    [string]$Mode = 'ReadOnly',
    [string]$Model = 'sonnet-5.5',
    [string]$ReasoningEffort,
    [string]$WorkingDirectory = (Get-Location).Path,
    [string]$OutputFile
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Prompt)) { throw 'Prompt must not be blank.' }
$claudeCommand = Get-Command claude -ErrorAction Stop
if ($Model -match '^([^/]+)/([^/]+)$') {
    $Model = $Matches[1]
    if (-not $ReasoningEffort) { $ReasoningEffort = $Matches[2] }
}
if (-not $ReasoningEffort) { $ReasoningEffort = 'high' }
if ($ReasoningEffort -eq 'extra-high') { $ReasoningEffort = 'xhigh' }
if ($ReasoningEffort -notin @('low', 'medium', 'high', 'xhigh', 'max')) {
    throw "Unsupported reasoning effort: $ReasoningEffort"
}
if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
    throw "Directory does not exist: $WorkingDirectory"
}
if ($OutputFile) {
    $OutputFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputFile)
}
$cliArgs = @('--print', '--output-format', 'json', '--no-session-persistence',
    '--model', $Model, '--effort', $ReasoningEffort)
if ($Mode -eq 'WorkspaceWrite') {
    $cliArgs += @('--permission-mode', 'acceptEdits')
} else {
    $cliArgs += @('--permission-mode', 'plan', '--tools', 'Read,Glob,Grep',
        '--allowedTools', 'Read,Glob,Grep', '--strict-mcp-config',
        '--disable-slash-commands')
    $Prompt = "Analyze without editing files or delegating tasks. Review mode: $Mode.`n`n$Prompt"
}
$tempOutput = [System.IO.Path]::GetTempFileName()
try {
    Push-Location -LiteralPath $WorkingDirectory
    try {
        $ErrorActionPreference = 'Continue'
        $Prompt | & $claudeCommand @cliArgs | Set-Content -LiteralPath $tempOutput -Encoding UTF8
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = 'Stop'
        Pop-Location
    }
    if ($exitCode -ne 0) { throw "Claude exited with code $exitCode. See stderr for details." }
    $result = Get-Content -LiteralPath $tempOutput -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($result.is_error -or $result.type -ne 'result' -or $result.subtype -ne 'success') {
        throw "Claude did not complete successfully: $($result | ConvertTo-Json -Depth 10 -Compress)"
    }
    $answer = [string]$result.result
    if ([string]::IsNullOrWhiteSpace($answer)) { throw 'Claude returned an empty response.' }
    if ($OutputFile) {
        [System.IO.File]::WriteAllText($OutputFile, $answer, [System.Text.UTF8Encoding]::new($false))
    }
    $answer
} finally {
    Remove-Item -LiteralPath $tempOutput -Force -ErrorAction SilentlyContinue
}
