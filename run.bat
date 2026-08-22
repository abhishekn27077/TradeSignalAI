@echo off
echo ===================================================
echo Starting TradeSignalAI-v3 System
echo ===================================================

echo [1/2] Starting Backend API (FastAPI)...
start "TradeSignalAI Backend" cmd /k "cd /d "%~dp0" && uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Frontend (React/Vite)...
start "TradeSignalAI Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both services have been started in separate windows!
echo Backend API available at: http://localhost:8000
echo Frontend UI available at: http://localhost:5173
echo.
pause
