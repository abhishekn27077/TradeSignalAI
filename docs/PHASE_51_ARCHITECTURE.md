# Phase 51+ Architecture Specification

**System:** TradeSignalAI-v3 Institutional Quantitative Engine  
**Author:** Quantitative Architecture & Engineering Team  
**Scope:** Multi-Layer Market Intelligence, Smart Money Concepts, Confluence Engine, and High-Fidelity Backtesting

---

## 1. System Topology & Data Flow

```
+-------------------------------------------------------------------------+
|                         MARKET DATA INGESTION                           |
|       - Live OHLCV Candles (1D, 4H, 1H, 15M, 5M)                        |
|       - MarketClockService: Canonical UTC / IST Formatting              |
|       - Freshness & Integrity Check (Fail-Closed on Stale Data)         |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  LAYER 1: ATOMIC FEATURE EXTRACTION                     |
|  - Technical Indicators: ATR, ADX, RSI, MACD, SMA 200, SuperTrend,      |
|    UT-Bot ATR Trailing Bands, VWAP                                      |
|  - Session Profiler: Asian Range, London Open, NY AM, NY PM Killzones   |
|  - Dealing Range: 50% Equilibrium, Premium / Discount Zones             |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|             LAYER 2: MARKET STRUCTURE & SMART MONEY (SMC)               |
|  - Swing Detection: Multi-Bar Left/Right Extremes (Zero Lookahead)      |
|  - Break of Structure (BOS) & Change of Character (CHoCH)              |
|  - Market Structure Break (MSB) & Trend Strength Evaluation             |
|  - Order Blocks (OB): Bullish, Bearish, Breaker, Mitigation Lifecycles  |
|  - Fair Value Gaps (FVG): Imbalance Quantification & Mitigation State   |
|  - Liquidity Pools: Equal Highs/Lows (EQH/EQL), Prior Day/Week H/L      |
|  - Sweeps: Wick penetration with range recovery confirmation            |
|  - SMT Divergence: Cross-pair relative strength discrepancies           |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|             LAYER 3: MULTI-TIMEFRAME & REGIME ROUTER                    |
|  - Multi-Timeframe Hierarchy: HTF Trend -> MTF Structure -> LTF Entry   |
|  - Market Regime Classification: STRONG_TREND, RANGE, BREAKOUT, etc.    |
|  - Strategy Router: Directs setup generation to optimal family          |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|          LAYER 4: CONFLUENCE SCORING & EXPLAINABILITY ENGINE            |
|  - Multi-Factor Confluence Score (0 - 100) with Dynamic Regime Weights  |
|  - Collinearity Attenuation: Prevents correlated vote inflation         |
|  - Evidence Tree Generator: Detailed "Why / Risk / Invalidation" Rationale|
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|          LAYER 5: PHASE 50 ACTIONABLE DECISION & RISK ENGINE            |
|  - Pre-Entry Revalidation with Anti-Whipsaw Hysteresis                  |
|  - Dynamic Entry Envelopes (Timeframe & Volatility Scaled)              |
|  - Zero-Trust Risk Gate: Minimum 1.2:1 R:R & Macroeconomic Event Filter |
|  - Status Transitions: WATCH -> ENTER_NOW -> IN_POSITION -> RESOLVED   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                 LAYER 6: APIS & FRONTEND COMMAND CENTER                 |
|  - REST Endpoints: /api/v1/analysis/*                                   |
|  - React 19 Frontend: Real-time telemetry, confluence gauges,           |
|    SMC / structure cards, backtest analytics, and explanation modals    |
+-------------------------------------------------------------------------+
```

---

## 2. Core Python Type Definitions & Schemas

All structures are modeled using strictly-typed Python dataclasses and Pydantic models with UTC datetime handling.
- `SwingPoint`: `(asset, timeframe, index, timestamp_utc, timestamp_ist, price, swing_type, confirmed)`
- `StructureEvent`: `(asset, timeframe, event_type, direction, price, timestamp_utc, timestamp_ist, source_candle, confirmation_candle, strength, invalidation_price)`
- `OrderBlock`: `(id, asset, timeframe, block_type, direction, price_high, price_low, created_at_utc, strength, touch_count, mitigation_pct, invalidation_price, status)`
- `FairValueGap`: `(id, asset, timeframe, direction, gap_high, gap_low, gap_size, atr_normalized_size, created_at_utc, fill_pct, is_filled, status)`
- `LiquidityLevel`: `(asset, timeframe, level_type, price, tolerance_pct, created_at_utc, is_swept, sweep_timestamp_utc)`
- `SessionState`: `(session_name, is_active, is_killzone, session_start_utc, session_end_utc, session_high, session_low, session_range, session_volatility)`
- `ConfluenceResult`: `(total_score, breakdown, regime, direction, confidence, why_summary, invalidation_triggers)`
