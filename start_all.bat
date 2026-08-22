@echo off
echo =======================================================
echo Starting TradeSignalAI-v3...
echo =======================================================

echo [1/2] Launching FastAPI Backend on Port 8000...
start "Backend (FastAPI)" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate 2>nul || echo Virtual env not found, using global Python && python -m uvicorn app.main:app --port 8000"

echo [2/2] Launching React Frontend on Port 3000...
start "Frontend (Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both services have been launched in separate windows!
echo Once they load, you can access the dashboard at: http://localhost:3000
echo =======================================================
