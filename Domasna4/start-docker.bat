@echo off
REM CryptoInfo Docker Quick Start Script for Windows

echo ========================================
echo Starting CryptoInfo with Docker Compose
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Stop any existing containers
echo Cleaning up existing containers...
docker-compose down 2>nul

echo.
echo Building and starting services...
echo This may take 5-10 minutes on first run...
echo.

REM Build and start all services
docker-compose up --build -d

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Services started successfully!
    echo.
    echo Service Status:
    docker-compose ps
    echo.
    echo Access your application:
    echo   Frontend:    http://localhost:3000
    echo   Backend API: http://localhost:8080/api
    echo   Health:      http://localhost:8080/api/health
    echo.
    echo View logs with: docker-compose logs -f
    echo Stop services with: docker-compose down
    echo.
    echo Application is ready to use!
) else (
    echo.
    echo [ERROR] Failed to start services.
    echo Check logs with: docker-compose logs
    pause
    exit /b 1
)

pause

