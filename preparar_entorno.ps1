param(
    [string]$PythonEjecutable = "python",
    [switch]$ConPlaywright,
    [switch]$SinFrontend
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

# Los venv basados en Anaconda necesitan registrar sus DLL antes de importar pip.
$pipBootstrap = @'
import os
import sys
from pathlib import Path

dll_dir = Path(sys.base_prefix) / "Library" / "bin"
dll_handle = os.add_dll_directory(str(dll_dir)) if os.name == "nt" and dll_dir.is_dir() else None
from pip._internal.cli.main import main
raise SystemExit(main())
'@
& $python -c $pipBootstrap install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "No se pudo actualizar pip en .venv." }
if ($ConPlaywright) {
    & $python -c $pipBootstrap install -e "$raizProyecto[playwright]"
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de Python." }
    & $python -m playwright install chromium
} else {
    & $python -c $pipBootstrap install -e $raizProyecto
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de Python." }
}

if (-not $SinFrontend) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Write-Warning "No se encontró Node.js/npm. El pipeline Python quedó listo, pero la interfaz React necesita Node.js 20 o superior para compilarse."
    } else {
        Push-Location (Join-Path $raizProyecto "web")
        try {
            & npm install --no-audit --no-fund
            if ($LASTEXITCODE -ne 0) { throw "npm install falló." }
            & npm run build
            if ($LASTEXITCODE -ne 0) { throw "npm run build falló." }
        } finally {
            Pop-Location
        }
    }
}

$convertidoresPdf = @()
if (Test-Path -LiteralPath 'Registry::HKEY_CLASSES_ROOT\PowerPoint.Application') {
    $convertidoresPdf += 'Microsoft PowerPoint'
}
$soffice = Get-Command soffice, libreoffice -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $soffice) {
    $soffice = @(
        'C:\Program Files\LibreOffice\program\soffice.exe',
        'C:\Program Files (x86)\LibreOffice\program\soffice.exe'
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if ($null -ne $soffice) {
    $convertidoresPdf += 'LibreOffice'
}
if ($convertidoresPdf.Count -eq 0) {
    Write-Warning 'La descarga PDF necesita Microsoft PowerPoint o LibreOffice. El resto del proyecto quedó instalado correctamente.'
} else {
    Write-Host "Conversión PPTX a PDF disponible: $($convertidoresPdf -join ', ')."
}

Write-Host "Entorno listo."
Write-Host "Pipeline: .\ejecutar.ps1 doctor"
Write-Host "Interfaz web: .\ejecutar.ps1 web"
