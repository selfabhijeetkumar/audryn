# AUDRYN — Start Frontend Dev Server
# Usage: .\scripts\start_frontend.ps1

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "AUDRYN Frontend — Starting dev server" -ForegroundColor Cyan
Write-Host "Frontend dir: $FrontendDir" -ForegroundColor Gray

Set-Location $FrontendDir

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Starting Vite dev server..." -ForegroundColor Yellow
npm run dev
