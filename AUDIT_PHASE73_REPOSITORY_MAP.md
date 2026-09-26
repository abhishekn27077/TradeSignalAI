# Phase 73 — Forensic Repository Inventory & Architecture Map

**Audit Date:** 2026-09-26  
**Repository:** `TradeSignalAI-v3`  
**Git Branch:** `master`  
**Git Commit:** `8b7e50267d7f501b14db5a1da22b89ad699295c8`  
**Audit Methodology:** Zero-Trust Forensic Code & Runtime Inspection  

---

## 1. Directory Structure & Module Layout

```
TradeSignalAI-v3/
├── app/
│   ├── agents/                   # Multi-agent LLM consensus and voting engines
│   │   ├── consensus/            # Voting mechanisms, weight calculations, debate rounds
│   │   ├── providers/            # LLM providers: OpenAI, OpenRouter, Heuristic, Router
│   │   └── manager.py            # Lifecycle and agent coordination
│   ├── analytics/                # Statistical engines, ablation, drift, reality checks
│   │   ├── models/               # Kronos model adapter, statistical adapters
│   │   ├── ablation_engine.py    # [FORENSIC] Returns hardcoded ablation scores
│   │   ├── edge_drift_engine.py  # Drift monitoring engine (not wired to execution)
│   │   ├── no_trade_engine.py    # [FORENSIC] Returns hardcoded counterfactuals
│   │   └── prediction_reality_engine.py # [FORENSIC] Hardcoded scorecard benchmarks
│   ├── api/                      # FastAPI layer (357 endpoints across 49 router files)
│   │   ├── v1/                   # Main v1 API routers
│   │   │   ├── auth.py           # OAuth2 token endpoints
│   │   │   ├── signals.py        # Canonical signal queries & injection
│   │   │   ├── signal_stream_routes.py # SignalFactory stream endpoints
│   │   │   ├── ws.py             # Global WebSocket handler (unauthenticated)
│   │   │   └── ... (45 other route files)
│   │   ├── dependencies.py       # get_current_user (fail-closed, but only on 4 routes)
│   │   └── middleware.py         # Rate limit, fingerprint, security headers
│   ├── auth/                     # Password hashing, JWT creation & token verification
│   │   └── security.py           # bcrypt hashing (fail-closed) & API key validation
│   ├── backtesting/              # Backtest engine and performance metrics
│   ├── brokers/                  # Broker adapters (TradingView paper broker only)
│   │   ├── factory.py            # Broker factory
│   │   └── tradingview_broker.py # Paper trading simulator with TradingView pricing
│   ├── config/                   # Configuration settings and environment validation
│   │   └── settings.py           # Pydantic Settings class
│   ├── core/                     # Canonical signal services & business domain models
│   │   ├── canonical_signal_service.py # Core service: loads candles, calculates scores
│   │   ├── signal_factory.py     # [FORENSIC] Generates signals from sha256(hour)
│   │   ├── signal_identity.py    # SignalIdentityGuard (not called in hot path)
│   │   └── execution_abstraction.py # Real money lockout safety guard
│   ├── database/                 # SQLAlchemy models, sessions, connection manager
│   │   ├── manager.py            # DatabaseManager (SQLite WAL mode)
│   │   └── models/               # 26 SQLAlchemy model definition files
│   ├── execution/                # Order routing, coordinator, failsafes, reconciliation
│   │   ├── coordinator.py        # Coordinates signal -> risk -> failsafe -> execution
│   │   ├── reconciliation.py     # Position reconciliation (Phase 74 rewritten)
│   │   └── router.py             # Smart order router
│   ├── forecast_engine/          # ML model registry and prediction lifecycle
│   ├── indicators/               # Native indicators registry & cluster definitions
│   ├── journal/                  # Automated trade journaling and daily review
│   ├── market_data/              # OHLCV providers, live refresher, candle validation
│   │   ├── live_refresher.py     # Background loop refreshing candles from providers
│   │   └── providers/            # tvDatafeed, Yahoo Finance, SQLite provider
│   ├── paper_trading/            # Paper execution simulator, account manager
│   │   ├── execution_simulator.py # Conservative same-bar SL/TP ambiguity resolution
│   │   └── executor.py           # Paper executor with short-cover and input validation
│   ├── runtime/                  # Scheduled background workers, latency monitor
│   │   └── latency_monitor.py    # [FORENSIC] Contains hardcoded 8-float sample list
│   ├── shadow/                   # Shadow prediction ledger and lifecycle
│   │   └── shadow_live_engine.py # Generates immutable predictions (has fallback flaw)
│   ├── strategies/               # Strategy plugins and technical indicator calculations
│   └── validation/               # Walk-forward cross validation engine
│       └── walk_forward_engine.py # [FORENSIC] Tests dummy `c > ema20`, not full model
├── frontend/                     # React 19 + TypeScript + Vite dashboard
│   ├── src/                      # Components, API client, hooks, pages
│   └── package.json              # Vite build setup
├── tests/                        # 159 pytest test suites (958 collected tests)
├── docs/                         # Architecture, compliance, and phase reports
├── tradesignal.db                # SQLite database (251k candles, 42k signal records)
├── .env                          # Local environment file (untracked in git)
├── .env.example                  # Sanitized template
├── .gitignore                    # Git ignore file (correctly ignores .env, *.db)
└── pytest.ini                    # Test runner configuration
```

