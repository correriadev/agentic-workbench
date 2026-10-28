# Offline contract checks: no authentication, network requests, or model usage.
$ErrorActionPreference = 'Stop'
$wrapper = Join-Path $PSScriptRoot 'Invoke-Antigravity.ps1'
$originalLocation = (Get-Location).Path
$global:askAntigravityTestExit = 0
$global:askAntigravityTestResult = '{"status":"SUCCESS","response":"análise válida"}'
function global:agy {
    $global:askAntigravityTestArgs = @($args)
    $global:LASTEXITCODE = $global:askAntigravityTestExit
    $global:askAntigravityTestResult
}
function Assert($Condition, $Message) {
    if (-not $Condition) { throw $Message }
}
function Assert-Fails([scriptblock]$Action) {
    $failed = $false
    try { & $Action | Out-Null } catch { $failed = $true }
    Assert $failed 'Era esperada uma falha.'
}
$schema = [System.IO.Path]::GetTempFileName()
$output = [System.IO.Path]::GetTempFileName()
try {
    $answer = & $wrapper -Prompt 'Revise "ação".' -Mode Review -Model 'example/extra-high'
    Assert ($answer -eq 'análise válida') 'Resposta alterada.'
    Assert ($global:askAntigravityTestArgs -contains 'plan') 'Revisão precisa usar plan.'
    Assert ($global:askAntigravityTestArgs -contains 'xhigh') 'Alias de esforço incorreto.'
    Assert ($global:askAntigravityTestArgs -contains '--sandbox') 'Sandbox ausente.'
    Assert ($global:askAntigravityTestArgs -notcontains '--dangerously-skip-permissions') 'Permissões ampliadas.'
    & $wrapper -Prompt 'Corrija.' -Mode WorkspaceWrite -Model 'example/high' -ReasoningEffort low | Out-Null
    Assert ($global:askAntigravityTestArgs -contains 'accept-edits') 'Modo de escrita incorreto.'
    Assert ($global:askAntigravityTestArgs -contains 'low') 'Esforço explícito deve prevalecer.'
    Set-Content -LiteralPath $schema -Value '{"type":"object"}' -Encoding UTF8
    $global:askAntigravityTestResult = '{"status":"SUCCESS","structured_output":{"ok":true}}'
    & $wrapper -Prompt 'Extraia.' -OutputSchema $schema -OutputFile $output | Out-Null
    Assert ((Get-Content -LiteralPath $output -Raw | ConvertFrom-Json).ok) 'Saída estruturada inválida.'
    $global:askAntigravityTestResult = '{"status":"WAITING","error":"permission denied"}'
    Assert-Fails { & $wrapper -Prompt 'Analise.' }
    $global:askAntigravityTestExit = 1
    Assert-Fails { & $wrapper -Prompt 'Analise.' }
    $global:askAntigravityTestExit = 0
    $global:askAntigravityTestResult = 'not json'
    Assert-Fails { & $wrapper -Prompt 'Analise.' }
    Assert-Fails { & $wrapper -Prompt 'Analise.' -ReasoningEffort none }
    Assert ((Get-Location).Path -eq $originalLocation) 'Diretório não restaurado.'
    'Offline checks passed.'
} finally {
    Remove-Item -LiteralPath $schema, $output -Force
    Remove-Item Function:\agy
    Remove-Variable -Scope Global -Name askAntigravityTestArgs, askAntigravityTestExit, askAntigravityTestResult
}
