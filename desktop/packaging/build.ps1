$ErrorActionPreference = "Stop"

$desktop = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $desktop
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found: $python"
}

& $python (Join-Path $desktop "tools\make_icon.py")

Push-Location $root
try {
    & $python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath (Join-Path $desktop "dist") `
        --workpath (Join-Path $desktop "build") `
        (Join-Path $desktop "packaging\textshield-desktop.spec")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Built: $(Join-Path $desktop 'dist\TextShieldDesktop\TextShieldDesktop.exe')"
