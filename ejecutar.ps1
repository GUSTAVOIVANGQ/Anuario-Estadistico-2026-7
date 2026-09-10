param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Argumentos
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$raizProyecto = $PSScriptRoot
$pythonLocal = Join-Path $raizProyecto ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $pythonLocal) {
    $pythonEjecutable = $pythonLocal
} else {
    $pythonEjecutable = "python"
}

$env:PYTHONPATH = Join-Path $raizProyecto "src"
& $pythonEjecutable -m anuario2026 @Argumentos
exit $LASTEXITCODE
