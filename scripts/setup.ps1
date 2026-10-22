# Setup script for Heketon Monorepo (Windows PowerShell)
$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path "$PSScriptRoot\.."

if (-not (Test-Path "$RootDir\.env")) {
    Write-Host "==> Creating root .env from .env.example..." -ForegroundColor Cyan
    Copy-Item "$RootDir\.env.example" "$RootDir\.env"
}

Write-Host "==> 1. Syncing Backend dependencies with uv..." -ForegroundColor Cyan
Push-Location "$RootDir\backend"
uv sync
Pop-Location

Write-Host "==> 2. Installing Frontend dependencies with pnpm..." -ForegroundColor Cyan
Push-Location "$RootDir\frontend"
pnpm install
Pop-Location

Write-Host "==> Setup completed! Edit the root .env file to set your Supabase / LLM credentials." -ForegroundColor Green
