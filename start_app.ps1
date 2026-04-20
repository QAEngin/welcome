$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Virtual environment Python not found at $pythonExe"
    exit 1
}

if (Test-Path "requirements.txt") {
    Write-Host "Installing/updating requirements..."
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. app.py expects required environment variables."
}

Write-Host "Starting Flask app on http://127.0.0.1:5059 ..."
& $pythonExe app.py
