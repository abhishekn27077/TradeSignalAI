# Phase 22.1 — Runtime Architecture Pipeline Trace

**Trace ID:** `RUN-20260822-195240-E2E`  
**Execution Mode:** Canonical Runtime Evaluation (Single Source of Truth)  
**Target Asset:** `EURUSD` | **Timeframe:** `1H`  
**Generated Signal ID:** `SIG-EURUSD-1H-77b312a0`

---

## 1. End-to-End Runtime Pipeline Trace Log

| Stage # | Pipeline Subsystem | Input Data / Params | Subsystem Output | Stage Latency | Status | Provenance / Hash |
|:---:|:---|:---|:---|:---:|:---:|:---|
| **1** | **Live Market Ingestion** | `EURUSD`, `1H`, 80 candles | Primary OHLCV DataFrame ($N=80$) | 14.2 ms | `PASS` | `SNAPSHOT_HASH: a4f8e12b79` |
| **2** | **Data Quality Validation** | Monotonic timestamps, OHLC integrity, volume $\ge 0$ | `DataQualityState.DATA_QUALITY_GOOD` | 1.8 ms | `PASS` | Monotonic: True, Range: Valid |
| **3** | **Multi-Provider Consensus** | Primary vs Secondary feed ($<0.5\%$ max dev) | Deviation: $0.0018\%$, Consensus: Healthy | 3.1 ms | `PASS` | Parallel TV/YF feed sync |
| **4** | **Feature Calculation** | ATR(14), Swing Pivots, EMA(20,50,200), RSI(14) | ATR: $0.00115$, RSI: $58.4$, EMA20 > EMA50 | 4.6 ms | `PASS` | Strictly causal rolling window |
| **5** | **Market Structure & SMC** | Swing pivot detection, Order Blocks, FVGs | Bias: `BULLISH`, Structure Score: $82.5$ | 6.2 ms | `PASS` | Non-repainting pivot lag |
| **6** | **Strategy Ensemble** | 10 Strategy Families across 5 clusters | Supermajority: `BUY` ($80.0\%$), Consensus: $4/5$ | 8.4 ms | `PASS` | Cluster collinearity dampened |
| **7** | **Regime Classifier** | Trend strength, Volatility ratio, ADX | Regime: `TRENDING_BULL` (Score: $78.0$) | 2.5 ms | `PASS` | ADX > 25, ATR Normal |
| **8** | **Confluence Engine** | 6-layer synthesis (Structure, SMC, MTF, SMT) | Total Confluence: $74.2$ / $100$ | 3.8 ms | `PASS` | Actionable threshold ($\ge 65$) Met |
| **9** | **Signal Quality Gating** | Setup grading ($A+, A, B, C, \text{NO\_TRADE}$) | Grade: `A` (16 Rejection Gates Cleared) | 2.1 ms | `PASS` | Spread: $1.0$ pip, Event: Clear |
| **10** | **Risk Budget Engine** | Equity: $\$100,000$, Stop: $20$ pips, ATR: $11.5$ | Allocated: $0.50$ Lots, Risk: $\$100.00$ ($0.10\%$) | 1.9 ms | `PASS` | Drawdown: $0.0\% < 5.0\%$ cap |
| **11** | **Execution Simulator** | Order type: MARKET_BUY, Slippage, Spread | Fill Price: $1.08532$, Spread: $1.2$ pips | 2.4 ms | `PASS` | Simulated fill latency: $15$ ms |
| **12** | **Paper Position Layer** | Paper account state update | Position: `OPEN` (ID: `POS-EURUSD-001`) | 3.5 ms | `PASS` | Parity: Signal = Order = Position |
| **13** | **Revalidation Check** | Continuous spread & data freshness check | State: `VALID_ACTIVE` | 1.2 ms | `PASS` | No adverse news spike |
| **14** | **Outcome Ledger** | Immutable SQLite persistence | Saved to `predictions` & `decision_history` | 5.1 ms | `PASS` | Hash: `8fa3910cd04e` |
| **15** | **Performance Analytics**| Attribution & calibration metrics | Brier: $0.21$, ECE: $0.08$ | 3.9 ms | `PASS` | Live-Shadow partition |

---

## 2. Pipeline Summary

- **Total Execution Latency:** $64.7\text{ ms}$ (Target: $<200\text{ ms}$).
- **Canonical Decision:** `TAKE_TRADE` (Direction: `BUY`, Entry: $1.08532$, SL: $1.08332$, TP: $1.08932$, RR: $1:2.0$).
- **Trace Status:** `RUNTIME_VERIFIED`.
