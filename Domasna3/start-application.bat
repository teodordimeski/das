@echo off
REM Start Crypto Application - Backend and Frontend
REM This batch file starts the Spring Boot backend and React frontend

echo ========================================
echo Starting Crypto Application
echo ========================================
echo.

REM Get the script directory
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%
set FRONTEND_DIR=%SCRIPT_DIR%crypto-frontend

REM Step 1: Start Backend (Spring Boot)
echo [1/2] Starting Spring Boot Backend...
echo Backend directory: %BACKEND_DIR%
echo.

cd /d "%BACKEND_DIR%"
start "Spring Boot Backend" cmd /k ".\mvnw.cmd spring-boot:run"

echo Backend started in new window
echo Waiting for backend to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

REM Step 2: Start Frontend (React)
echo.
echo [2/2] Starting React Frontend...
echo Frontend directory: %FRONTEND_DIR%
echo.
echo ========================================
echo Frontend starting...
echo Backend: http://localhost:8080
echo Frontend: http://localhost:3000
echo ========================================
echo.
echo Press Ctrl+C to stop the frontend
echo (Close the backend window separately)
echo.

cd /d "%FRONTEND_DIR%"
call npm start

echo.
echo Application stopped.
pause


