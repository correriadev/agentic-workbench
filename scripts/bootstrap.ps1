param(
    [ValidateSet('plan','fetch','install','apply','doctor','rollback')]
    [string]$Command = 'plan',
    [string]$TargetHome = $env:USERPROFILE
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    & $pythonCommand.Source -c 'import sys; raise SystemExit(sys.version_info < (3,12))'
    if ($LASTEXITCODE -eq 0) {
        & $pythonCommand.Source (Join-Path $PSScriptRoot 'environment.py') $Command --home $TargetHome
        exit $LASTEXITCODE
    }
}
if ($Command -eq 'plan') {
    Write-Output 'Python 3.12+ is missing. install/fetch will bootstrap checksum-verified Python 3.12.10 in this clone under .state/python.'
    exit 0
}
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Automatic Python bootstrap supports Windows x64 only; install Python 3.12+ for this architecture first.' }
$lock = Get-Content -Raw -LiteralPath (Join-Path $repo 'environment.lock.yaml') | ConvertFrom-Json
$spec = $lock.bootstrap.'windows-amd64'
$stateDir = Join-Path $repo '.state'
$pythonDir = Join-Path $stateDir 'python'
$pythonExe = Join-Path $pythonDir 'python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    $archive = Join-Path $stateDir 'python.zip'
    Invoke-WebRequest -Uri $spec.url -OutFile $archive
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $spec.digest) { throw 'Python archive checksum mismatch' }
    Expand-Archive -LiteralPath $archive -DestinationPath $pythonDir
    Remove-Item -LiteralPath $archive
}
& $pythonExe (Join-Path $PSScriptRoot 'environment.py') $Command --home $TargetHome
exit $LASTEXITCODE
