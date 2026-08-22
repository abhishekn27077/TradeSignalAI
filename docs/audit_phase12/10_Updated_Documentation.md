# Documentation Index & Deployment Guide

## Architecture Summary
TradeSignalAI-v3 is an Event-Driven monolithic application.
- **Frontend:** React + Zustand + TailwindCSS
- **Backend:** FastAPI + Python 3.11 + SQLAlchemy
- **Communication:** REST APIs for initial state, WebSockets for real-time streaming, Event Bus for internal module decoupling.

## Module Dependency Flow
`Market Data` -> `Feature Store` -> `Forecast Engine` -> `Decision Intelligence` -> `Risk` -> `Execution` -> `Journal` -> `Strategy Lab`

## Production Deployment Checklist
1. Provide a managed PostgreSQL database (configured with TimescaleDB for OHLCV).
2. Provide a Redis instance (for Rate Limiting and Pub/Sub WebSockets).
3. Run migrations: `alembic upgrade head`
4. Start backend: `uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000`
5. Start frontend: `npm run build && npm start`

## Developer Guidelines
- **Event Bus:** Do not write direct module-to-module imports if data flows sequentially. Use `event_bus.publish()` and `event_bus.subscribe()`.
- **Database:** Always use asynchronous sessions (`yield get_db`).
- **Security:** New endpoints must use `Depends(get_api_key)` or `Depends(get_current_user)`.
