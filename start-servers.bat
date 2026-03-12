@echo off
title EchoWorks — Starting Servers
echo.
echo  ========================================
echo   EchoWorks Server Launcher
echo  ========================================
echo.

:: Kill any existing processes on ports 8080 and 9000
echo  [1/4] Cleaning up stale processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000.*LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080.*LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

:: Start Command Console (port 9000)
echo  [2/4] Starting Command Console on port 9000...
start "EchoWorks Command Console (9000)" /min cmd /c "cd /d C:\echoworks-operators && python dashboard_server.py --port 9000"

:: Start Ecosystem Website (port 8080)
echo  [3/4] Starting Ecosystem Website on port 8080...
start "EchoWorks Website (8080)" /min cmd /c "cd /d C:\codetyphoons-aionos26\docs && python -m http.server 8080"

:: Wait and verify
echo  [4/4] Waiting for servers to start...
timeout /t 3 /nobreak >nul

echo.
echo  ========================================
echo   Servers Running:
echo   - Website:         http://localhost:8080
echo   - Command Console: http://localhost:9000
echo   - Simulation:      http://localhost:9000/simulate
echo  ========================================
echo.
echo  Press any key to open the website...
pause >nul
start http://localhost:8080
