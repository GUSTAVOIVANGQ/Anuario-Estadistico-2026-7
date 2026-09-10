param(
    [string]$PythonEjecutable = "python",
    [switch]$ConPlaywright
)

$ErrorActionPreference = "Stop"
$raizProyecto = $PSScriptRoot
$venv = Join-Path $raizProyecto ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    & $PythonEjecutable -c "import venv" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "El Python seleccionado no incluye venv. Ejecuta de nuevo con -PythonEjecutable y la ruta de una instalación completa de Python 3.11 o superior."
    }
    & $PythonEjecutable -m venv $venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $python)) {
        throw "No se pudo crear .venv con el Python seleccionado: $PythonEjecutable"
    }
}

& $python -m pip install --upgrade pip
if ($ConPlaywright) {
    & $python -m pip install -e "$raizProyecto[playwright]"
    & $python -m playwright install chromium
} else {
    & $python -m pip install -e $raizProyecto
}

Write-Host "Entorno listo. Prueba: .\ejecutar.ps1 doctor"
