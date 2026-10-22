# Start FastAPI Backend and Next.js Frontend concurrently using shared root .env
$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path "$PSScriptRoot\.."

Write-Host "==> Launching Backend (http://localhost:8000) & Frontend (http://localhost:3000)..." -ForegroundColor Cyan
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$RootDir\backend'; uv run fastapi dev app/main.py"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$RootDir\frontend'; pnpm dev"
