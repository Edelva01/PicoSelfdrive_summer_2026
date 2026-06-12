param(
    [string]$Port = "COM3",
    [string]$PythonExe = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found at '$PythonExe'."
}

& $PythonExe -m mpremote connect $Port exec "import os; print(os.listdir())"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Could not read Pico files on $Port." -ForegroundColor Yellow
    Write-Host "If COM is busy, close MicroPico vREPL/serial monitor and retry." -ForegroundColor Yellow
    exit 1
}
