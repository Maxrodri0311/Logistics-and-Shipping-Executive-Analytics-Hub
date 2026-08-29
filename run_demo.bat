@echo off
echo =====================================================================
echo  LOGISTICS KPI AUTOMATION & MULTI-CARRIER ANALYTICS PLATFORM
echo =====================================================================
echo.

echo [1/4] Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/4] Installing / Verifying dependencies...
python -m pip install -r requirements.txt

echo.
echo [3/4] Running End-to-End Analytics Pipeline (35,000 shipments)...
python src/main.py --shipments 35000 --quotes 50000 --days 180

echo.
echo [4/4] Running Automated Pytest Verification Suite...
python -m pytest tests/ -v --tb=short

echo.
echo =====================================================================
echo  SUCCESS: Pipeline execution complete.
echo  Output generated at: dist\Executive_Logistics_KPI_Dashboard.xlsx
echo =====================================================================
pause
