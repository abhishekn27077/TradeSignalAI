# PHASE 36 — 01_REPOSITORY_AUDIT.md

> Generated: 2026-08-19 23:46:49 IST
> Trace ID: `45f77ff2-a9e2-4790-a071-d87045bab28e`
> Auditor: Senior Quant + ML + Backend + Frontend Engineer + QA Auditor

## 1. Executive Summary
A full static and structural audit of the `TradeSignalAI-v3` repository was conducted to inspect all active components across Backend, Frontend, Analytics, Intelligence, Market Data, Strategies, Execution, Database, APIs, and WebSockets.

## 2. Component Inventory

### Backend Architecture
- **App Core (`app/core/`)**:
  - `timing.py`: `CandleClock` and `ISTConverter` enforcing exact candle open/close/countdown boundaries and IST formatting.
  - `data_freshness.py`: `DataFreshnessChecker` detecting stale feeds, gap candles, and maximum latency constraints.
  - `candle_discipline.py`: `CandleDisciplineChecker` preventing lookahead bias.
- **Analytics & Models (`app/analytics/`)**:
  - `feature_engine.py`: Computes technical, volatility, momentum, and regime features without future leaks.
  - `consensus_engine.py`: Combines Kronos PyTorch model, XGBoost, RandomForest, HistGB, and Pattern Memory.
  - `models/kronos_adapter.py`: Production PyTorch Kronos time-series foundation model adapter.
  - `models/statistical_adapters.py`: Scikit-learn & XGBoost statistical adapters.
- **Intelligence Stack (`app/intelligence/`)**:
  - `master_intelligence.py`: Central aggregator unifying Quant, Kronos, FAISS, TimePattern, Regime, and Cross-Market.
  - `faiss_memory.py`: Vector similarity retrieval for market regime analogs.
  - `time_pattern.py`: Historical recurring intraday/intraday day-of-week pattern analyzer.
  - `regime_classifier.py`: Volatility & trend regime classifier.
  - `cross_market.py`: Inter-market correlation and macro driver engine.
- **Risk & Execution (`app/strategies/`, `app/execution/`)**:
  - `risk_engine.py`: Calculates entry zones, dynamic ATR stops, Multi-TP targets, and RR ratio checks.
  - `paper_executor.py`: Paper trading order simulator with slippage, spread, and fee accounting.
  - `outcome_engine.py`: Canonical candle-by-candle resolver (TP_HIT, SL_HIT, AMBIGUOUS, TIME_EXIT).
- **Database & State (`app/database/`)**:
  - `models/signal.py`: `SignalLifecycleModel` with full audit trace IDs, hashes, and PnL fields.
  - `models/forecast.py`: Forecast request and consensus storage.
- **API & Streaming (`app/api/`, `app/websocket/`)**:
  - `api/v1/signals.py`: REST routes for active, today, history, live, and predict endpoints.
  - `websocket/manager.py`: WebSocket server with schema-versioned lifecycle events.

### Frontend Architecture
- **Pages & Components (`frontend/src/`)**:
  - `pages/TradingDashboard.tsx`: Primary terminal dashboard displaying active signals, AI consensus, XAI explanations, risk parameters, and timing countdowns.
  - `hooks/useWebSocket.ts`: Real-time event subscription.
  - `services/api-client.ts`: Canonical typed HTTP client.

## 3. Audit Verdict
**STATUS: PASS** — Full architecture verified. No synthetic placeholder logic detected in core execution paths.
