$ErrorActionPreference = 'Stop'
$wrapper = Join-Path $PSScriptRoot 'Invoke-Claude.ps1'
$global:claudeTestArgs = @()
$global:claudeTestFailure = $false
$global:claudeTestExitCode = 0
function global:claude {
    $global:claudeTestArgs = $args
    $received = @($input) -join "`n"
    if (-not $received) { throw 'Missing stdin prompt.' }
    $global:LASTEXITCODE = $global:claudeTestExitCode
    if ($global:claudeTestFailure) {
        '{"type":"result","subtype":"error_during_execution","is_error":true}'
    } else {
        '{"type":"result","subtype":"success","is_error":false,"result":"checked"}'
    }
}
try {
    foreach ($mode in @('ReadOnly', 'Review', 'WorkspaceWrite')) {
        $answer = & $wrapper -Prompt 'Offline test' -Mode $mode
        if ($answer -ne 'checked') { throw 'Unexpected answer.' }
        $arguments = $global:claudeTestArgs -join ' '
        if ($arguments -notmatch '--model sonnet-5.5 --effort high') { throw 'Defaults missing.' }
        $expected = if ($mode -eq 'WorkspaceWrite') { 'acceptEdits' } else { 'plan' }
        if ($arguments -notmatch "--permission-mode $expected") { throw 'Wrong permissions.' }
    }
    & $wrapper -Prompt 'Override' -Model 'custom/extra-high' | Out-Null
    if (($global:claudeTestArgs -join ' ') -notmatch '--model custom --effort xhigh') {
        throw 'Combined override failed.'
    }
    & $wrapper -Prompt 'Override' -Model 'custom/extra-high' -ReasoningEffort low | Out-Null
    if (($global:claudeTestArgs -join ' ') -notmatch '--effort low') { throw 'Explicit effort lost.' }
    $global:claudeTestFailure = $true
    $failed = $false
    try { & $wrapper -Prompt 'Failure' | Out-Null } catch { $failed = $true }
    if (-not $failed) { throw 'Error result was accepted.' }
    $global:claudeTestFailure = $false
    $global:claudeTestExitCode = 3
    $failed = $false
    try { & $wrapper -Prompt 'Exit failure' | Out-Null } catch { $failed = $true }
    if (-not $failed) { throw 'Nonzero exit code was accepted.' }
    'Claude wrapper offline checks passed.'
} finally {
    Remove-Item Function:\claude
    Remove-Variable claudeTestArgs, claudeTestFailure, claudeTestExitCode -Scope Global
}
