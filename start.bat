@echo off
start "Backend" cmd /k "cd /d %~dp0 && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo Starting TradeSignalAI-v3...
