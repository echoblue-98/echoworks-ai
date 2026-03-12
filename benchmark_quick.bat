@echo off
REM AION OS - Quick Start LM Studio Benchmark
REM Double-click to run default benchmark (5 scenarios)
REM Or use: benchmark_quick.bat full   - for all 10 scenarios
REM         benchmark_quick.bat quick  - for 3 scenarios

echo.
echo ============================================================
echo   AION OS - LM Studio Sovereign Inference Benchmark
echo ============================================================
echo.

cd /d "%~dp0"

if "%1"=="full" (
    python aionos/api/lmstudio_client.py --scenarios=10
) else if "%1"=="quick" (
    python aionos/api/lmstudio_client.py --quick
) else (
    python aionos/api/lmstudio_client.py
)

echo.
pause
