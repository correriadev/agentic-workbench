<#
.SYNOPSIS
    Wrapper robusto para invocar o codex-cli no Windows/PowerShell de forma transparente e não-interativa.

.DESCRIPTION
    Encapsula pipes de entrada, controle de Git repository check, arquivos temporários (-o),
    modos de sandbox (read-only, workspace-write, worktree), seleção de modelo e esforço de raciocínio.

.PARAMETER Prompt
    Instrução textual para o Codex (obrigatório para modos de execução).

.PARAMETER Mode
    Modo de operação:
      - 'ReadOnly' (padrão): Leitura estrita, seguro para consultas, explicações e auditorias.
      - 'WorktreeWrite': Executa implementação em Git worktree temporário isolado.
      - 'WorkspaceWrite': Executa modificação direta na árvore de trabalho atual com aprovação automática.
      - 'Review': Roda 'codex review' contra alterações não comitadas ou base.

.PARAMETER Model
    Modelo específico a ser utilizado (ex: 'gpt-6.1-sol', 'gpt-6-luna', 'o3').
    Suporta formato combinado com esforço: 'gpt-6-luna/extra-high' ou 'gpt-6-luna/xhigh'.

.PARAMETER ReasoningEffort
    Nível de esforço de raciocínio: 'none', 'minimal', 'low', 'medium', 'high', 'xhigh' (ou 'extra-high'), 'max'.

.PARAMETER OutputSchema
    Caminho para arquivo JSON Schema para forçar saída estruturada determinística.

.PARAMETER ReviewTarget
    Alvo do comando review (padrão: '--uncommitted').

.PARAMETER Ephemeral
    Não persiste sessão de chat/histórico do Codex (padrão: $true).

.PARAMETER OutputFile
    Caminho de saída customizado. Se omitido, usa arquivo temporário e retorna o conteúdo.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Prompt,

    [Parameter(Position = 1)]
    [ValidateSet('ReadOnly', 'WorktreeWrite', 'WorkspaceWrite', 'Review')]
    [string]$Mode = 'ReadOnly',

    [Parameter()]
    [string]$Model,

    [Parameter()]
    [string]$ReasoningEffort,

    [Parameter()]
    [string]$OutputSchema,

    [Parameter()]
    [string]$ReviewTarget = '--uncommitted',

    [Parameter()]
    [switch]$Ephemeral = $true,

    [Parameter()]
    [string]$OutputFile
)

$ErrorActionPreference = 'Stop'

# Localizar binário do Codex
$codexCmd = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codexCmd) {
    throw "O executável 'codex' não foi encontrado no PATH do sistema."
}

# Suporte à notação combinada 'modelo/esforço' (ex: gpt-6-luna/extra-high)
if ($Model -match '^([^/]+)/([^/]+)$') {
    $Model = $Matches[1]
    if (-not $ReasoningEffort) {
        $ReasoningEffort = $Matches[2]
    }
}

# Normalizar reasoning effort (aliases em inglês e português para os enums nativos da OpenAI)
if ($ReasoningEffort) {
    $cleanEffort = $ReasoningEffort.ToLower().Trim()
    switch ($cleanEffort) {
        { $_ -in @('none', 'nenhum', 'zero', 'off') } { $ReasoningEffort = 'none' }
        { $_ -in @('minimal', 'minimo', 'mínimo', 'min') } { $ReasoningEffort = 'minimal' }
        { $_ -in @('low', 'baixo') } { $ReasoningEffort = 'low' }
        { $_ -in @('medium', 'medio', 'médio', 'med') } { $ReasoningEffort = 'medium' }
        { $_ -in @('high', 'alto') } { $ReasoningEffort = 'high' }
        { $_ -in @('xhigh', 'extra-high', 'extra_high', 'extra-alto', 'extra_alto', 'extra') } { $ReasoningEffort = 'xhigh' }
        { $_ -in @('max', 'maximo', 'máximo', 'maximum') } { $ReasoningEffort = 'max' }
        default { $ReasoningEffort = $cleanEffort }
    }
}

# Verificar se estamos dentro de um repositório git
$isGitRepo = $false
try {
    $gitStatus = & git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitStatus -eq 'true') {
        $isGitRepo = $true
    }
} catch {
    $isGitRepo = $false
}

# Gerenciar arquivo temporário de saída
$tempFileCreated = $false
if (-not $OutputFile) {
    $OutputFile = [System.IO.Path]::GetTempFileName()
    $tempFileCreated = $true
}

try {
    if ($Mode -eq 'Review') {
        if (-not $isGitRepo) {
            throw "O modo 'Review' exige que o diretório atual seja um repositório Git válido."
        }
        $argsList = @('review')
        if ($ReviewTarget) {
            $argsList += $ReviewTarget
        }
        
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $output = $null | & $codexCmd.Source @argsList 2>&1
            return ($output -join "`n")
        } finally {
            $ErrorActionPreference = $prevEAP
        }
    }

    if ([string]::IsNullOrWhiteSpace($Prompt)) {
        throw "O parâmetro -Prompt é obrigatório para o modo '$Mode'."
    }

    $argsList = @('exec')

    switch ($Mode) {
        'ReadOnly' {
            $argsList += @('--sandbox', 'read-only')
        }
        'WorktreeWrite' {
            if (-not $isGitRepo) {
                throw "O modo 'WorktreeWrite' exige que o diretório atual seja um repositório Git válido."
            }
            $argsList += @('--worktree', '--approve-for-me')
        }
        'WorkspaceWrite' {
            $argsList += @('--approve-for-me')
        }
    }

    # Se não for um repositório git e não for worktree, adiciona flag para ignorar checagem
    if (-not $isGitRepo -and $Mode -ne 'WorktreeWrite') {
        $argsList += '--skip-git-repo-check'
    }

    if ($Ephemeral) {
        $argsList += '--ephemeral'
    }

    # Configuração de Modelo e Raciocínio
    if ($Model) {
        $argsList += @('-c', "model=`"$Model`"")
    }

    if ($ReasoningEffort) {
        $argsList += @('-c', "model_reasoning_effort=`"$ReasoningEffort`"")
    }

    if ($OutputSchema -and (Test-Path $OutputSchema)) {
        $argsList += @('--output-schema', (Resolve-Path $OutputSchema).Path)
    }

    $argsList += @('-o', $OutputFile)
    $argsList += '-' # Instruções passadas via stdin para evitar truncamento e hangs

    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $Prompt | & $codexCmd.Source @argsList | Out-Null
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    if (Test-Path $OutputFile) {
        $content = Get-Content -Path $OutputFile -Raw -Encoding UTF8
        if ($content) {
            return $content.Trim()
        } else {
            return ""
        }
    } else {
        throw "Codex não produziu o arquivo de saída esperado: $OutputFile"
    }
}
finally {
    if ($tempFileCreated -and (Test-Path $OutputFile)) {
        Remove-Item -Path $OutputFile -Force -ErrorAction SilentlyContinue
    }
}
