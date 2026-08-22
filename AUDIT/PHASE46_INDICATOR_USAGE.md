# PHASE 46.4 — INDICATOR USAGE & RUNTIME CALL-GRAPH AUDIT

**Audit Objective:** Prove with code execution paths whether each indicator genuinely reaches `CanonicalDecisionEngine.evaluate_market()`.

---

## 1. End-to-End Dependency Call Graph

```
┌────────────────────────────────────────────────────────┐
│                   MARKET DATA SNAPSHOT                 │
│              OHLCV Candle Stream (1H, 4H, 1D)          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               TECHNICAL & SMC FEATURE ENGINES          │
│   Trend: EMA (20/50/200), SuperTrend (10/3), SMA       │
│   Momentum: RSI (14), MACD (12/26/9)                   │
│   Volatility & Risk: ATR (14), Bollinger Bands         │
│   Structure: BOS, CHoCH, Order Blocks, FVG, Sweeps     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                 10 STRATEGY FAMILY VOTING              │
│       SmartMoney, Momentum, Trend, Breakout, MeanRev   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                STRATEGY ENSEMBLE ENGINE                │
│    Calculates Weighted Direction & Confidence Score    │
│    Applies 1/√K Cluster Collinearity Dampener          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             CANONICAL DECISION ENGINE (SSOT)           │
│   Enforces Minimum R:R (1:1.50+), Drawdown Breaker,    │
│   Currency Exposure Cap, and Consensus Gate (≥60%)     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Indicator Consumption & Influence Matrix

| Indicator | Implementation Function | Downstream Caller | Directional Impact | Confidence Impact | Risk / SL / TP Impact | Runtime Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|
| **EMA 20/50/200** | `calculate_ema()` | `TrendFollowStrategy` | **YES** | **YES** | NO | `IMPLEMENTED_AND_USED` |
| **SuperTrend** | `calculate_supertrend()`| `SupertrendBreakout` | **YES** | **YES** | Trailing SL | `IMPLEMENTED_AND_USED` |
| **RSI (14)** | `calculate_rsi()` | `MomentumOscillator` | **YES** | **YES** | NO | `IMPLEMENTED_AND_USED` |
| **MACD (12/26/9)**| `calculate_macd()` | `MacdCrossover` | **YES** | **YES** | NO | `IMPLEMENTED_AND_USED` |
| **ATR (14)** | `calculate_atr()` | `DynamicRiskSizer` | NO | **YES** | **YES (SL/TP Distances)**| `IMPLEMENTED_AND_USED` |
| **ADX (14)** | `calculate_adx()` | `RegimeClassifier` | NO | **YES (Filter)** | NO | `IMPLEMENTED_AND_USED` |
| **BOS / CHoCH** | `detect_structure_breaks()`| `SmartMoneyStructure` | **YES** | **YES** | **YES (Entry Price)** | `IMPLEMENTED_AND_USED` |
| **Order Blocks** | `identify_order_blocks()` | `SmartMoneyLiquidity` | **YES** | **YES** | **YES (Entry / SL)** | `IMPLEMENTED_AND_USED` |
| **FVG Sweeps** | `detect_liquidity_sweeps()`| `LiquiditySweepStrategy`| **YES** | **YES** | **YES (TP Target)** | `IMPLEMENTED_AND_USED` |
