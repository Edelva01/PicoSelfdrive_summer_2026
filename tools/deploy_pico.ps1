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

$filesToDeploy = @(
    "config.py",
    "main.py",
    "motor.py",
    "sensorssr04.py",
    "wifi_car.py"
)

if (Test-Path "boot.py") {
    # Keep optional board startup behavior in sync when a local boot.py exists.
    $filesToDeploy += "boot.py"
}

foreach ($file in $filesToDeploy) {
    if (-not (Test-Path $file)) {
        throw "Expected file '$file' not found in project root."
    }
}

# Pre-flight: check whether the COM port is already locked.
$lockCheck = & $PythonExe -c "import serial,sys; p=sys.argv[1]; s=serial.Serial(p,115200,timeout=1); s.close(); print('PORT_OK')" $Port 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Cannot open $Port. Another app is using it (likely MicroPico vREPL/serial monitor)." -ForegroundColor Yellow
    Write-Host "Close the serial terminal and run deploy again." -ForegroundColor Yellow
    Write-Host $lockCheck
    exit 2
}

foreach ($file in $filesToDeploy) {
    Write-Host "Uploading $file -> :$file"
    & $PythonExe -m mpremote connect $Port fs cp $file ":$file"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed while uploading '$file'."
    }
}

Write-Host "Deployment complete. Current Pico root files:" -ForegroundColor Green
& $PythonExe -m mpremote connect $Port exec "import os; print(os.listdir())"
if ($LASTEXITCODE -ne 0) {
    throw "Deployment completed, but listing files failed."
}
