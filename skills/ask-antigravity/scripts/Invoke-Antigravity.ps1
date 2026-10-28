[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Prompt,
    [ValidateSet('ReadOnly', 'Review', 'WorkspaceWrite')]
    [string]$Mode = 'ReadOnly',
    [string]$WorkingDirectory = (Get-Location).Path,
    [string]$Model,
    [string]$ReasoningEffort,
    [string]$OutputSchema,
    [string]$OutputFile,
    [ValidateRange(1, 86400)]
    [int]$TimeoutSeconds = 600
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Prompt)) { throw 'O prompt não pode estar vazio.' }
$agyCommand = Get-Command agy -ErrorAction Stop
if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
    throw "Diretório inexistente: $WorkingDirectory"
}

if ($Model -match '^([^/]+)/([^/]+)$') {
    $Model = $Matches[1]
    if (-not $ReasoningEffort) { $ReasoningEffort = $Matches[2] }
}
if ($ReasoningEffort) {
    $aliases = @{
        'baixo' = 'low'; 'medio' = 'medium'; 'médio' = 'medium'
        'alto' = 'high'; 'extra-high' = 'xhigh'; 'extra-alto' = 'xhigh'
        'maximo' = 'max'; 'máximo' = 'max'
    }
    $ReasoningEffort = $ReasoningEffort.Trim().ToLowerInvariant()
    if ($aliases.ContainsKey($ReasoningEffort)) { $ReasoningEffort = $aliases[$ReasoningEffort] }
    if ($ReasoningEffort -notin @('low', 'medium', 'high', 'xhigh', 'max')) {
        throw "Esforço não suportado: $ReasoningEffort"
    }
}

$cliArgs = @('--output-format', 'json', '--sandbox', '--disable-slash-commands', '--print-timeout', "${TimeoutSeconds}s")
if ($Mode -eq 'WorkspaceWrite') {
    $cliArgs += @('--mode', 'accept-edits')
} else {
    $cliArgs += @('--mode', 'plan')
    $Prompt = "Analise sem modificar arquivos nem executar ações de escrita. Não delegue novamente ao agente solicitante.`n`n$Prompt"
}
if ($Model) { $cliArgs += @('--model', $Model) }
if ($ReasoningEffort) { $cliArgs += @('--effort', $ReasoningEffort) }
if ($OutputSchema) {
    $schemaPath = (Resolve-Path -LiteralPath $OutputSchema).Path
    Get-Content -LiteralPath $schemaPath -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
    $cliArgs += @('--json-schema', $schemaPath)
}
$cliArgs += @('--print', $Prompt)

Push-Location -LiteralPath $WorkingDirectory
try {
    # Preserve stderr while allowing native failures to reach the explicit exit-code check.
    $ErrorActionPreference = 'Continue'
    $raw = $null | & $agyCommand @cliArgs
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($exitCode -ne 0) { throw "Antigravity terminou com código $exitCode. Consulte stderr para detalhes." }
    $result = ($raw -join "`n") | ConvertFrom-Json
    if ($result.status -ne 'SUCCESS') {
        throw "Antigravity não concluiu a tarefa ($($result.status)): $($result.error)"
    }
    if ($OutputSchema) {
        if ($null -eq $result.structured_output) { throw 'Antigravity não retornou structured_output.' }
        $answer = ConvertTo-Json -InputObject $result.structured_output -Depth 100
    } else {
        $answer = [string]$result.response
        if ([string]::IsNullOrWhiteSpace($answer)) { throw 'Antigravity retornou uma resposta vazia.' }
    }
} finally {
    Pop-Location
}
if ($OutputFile) {
    [System.IO.File]::WriteAllText($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputFile), $answer, [System.Text.UTF8Encoding]::new($false))
}
$answer
