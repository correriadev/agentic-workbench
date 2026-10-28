<#
.SYNOPSIS
    Script de simplificacao estrutural e remocao de pastas/arquivos legados.
#>
[CmdletBinding()]
param()

$rootDir = Split-Path -Parent $PSScriptRoot
Push-Location $rootDir

Write-Host "Iniciando simplificacao estrutural em: $rootDir" -ForegroundColor Cyan

# 1. Mover skills de skills/authored/* para skills/*
$authoredDir = Join-Path $rootDir "skills/authored"
if (Test-Path $authoredDir) {
    $skillsToRemove = @(
        "autonomous-orchestrator",
        "memory-context",
        "horizon-deliberator",
        "integrar-temenos",
        "level-graduator"
    )
    foreach ($s in $skillsToRemove) {
        $p = "skills/authored/$s"
        if (Test-Path $p) {
            git rm -rf $p 2>$null
            Remove-Item -Path $p -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Get-ChildItem -Path $authoredDir -Directory | ForEach-Object {
        $dest = Join-Path $rootDir "skills/$($_.Name)"
        if (-not (Test-Path $dest)) {
            Write-Host "Movendo skill para raiz de skills/: $($_.Name)" -ForegroundColor Yellow
            git mv "skills/authored/$($_.Name)" "skills/$($_.Name)" 2>$null
            if (-not (Test-Path $dest)) {
                Move-Item -Path $_.FullName -Destination $dest -Force
            }
        }
    }
    Remove-Item -Path $authoredDir -Recurse -Force -ErrorAction SilentlyContinue
}

# 2. Remover pastas e arquivos legados/desnecessarios
$pathsToRemove = @(
    "skills/autonomous-orchestrator",
    "skills/memory-context",
    "skills/horizon-deliberator",
    "skills/integrar-temenos",
    "skills/level-graduator",
    "skills/curated",
    ".work",
    "integrations",
    "mcp",
    "profiles",
    "tests",
    "tools",
    "docs/research",
    "docs/specs",
    "docs/ARCHITECTURE.md",
    "docs/CUSTOMIZATION.md",
    "docs/INSTALL.md",
    "docs/INVENTORY.md",
    "docs/RECOVERY.md",
    "docs/SECURITY.md",
    "environment.yaml",
    "environment.lock.yaml",
    "scripts/acceptance.py",
    "scripts/bootstrap.ps1",
    "scripts/bootstrap.sh",
    "scripts/check_mcp.py",
    "scripts/environment.py",
    "scripts/verify_repository.py",
    "scripts/__pycache__"
)

foreach ($relPath in $pathsToRemove) {
    if (Test-Path $relPath) {
        Write-Host "Removendo: $relPath" -ForegroundColor Yellow
        git rm -rf $relPath 2>$null
        if (Test-Path $relPath) {
            Remove-Item -Path $relPath -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Removido: $relPath" -ForegroundColor Green
    }
}

Pop-Location
Write-Host "Simplificacao concluida com sucesso." -ForegroundColor Cyan
