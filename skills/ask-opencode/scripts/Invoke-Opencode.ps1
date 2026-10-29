<#
.SYNOPSIS
    Wrapper de alta performance e ciclo de vida estritamente controlado para o OpenCode CLI.

.DESCRIPTION
    Inicia o daemon 'opencode serve --port 4096' sob demanda em background,
    cria uma sessão isolada, executa o prompt com o modelo e variant (reasoning effort) desejados,
    extrai o texto limpo da resposta e garante a destruição imediata de todos os processos do OpenCode
    ao final da execução.

.PARAMETER Prompt
    Instrução textual para o OpenCode.

.PARAMETER Model
    Identificador do modelo (ex: 'glm-5.3-flash', 'gpt-6-luna', 'qwen3.8-flash', 'big-pickle').
    Suporta formato combinado 'modelo/variant' (ex: 'gpt-6-luna/xhigh' ou 'glm-5.3-flash/max').

.PARAMETER Variant
    Esforço de raciocínio (reasoning effort) ou variante:
    'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'thinking'.

.PARAMETER Agent
    Agente do OpenCode a ser utilizado (padrão: 'build'). Exemplos: 'build', 'explore', 'software-architect'.

.PARAMETER Port
    Porta do servidor OpenCode (padrão: 4096).

.PARAMETER AutoKill
    Garante que os processos do opencode sejam mortos ao final da resposta (padrão: $true).

.PARAMETER KillOnly
    Apenas encerra imediatamente qualquer processo residual do opencode no sistema.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Prompt,

    [Parameter(Position = 1)]
    [string]$Model = 'glm-5.3',

    [Parameter(Position = 2)]
    [string]$Variant,

    [Parameter()]
    [string]$Agent = 'build',

    [Parameter()]
    [int]$Port = 4096,

    [Parameter()]
    [bool]$AutoKill = $true,

    [Parameter()]
    [switch]$KillOnly
)

$ErrorActionPreference = 'Stop'

function Stop-OpenCodeProcesses {
    [CmdletBinding()]
    param()
    # Mata via Stop-Process e reforça com taskkill /F no Windows
    try {
        Get-Process -Name "*opencode*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    } catch {}
    try {
        & taskkill.exe /F /IM "opencode.exe" /T 2>$null | Out-Null
    } catch {}
}

# Se for apenas para matar os processos residuais
if ($KillOnly) {
    Stop-OpenCodeProcesses
    return "Todos os processos do OpenCode foram finalizados com sucesso."
}

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    throw "O parâmetro -Prompt é obrigatório quando -KillOnly não for especificado."
}

# Normalizar Model e Variant combinados (ex: gpt-6-luna/xhigh ou opencode-go/gpt-6-luna/xhigh)
if ($Model -match '^(.*?)/([^/]+)$' -and -not $Variant) {
    $firstPart = $Matches[1]
    $secondPart = $Matches[2]
    if ($secondPart.ToLower() -in @('none', 'minimal', 'minimo', 'mínimo', 'low', 'baixo', 'medium', 'medio', 'médio', 'high', 'alto', 'xhigh', 'extra-high', 'max', 'maximo', 'máximo', 'thinking')) {
        $Model = $firstPart
        $Variant = $secondPart
    }
}

if (-not $Variant) { $Variant = 'high' }

# Normalizar Variant (reasoning effort)
if ($Variant) {
    $cleanVariant = $Variant.ToLower().Trim()
    switch ($cleanVariant) {
        { $_ -in @('none', 'nenhum', 'zero', 'off') } { $Variant = 'none' }
        { $_ -in @('minimal', 'minimo', 'mínimo', 'min') } { $Variant = 'minimal' }
        { $_ -in @('low', 'baixo') } { $Variant = 'low' }
        { $_ -in @('medium', 'medio', 'médio', 'med') } { $Variant = 'medium' }
        { $_ -in @('high', 'alto') } { $Variant = 'high' }
        { $_ -in @('xhigh', 'extra-high', 'extra_high', 'extra-alto', 'extra_alto', 'extra') } { $Variant = 'xhigh' }
        { $_ -in @('max', 'maximo', 'máximo', 'maximum') } { $Variant = 'max' }
        { $_ -in @('thinking') } { $Variant = 'thinking' }
        default { $Variant = $cleanVariant }
    }
}

