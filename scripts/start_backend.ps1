# AUDRYN — Start Backend
# Usage: .\scripts\start_backend.ps1 [-Port 8000] [-Reload]

param(
    [int]$Port = 8000,
    [switch]$Reload
)

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $ProjectRoot

Write-Host "AUDRYN Backend — Starting on port $Port" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

# Apply migrations first
Write-Host "Applying database migrations..." -ForegroundColor Yellow
& "$ProjectRoot\.venv\Scripts\python.exe" -m backend.db.migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migration failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Migrations OK" -ForegroundColor Green

# Start uvicorn
$args_list = @("backend.app.main:app", "--host", "0.0.0.0", "--port", "$Port")
if ($Reload) {
    $args_list += "--reload"
}

Write-Host "Starting uvicorn..." -ForegroundColor Yellow
& "$ProjectRoot\.venv\Scripts\uvicorn.exe" @args_list
