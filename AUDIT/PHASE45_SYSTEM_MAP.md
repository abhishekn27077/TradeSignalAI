# PHASE 45 — FULL SYSTEM ARCHITECTURE MAP & ENTRY POINT AUDIT

**Audit Date (UTC):** 2026-08-22T20:53:10Z  
**System Under Audit:** TradeSignalAI-v3 (41 Backend Modules, 42 SQLite Database Tables, 6,336 Frontend Modules)  
**Authority:** Principal Quantitative Systems Auditor & Enterprise Architect

---

## 1. System Topology & Data Flow Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LIVE MARKET DATA SOURCES                        │
│             Yahoo Finance (Primary)  |  TradingView (Secondary)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   CANONICAL MARKET DATA SERVICE                        │
│          MarketDataSnapshot | Monotonicity | Staleness Gating          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  MULTI-LAYER FEATURE & SMC ENGINES                     │
│       Technical (RSI, EMA, ATR, MACD) | Structure (BOS, CHoCH, OB)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                ECONOMIC CALENDAR & NEWS IMPACT ENGINE                  │
│       Forex Factory Ingestion | EconomicEventAnalyzer | Macro Bias     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    MULTI-MODEL CONSENSUS ENSEMBLE                      │
│        10 Strategy Families (1/√K Collinearity Dampening)              │
│        8 Model Layers: Quant, Kronos, FAISS, Regime, Macro, News, AI   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  CANONICAL DECISION ENGINE (SSOT)                      │
│     Signal Quality Gating (A+, A, B, C, NO_TRADE) | 16 Rejection Gates │
│     Portfolio Currency Exposure Engine | Risk Budgeting Engine (5% DD) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   CANONICAL SIGNAL PERSISTENCE                         │
│       predictions | decision_history | signal_lifecycle (SQLite)       │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│     FASTAPI REST & WEBSOCKET APIS    │ │   VIRTUAL SHADOW EXECUTION    │
│  /api/v1/signals/live                │ │   ExecutionSimulator          │
│  /api/v1/decision/evaluate           │ │   paper_orders | positions    │
│  /api/v1/system-intelligence/*       │ │   Outcome Resolution Engine   │
└───────────────────┬──────────────────┘ └───────────────┬───────────────┘
                    │                                    │
                    ▼                                    ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│         FRONTEND DASHBOARDS          │ │      PREDICTION LEDGER        │
│  TradingDashboard.tsx                │ │  Immutable Outcome Store      │
│  Today's Signals | H4 Forecasts      │ │  Statistical Evidence Suite   │
│  MarketStructureIntelligence.tsx     │ │  Calibration & Drift Engine   │
└──────────────────────────────────────┘ └───────────────────────────────┘
```

---

## 2. Comprehensive Entry Points & Dependencies

| Component | File Path | Primary Entry Point | Database Dependencies | External Connectors |
|:---|:---|:---|:---|:---|
| **FastAPI Core** | `app/main.py` | `app` (FastAPI instance) | `tradesignal.db` | HTTP, WebSockets |
| **Canonical Decision** | `app/decision/canonical_decision_engine.py` | `canonical_decision_engine.evaluate_market()` | `predictions`, `decision_history` | Internal SSOT |
| **Market Data Normalizer** | `app/market_data/canonical_snapshot.py` | `CanonicalMarketDataService.create_snapshot()` | None | YFinance / TV |
| **Data Quality Engine** | `app/market_data/quality/engine.py` | `DataQualityEngine.evaluate()` | `data_quality_reports` | In-memory stream |
| **Strategy Ensemble** | `app/strategies/Ensemble/ensemble_engine.py` | `StrategyEnsembleEngine.evaluate_ensemble()` | None | 10 Strategy Engines |
| **Economic Calendar** | `app/market_data/economic_calendar.py` | `EconomicCalendarEngine.get_upcoming_events()` | `economic_events` | Forex Factory / Local |
| **News Intelligence** | `app/news/intelligence.py` | `NewsIntelligenceEngine.evaluate()` | `historical_news` | Macro / RSS Feeds |
| **Shadow Execution** | `app/analytics/shadow_ledger_engine.py` | `ShadowLedgerEngine.record_prediction()` | `paper_orders`, `positions` | Simulator |
| **Outcome Resolution** | `app/decision/outcome_engine.py` | `OutcomeEngine.resolve_outcomes()` | `research_validations` | Price replay |
| **Frontend Root** | `frontend/src/App.tsx` | React Router DOM | None | REST / WS APIs |