# Mapear providerID e modelID
$providerID = 'opencode-go'
$modelID = $Model

if ($Model -match '^([^/]+)/(.+)$') {
    $providerID = $Matches[1]
    $modelID = $Matches[2]
} else {
    $freeModels = @(
        'big-pickle', 'exo-free', 'fledge-alpha-free', 'ling-3.0-flash-fin-free',
        'ling-3.1-flash-free', 'longcat-2.5-preview-free', 'mimo-v2.6-flash-free',
        'muse-spark-1.3-contributor-free', 'nemotron-3.5-lightning-free',
        'nemotron-3-ultra-free', 'space-bunny-free'
    )
    if ($modelID -in $freeModels) {
        $providerID = 'opencode'
    } else {
        $providerID = 'opencode-go'
    }
}

$baseUrl = "http://127.0.0.1:$Port"

# Inicializar servidor headless se necessário
$serverRunning = $false
try {
    $null = Invoke-RestMethod -Uri "$baseUrl/session" -Method Get -TimeoutSec 1 -ErrorAction Stop
    $serverRunning = $true
} catch {
    $serverRunning = $false
}

if (-not $serverRunning) {
    $opencodeCmd = Get-Command opencode -ErrorAction SilentlyContinue
    if (-not $opencodeCmd) {
        throw "O comando 'opencode' não foi encontrado no PATH do sistema."
    }
    
    Start-Process -FilePath "opencode.cmd" -ArgumentList "serve --port $Port" -WindowStyle Hidden
    
    $retries = 15
    while ($retries -gt 0) {
        Start-Sleep -Milliseconds 400
        try {
            $null = Invoke-RestMethod -Uri "$baseUrl/session" -Method Get -TimeoutSec 1 -ErrorAction Stop
            $serverRunning = $true
            break
        } catch {
            $retries--
        }
    }
    if (-not $serverRunning) {
        throw "Não foi possível conectar ao servidor opencode serve na porta $Port."
    }
}

# Criar sessão efêmera
$session = Invoke-RestMethod -Uri "$baseUrl/session" -Method Post -ContentType "application/json" -Body '{}' -TimeoutSec 10
$sessionId = $session.id

try {
    $modelObj = @{
        modelID = $modelID
        providerID = $providerID
    }
    if ($Variant) {
        $modelObj['variant'] = $Variant
    }

    $bodyObj = @{
        agent = $Agent
        model = $modelObj
        parts = @(
            @{
                type = "text"
                text = $Prompt
            }
        )
    }

    $jsonBody = $bodyObj | ConvertTo-Json -Depth 5

    # Enviar mensagem e capturar a resposta
    $postResponse = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId/message" -Method Post -ContentType "application/json" -Body $jsonBody -TimeoutSec 600

    if ($postResponse -and $postResponse.parts) {
        $textParts = $postResponse.parts | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.text }
        if ($textParts) {
            return ($textParts -join "`n").Trim()
        }
    }

    # Polling resiliente caso o retorno venha assíncrono
    $pollAttempts = 20
    while ($pollAttempts -gt 0) {
        Start-Sleep -Milliseconds 800
        $messages = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId/message" -Method Get -TimeoutSec 10
        $lastAssistantMsg = $messages | Where-Object { $_.role -eq 'assistant' } | Select-Object -Last 1
        if ($lastAssistantMsg -and $lastAssistantMsg.parts) {
            $textParts = $lastAssistantMsg.parts | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.text }
            if ($textParts) {
                return ($textParts -join "`n").Trim()
            }
        }
        $pollAttempts--
    }

    throw "Nenhuma resposta de texto retornada pelo OpenCode dentro do limite de tempo."
}
finally {
    # Limpar a sessão temporária
    try {
        $null = Invoke-RestMethod -Uri "$baseUrl/session/$sessionId" -Method Delete -TimeoutSec 3 -ErrorAction SilentlyContinue
    } catch {}

    # MATAR O PROCESSO DO OPENCODE GARANTIDAMENTE
    if ($AutoKill) {
        Stop-OpenCodeProcesses
    }
}
