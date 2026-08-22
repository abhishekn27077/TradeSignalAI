# Architecture Audit

## Overview
TradeSignalAI-v3 follows a modular, monolithic architecture built on FastAPI and React. The system is highly decoupled into discrete service domains, communicating via an event-driven architecture using an internal Event Bus.

## Folder Structure
- `app/` (Backend core)
  - `agents/`: AI agents and provider interfaces
  - `api/v1/`: Unified REST routing layer
  - `auth/`: Security and rate limiting
  - `core/`: Configurations and plugin loading
  - `database/`: SQLAlchemy models and migrations
  - `decision/`: Decision Intelligence
  - `forecast_engine/`: H4 and Swing forecasting
  - `market_data/`: Data providers and feature store
  - `operations/`: System health and audit logging
  - `portfolio/`: Portfolio management and ranking
  - `strategy_lab/`: AI Quantitative Research
  - `utils/`: Event bus, WebSocket manager, scheduler
- `frontend/src/` (React UI)
  - `pages/`: Mapped exactly to backend domains
  - `components/`: Reusable UI elements
  - `store/`: Zustand state management

## Architecture Violations & Smells
1. **Coupling in Strategy Lab**: The `evaluator.py` module in Strategy Lab is currently a stub and needs tight integration with `app.backtest` without circular dependencies.
2. **Missing Dependency Injections**: Several database operations rely on synchronous global sessions rather than async dependency injection in the REST layer.
3. **Dead Code**: The original `/research` router (Phase 6) has overlapping functionality with `/strategy_lab` (Phase 11). `app.api.v1.research_routes` should be pruned or merged.

## Conclusion
The architecture is solid and successfully implements an event-driven domain model. The primary focus for production readiness is removing duplicate code between Phase 6 and Phase 11.
