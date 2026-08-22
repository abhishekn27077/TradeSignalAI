# TradeSignalAI-v3: Master Cross-System Architecture & Discovery Audit

**Audit Date (UTC):** 2026-08-22T19:41:00Z  
**Audit Scope:** 41 App Submodules, 41 API Route Modules, 42 Database Tables, 6,336 Frontend Modules.

---

## 1. Full Subsystem Component Mapping

| Subsystem Component | Primary File Path | Responsibility | Inputs | Outputs | Data Source | Database Table | API Endpoint | Status | Problems & Duplicate Logic | Fallback / Synthetic Behavior |
|:---|:---|:---|:---|:---|:---|:---|:---|:---:|:---|:---|
| **Market Clock** | `app/core/market_clock.py` | Canonical timekeeping, UTC/IST conversions, staleness checking | System clock | `MarketClockReport` | System time | None | `/api/v1/health/market-clock` | `VERIFIED` | Clean | None |
| **Startup Sync** | `app/market_data/startup_sync.py` | Initial candle hydration & deduplication | Provider candles | Stored candles | Yahoo Finance / TV | `historical_candles` | None (Worker) | `VERIFIED` | Fails closed on provider error | None |
| **Data Quality Engine** | `app/market_data/quality/engine.py` | Fail-closed validation for OHLC, timestamps, volume, spikes | `pd.DataFrame` | `DataQualityReport` | Raw DB / Provider | `data_quality_reports` | `/api/v1/system-intelligence/market-data-health` | `VERIFIED` | Clean | Fails closed on corruption |
| **Provider Consensus** | `app/market_data/providers/consensus.py` | Parallel feed validation within 0.5% tolerance | Primary / Secondary DFs | `ProviderConsensusReport` | Yahoo Finance + TV | None | `/api/v1/system-intelligence/market-data-health` | `VERIFIED` | Clean | Rejects on mismatch |
| **Market Structure** | `app/strategies/Structure/` | Swing points, BOS, CHoCH, MSB, trend strength | `pd.DataFrame` | `StructureStrengthReport` | Normalized candles | None | `/api/v1/analysis/structure/{asset}` | `VERIFIED` | Non-repainting | None |
| **Smart Money (SMC)** | `app/strategies/SmartMoney/` | Order Blocks, FVGs, Liquidity Pools | `pd.DataFrame` | `OrderBlock`, `FVG`, `LiquidityPool` | Normalized candles | None | `/api/v1/analysis/smart-money/{asset}` | `VERIFIED` | Non-repainting | None |
| **Strategy Ensemble** | `app/strategies/Ensemble/ensemble_engine.py` | Cluster-dampened 10-family strategy voting | `List[StrategyVote]` | `EnsembleDecision` | Strategy Engines | None | `/api/v1/system-intelligence/ensemble/evaluate` | `VERIFIED` | 60% supermajority required | Resolves to NEUTRAL if split |
| **Regime Classifier** | `app/strategies/Regime/regime_classifier.py` | Market regime identification (Trend/Range/Vol) | `pd.DataFrame` | `MarketRegimeResult` | Normalized candles | None | `/api/v1/analysis/regime/{asset}` | `VERIFIED` | Clean | None |
| **Confluence Engine** | `app/strategies/Confluence/confluence_engine.py` | 6-layer score synthesis with collinearity dampening | Multi-engine reports | `ConfluenceResult` (0-100) | Normalized candles | None | `/api/v1/analysis/confluence/{asset}` | `VERIFIED` | Collinearity dampener active | None |
| **Signal Quality & Gating** | `app/strategies/SignalQuality/engine.py` | Setup grading (`A+`, `A`, `B`, `C`, `NO_TRADE`) | Setup metrics | `SignalQualityEvaluation` | Confluence + Market Data | None | `/api/v1/system-intelligence/signal-quality/evaluate` | `VERIFIED` | Enforces 16 rejection reasons | Blocks trade execution |
| **Risk Budget Engine** | `app/portfolio/risk_budget_engine.py` | Dynamic equity-based lot sizing & drawdown halting | Equity, Stop, ATR | `SizingResult` | Portfolio State | `paper_accounts` | `/api/v1/risk/` | `VERIFIED` | 5% daily drawdown circuit breaker | None |
| **Currency Exposure** | `app/portfolio/currency_exposure_engine.py` | Decomposed base/quote USD/EUR net exposure | Active positions | `CurrencyExposureReport` | Open positions | `paper_positions` | `/api/v1/system-intelligence/portfolio-exposure` | `VERIFIED` | Blocks >3.0 lot stacking | None |
| **Execution Simulator** | `app/execution/simulator.py` | Slippage, bid/ask spread, and latency modeling | `SimulatedOrder` | `SimulatedFill` | Real-time prices | `paper_orders` | `/api/v1/system-intelligence/execution/simulate` | `VERIFIED` | Frictions active | None |
| **Tomorrow Forecast** | `app/analytics/tomorrow_forecast_engine.py` | Daily multi-model forward predictions | Market features | Forecast Package | DB / Models | `forecast_results` | `/api/v1/forecasts/tomorrow` | `PARTIALLY_VERIFIED` | `daily_signal_journal.py` contained static hash fallback | Label fallback as `FALLBACK` |
| **Sequence Engine** | `app/strategies/indicators/sequence_engine.py` | Candlestick sequence & continuation calculation | `pd.DataFrame` | `SequenceResult` | OHLCV data | None | None | `PARTIALLY_VERIFIED` | Confidence clamping at 41.2% in edge case | Needs dynamic scaling |
| **TradingView Provider**| `app/market_data/providers/tradingview.py` | TradingView feed via `tvDatafeed` | TV Web API | `Candle` list | TradingView | `historical_candles` | `/api/v1/data/candles` | `PARTIALLY_VERIFIED` | Circuit breaker triggers if network offline | Marks feed UNAVAILABLE |
| **TradeWithHomie** | None (External Reference) | External system mentioned in specs | None | None | None | None | None | `UNAVAILABLE` | **No technical code exists** | Marked as NOT INTEGRATED |
| **Kronos & FAISS** | `app/intelligence/` / `app/forecast/` | Vector-similarity & time-series forecast | Historical embeddings | Similarity match | Local embeddings | `research_experiments` | `/api/v1/intelligence/` | `WORKING` | Clean | None |
| **Shadow / Paper Trading**| `app/paper_trading/` / `app/decision/` | Simulated trade ledgering & forward evaluation | Signals | Trade lifecycle | SQLite DB | `paper_orders`, `paper_positions` | `/api/v1/paper/` | `VERIFIED` | Clean | None |
| **Prediction Ledger** | `app/analytics/forecast_manager.py` | Immutable prediction log | Signals | Hash-verified record | SQLite DB | `predictions`, `decision_history` | `/api/v1/signals/ledger` | `VERIFIED` | Clean | None |
