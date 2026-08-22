@echo off
title TradeSignalAI-v3 Launcher
echo ===================================================
echo Starting TradeSignalAI-v3 Platform...
echo ===================================================

cd /d "d:\trading Bots\FinalTrade\TradeSignalAI-v3"

echo 1. Launching Backend (FastAPI on http://127.0.0.1:8001)...
start "TradeSignalAI Backend" cmd /k "python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"

echo 2. Launching Frontend (Vite React on http://localhost:3000)...
start "TradeSignalAI Frontend" cmd /k "cd frontend && npm run dev"

echo ===================================================
echo TradeSignalAI-v3 is starting up!
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:3000
echo ===================================================
pause
