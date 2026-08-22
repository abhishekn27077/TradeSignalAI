# Phase 51 Baseline & System Forensic Inspection Report

**Generated on:** Saturday, 22 August 2026 06:30 PM IST  
**System:** TradeSignalAI-v3 Production Quantitative & Decision Architecture  
**Certification Status:** Phase 49 Certified (32/32) | Phase 50 Certified (43/43) | Frontend Verified

---

## 1. Executive Baseline Summary

TradeSignalAI-v3 is an institutional-grade, multi-layer market intelligence, automated forecasting, and actionable signal orchestration platform. The system operates on strict temporal truth, timezone-aware UTC internals with Indian Standard Time (IST) presentation formatting, zero-trust risk gating, and immutable ledger governance.

### Certified Subsystems Overview
1. **Authoritative Temporal Clock:** `MarketClockService` (`app/core/market_clock.py`) guarantees drift-free UTC-to-IST canonical conversion, dynamic timeframe-scaled and ATR-scaled entry/holding envelopes, and strict data freshness validation (`DATA_STALE` / `DATA_UNAVAILABLE`).
2. **Cold-Start Startup Sync:** `StartupSyncService` (`app/runtime/startup_sync.py`) verifies database synchronization against live market providers on cold start, preventing duplicate candles and enforcing fail-closed discipline.
3. **Actionable Decision Suite:** `ActionableSignalEngine` and `RevalidationEngine` (`app/decision/`) manage deterministic state transitions (`WATCH` -> `ENTER_NOW` -> `IN_POSITION` -> `RESOLVED` / `INVALIDATED` / `EXPIRED`), anti-whipsaw hysteresis, and versioned lineage tracking.
4. **Execution & Ledger Forensics:** `OutcomeEngine` (`app/execution/outcome_engine.py`) and `ShadowLedgerEngine` (`app/analytics/shadow_ledger_engine.py`) provide immutable trade resolution, MFE/MAE calculation, intra-candle ambiguity resolution, and friction modeling (spread, slippage, commission).
5. **Frontend Command Center:** Reactive TypeScript/React 19 single-page dashboard built with Vite, Ant Design, and TailwindCSS, rendering actionable setups, countdown clocks, and live audit telemetry.

---

## 2. Baseline Test Suite Verification

### Phase 49 Runtime Acceptance (32 / 32 Passed - 100%)
- **Test A (Startup Data Refresh):** 9/9 assets synchronized without duplicates.
- **Test B (Future Signal Only):** Expired signals strictly rejected; target_time > current_time verified.
- **Test C (Restart Re-Evaluation):** Stateless restart recomputes forecast dynamically; prior predictions retained in immutable ledger.
- **Test D (Past Forecasts):** Elapsed signals removed from active feed, present in shadow ledger.
- **Test E (Time Formatting):** Strict IST pattern `Weekday, DD Month YYYY HH:MM AM/PM IST` validated.
- **Test F (No Hardcoded Timestamps):** Zero hardcoded forecast timestamps in production code.
- **Test G (Freshness Failure):** Fail-closed on stale data (>3600s) and provider dropouts.
- **Test H (End-to-End Lineage):** Full traceability from provider candle -> DB -> feature -> model -> decision -> actionable UI signal.

### Phase 50 Actionable Lifecycle & Forensic Suite (43 / 43 Passed - 100%)
- **Actionable Setups:** Dynamic lead/lag entry envelopes scaled across 15M, 1H, 4H, and 1D timeframes.
- **Revalidation Engine:** Real-time pre-entry validation with anti-whipsaw hysteresis (+15% confidence delta required for flip).
- **Zero-Trust Risk Engine:** Minimum 1.2:1 Risk-to-Reward ratio enforced; high-impact event risk filtering active.
- **Parent/Child Lineage:** Versioning and immutable parent IDs preserved across signal strengthen/weaken cycles.

---

## 3. Architecture & Data Flow Matrix

```
Market Data (Yahoo / MT5 / Binance)
  ↓
StartupSyncService / MarketClockService (Staleness & Canonical Time Gating)
  ↓
SQLite Database (historical_candles, tradesignal.db)
  ↓
Quantitative Feature & Indicator Pipeline (ATR, ADX, RSI, MACD, VWAP, SuperTrend)
  ↓
Market Intelligence (H4 Engine, Consensus Engine, ML Models)
  ↓
ActionableSignalEngine (State Machine & Dynamic Envelopes)
  ↓
RevalidationEngine (Anti-Whipsaw & Live Real-Time Validation)
  ↓
Risk Engine (Exposure, Position Sizing, Minimum R:R)
  ↓
FastAPI REST API & WebSocket Feed (/api/v1/signals/*)
  ↓
Frontend Command Center (React 19 / Vite / Ant Design)
```

---

## 4. Current Database Schema & Persistence

| Table Name | Primary Role | Immutability / Constraints | Indexes |
|:---|:---|:---|:---|
| `historical_candles` | Raw OHLCV bar storage | `UNIQUE(symbol, timeframe, timestamp)` | symbol, timeframe, timestamp |
| `daily_predictions` | Immutable raw model inferences | Append-only ledger | symbol, date, timeframe |
| `actionable_signals` | State-machine managed setups | Versioned with `parent_signal_id` | id, symbol, status, target_time_utc |
| `shadow_trades` | Simulated trade executions | Immutable historical replay | id, symbol, status, exit_time |
| `system_logs` | Audit trail and health logs | Timestamped events | timestamp, level |

---

## 5. Identified Areas for Phase 51 Expansion

1. **Market Structure:** Swing High/Low detection, Bullish/Bearish BOS, Bullish/Bearish CHoCH, MSB, and multi-timeframe structural strength.
2. **Smart Money Concepts (SMC):** Bullish/Bearish Order Blocks, Breaker/Mitigation blocks with lifecycle tracking (`ACTIVE`, `TOUCHED`, `PARTIALLY_MITIGATED`, `FULLY_MITIGATED`, `INVALIDATED`), Fair Value Gaps (FVG), Premium vs. Discount active dealing ranges.
3. **Liquidity Analysis:** Buy-side/Sell-side liquidity pools, Equal Highs/Lows (EQH/EQL), session sweeps (Asia/London/NY), and sweep confirmation filters.
4. **SMT & Cross-Asset Correlation:** SMT divergence detection (e.g. XAUUSD vs DXY, EURUSD vs DXY, BTC vs ETH).
5. **Technical Confluence Engine:** Multi-factor weighted confluence scoring (0-100) combining structural, liquidity, SMC, session, volatility, and momentum evidence without collinear double-counting.
6. **Strategy Router & Explainability:** Regime-adaptive strategy selection with full "Why / Risk / Invalidation" evidence trees.
7. **Rigorous Backtesting & Anti-Lookahead:** Walk-forward validation, feature ablation studies, Monte Carlo trade sequence analysis, and friction-realistic backtesting (spread, slippage, latency, commission).
