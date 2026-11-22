# AUDRYN — Run All Tests
# Usage: .\scripts\run_tests.ps1 [-Suite all|phase7|phase8-security|phase8-db|phase8-e2e] [-Verbose]

param(
    [ValidateSet("all", "phase7", "phase8-security", "phase8-db", "phase8-e2e")]
    [string]$Suite = "all",
    [switch]$Verbose
)

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $ProjectRoot
Set-Location $ProjectRoot

$python = "$ProjectRoot\.venv\Scripts\python.exe"
$verbosity = if ($Verbose) { "-v" } else { "" }

Write-Host "AUDRYN Test Runner — Suite: $Suite" -ForegroundColor Cyan

switch ($Suite) {
    "phase7" {
        & $python -m pytest tests/unit/test_phase7_fastapi_integration.py $verbosity --tb=short
    }
    "phase8-security" {
        & $python -m pytest tests/unit/test_phase8_security.py $verbosity --tb=short
    }
    "phase8-db" {
        & $python -m pytest tests/unit/test_phase8_db_integrity.py $verbosity --tb=short
    }
    "phase8-e2e" {
        & $python -m pytest tests/integration/test_phase8_e2e_journey.py $verbosity --tb=short
    }
    "all" {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $logfile = "$ProjectRoot\docs\test_run_$timestamp.txt"
        Write-Host "Output: $logfile" -ForegroundColor Gray
        & $python -m pytest $verbosity --tb=short 2>&1 | Tee-Object $logfile
    }
}

Write-Host ""
Write-Host "Test run complete." -ForegroundColor Green
