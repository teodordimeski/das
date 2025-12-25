# Start Crypto Application - Backend and Frontend
# This script starts the Spring Boot backend and React frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Crypto Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = $scriptDir
$frontendDir = Join-Path $scriptDir "crypto-frontend"

# Step 1: Start Backend (Spring Boot)
Write-Host "`n[1/2] Starting Spring Boot Backend..." -ForegroundColor Yellow
Write-Host "Backend directory: $backendDir" -ForegroundColor Gray

# Change to backend directory and start Spring Boot in background
Set-Location $backendDir
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:backendDir
    & .\mvnw.cmd spring-boot:run
}

Write-Host "Backend started in background (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "Waiting for backend to initialize (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Step 2: Start Frontend (React)
Write-Host "`n[2/2] Starting React Frontend..." -ForegroundColor Yellow
Write-Host "Frontend directory: $frontendDir" -ForegroundColor Gray

# Change to frontend directory and start React
Set-Location $frontendDir
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Frontend starting..." -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8080" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop both servers`n" -ForegroundColor Yellow

# Start frontend (this will block)
npm start

# Cleanup: Stop backend job when frontend stops
Write-Host "`nStopping backend..." -ForegroundColor Yellow
Stop-Job $backendJob
Remove-Job $backendJob
Write-Host "Application stopped." -ForegroundColor Green