---

## 2. Core Execution Paths & Entry Points

### 2.1 Backend Startup Path
1. **Entry Point:** `app.main:app` (FastAPI instance via `create_app()`).
2. **Lifespan Manager (`app/main.py:26`):**
   - Initializes logging (`setup_logging()`).
   - Connects to SQLite (`db_manager.connect()`) and runs `db_manager.init_db()`.
   - Runs `startup_validator.validate_all()`.
   - Registers core provider instances (`database`, `market`, `tradingview`, `ai`).
   - Starts background tasks:
     - `stream_manager.start_polling()`
     - `strategy_manager.start()`
     - `coordinator.start()`
     - `live_refresher.refresh_all_async()` loop (every 5 minutes)
     - `h4_forecast_engine`, `swing_scanner`, `live_forecast_scheduler`.

### 2.2 Canonical Signal Generation Paths (Three Divergent Pipelines)
The codebase contains **three distinct signal generation implementations**:

* **Pipeline 1 (Agent Consensus Pipeline):**
  `app/strategies/manager.py` → emits `SignalGenerated` event → `app/agents/manager.py` triggers consensus → `app/agents/consensus/voting.py` evaluates votes → emits `ConsensusCompleted` → `app/execution/coordinator.py` validates risk and routes order.
* **Pipeline 2 (Canonical Signal Service):**
  `app/core/canonical_signal_service.py:get_active_snapshot()` → calls `_evaluate_single_asset()` → queries `historical_candles` from `tradesignal.db` → computes RSI, MACD, EMA, ATR → if rows < 10, fabricates candles from `ASSET_BASE_PRICES`.
* **Pipeline 3 (Signal Factory - Phase 62+):**
  `app/core/signal_factory.py:generate_signal()` → queries `tradingview_adapter.extract_indicator_observations()` (which returns hardcoded RSI=58.2) → hashes string `f"{asset}_{timeframe}_{hour}"` using SHA-256 → decides `direction = BUY/SELL/WAIT` based on `seed % 3` → powers `/api/v1/signals/*` and `/api/v1/campaigns/*`.

### 2.3 Order Execution Path
1. `app/execution/coordinator.py:_execute_order()` receives `trade_proposal`.
2. Calls `app/risk/engine.py:validate_trade()` (checks RR ratio and quantity limit).
3. Reads account balance from `account_manager` and calls `failsafe_manager.evaluate_failsafes()`.
4. Dispatches order to `app/execution/router.py:smart_router.execute_trade()`.
5. `smart_router` delegates to `TradingViewBrokerAdapter` (simulated paper fill) or `PaperExecutor`.
6. Enforces Rule Zero: `execution_abstraction.py` throws `PermissionError` if `REAL_MONEY_ENABLED` is active.

### 2.4 Authentication & Authorization Path
1. JWT verification: `app/auth/security.py:verify_token()`.
2. Dependency: `app/api/dependencies.py:get_current_user()` (fails closed with HTTP 401).
3. **Flaw:** Only 4 of 357 routes declare `Depends(get_current_user)` or `Depends(require_role)`. 61 state-changing endpoints accept unauthenticated requests.
