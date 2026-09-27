# TRADE SIGNAL AI-v3 — PHASE 76 BASELINE SPECIFICATION

**Baseline Date:** 2026-09-27  
**Baseline Git Commit SHA:** `b9b7a13467b494c46e67432852bb2fa7952f3463`  
**Execution Standard:** Zero-Trust Paper-Only Protocol  
**Operational Status:** **PAPER-ONLY RESEARCH MODE** (`REAL_MONEY_ENABLED = False`)

---

## 1. Runtime Environment & Dependency Versions

- **Operating System:** Windows 11 (AMD64)
- **Python Version:** `Python 3.14.3` (tags/v3.14.3:323c59a, Feb 3 2026)
- **Node.js Version:** `v24.18.0`
- **Core Python Frameworks:**
  - `fastapi`: `0.135.2`
  - `pydantic`: `2.12.5`
  - `pandas`: `3.0.5`
  - `numpy`: `2.4.1`
  - `ta`: `0.11.0`
  - `uvicorn`: `0.34.0`
  - `pytest`: `9.1.1`
  - `passlib`: `1.7.4`
- **Frontend Frameworks:**
  - `react`: `18.3.1`
  - `typescript`: `5.5.3`
  - `vite`: `8.1.5`
  - `tailwindcss`: `3.4.1`

---

## 2. Core Strategy Configuration & Multi-Model Layer Weights

TradeSignalAI-v3 evaluates 8 specialized evidence layers to synthesize trading decisions:

| Layer # | Model Name | Role | Default Weight | Status Invariant |
|---|---|---|---|---|
| **1** | **Quant Baseline** | Momentum, Trend, Overbought/Oversold | 0.20 | AVAILABLE |
| **2** | **Kronos Transformer** | Deep Time-Series Prediction Engine | 0.20 | AVAILABLE |
| **3** | **FAISS Vector Memory** | Historical Analog Matcher | 0.00 | EXPLICIT UNAVAILABLE (zero weight dilution) |
| **4** | **Time Pattern Seasonality** | Intraday / Session / Day-of-Week | 0.10 | AVAILABLE ($N \ge 1000$ historical bars) |
| **5** | **Market Structure & SMC** | Order Blocks, FVG, Liquidity Sweeps | 0.20 | AVAILABLE |
| **6** | **Macro Context** | Economic Calendar & Interest Rates | 0.10 | AVAILABLE |
| **7** | **News Sentiment** | Real-time sentiment & high-impact risk | 0.05 | AVAILABLE |
| **8** | **AI Analyst Synthesis** | Cross-layer reasoning & validation | 0.15 | AVAILABLE |

### Consensus Formula:
$$\text{Consensus Direction} = \text{ArgMax} \left(\sum w_i \cdot \mathbb{I}(\text{dir}_i = D)\right)$$
$$\text{Consensus Confidence} = \frac{\sum_{i \in \text{Available}} w_i \cdot c_i}{\sum_{i \in \text{Available}} w_i}$$

---

## 3. Technical Indicator Periods & Parameters

All quantitative indicators are computed in `app/analytics/feature_engine.py`:
- **Relative Strength Index (RSI):** Period = 14, Wilder RMA smoothing.
- **Moving Average Convergence Divergence (MACD):** Fast = 12, Slow = 26, Signal = 9 (Exponential).
- **Exponential Moving Averages (EMA):** Periods = 20, 50, 200.
- **Simple Moving Averages (SMA):** Periods = 20, 50.
- **Average True Range (ATR):** Period = 14, Wilder RMA smoothing.
- **Bollinger Bands:** Window = 20, Multiplier = 2.0 standard deviations.
- **Average Directional Index (ADX):** Window = 14, Trend threshold = 25.0.
- **Stochastic Oscillator:** Fast $\%K = 14$, Slow $\%D = 3$, Smooth $= 3$.
- **Commodity Channel Index (CCI):** Window = 20.
- **Fair Value Gaps (FVG):** Strict 3-bar imbalance pattern.
- **Pivots & Swings:** Confirmation window $k = 2$ bars (strictly causal).

---

## 4. Risk & Order Sizing Parameters

Enforced fail-closed in `app/risk/portfolio_risk_manager.py`:
- **Risk Per Trade:** 1.0% to 2.0% of virtual paper equity.
- **Maximum Aggregate Portfolio Risk:** 5.0% of virtual paper equity.
- **Minimum Risk-to-Reward Ratio ($RR$):** $\ge 1.5$ (Trades with $RR < 1.5$ are rejected with `RR_BELOW_MINIMUM`).
- **Target Risk-to-Reward ($RR$):** 2.0 to 3.0 depending on market regime.
- **Inverted SL/TP Guard:** Buy orders with $\text{SL} \ge \text{Entry}$ or $\text{TP} \le \text{Entry}$ reject immediately.
- **NaN / Inf / Zero Sizing Guard:** Rejects immediately.

---

## 5. Signal Qualification & Decision Policy

- **`TAKE_NOW` (QUALIFIED):**
  - Market must be `OPEN`.
  - Consensus Confidence $\ge 0.65$.
  - Contributing Available Models $\ge 5$.
  - Model Agreement $\ge 60\%$.
  - Data Age within timeframe freshness limit (< 120s for 1m, < 600s for 5m, < 1800s for 15m).
  - High Impact Event Risk = `False`.
  - Risk-to-Reward $\ge 1.5$.
- **`WATCHLIST`:**
  - Directional Bias confirmed ($0.55 \le \text{Confidence} < 0.65$).
  - OR Market Closed with technically aligned setup awaiting session open.
- **`NO_TRADE`:**
  - Confidence $< 0.55$ OR any gating failure (`MARKET_CLOSED`, `STALE_MARKET_DATA`, `HIGH_EVENT_RISK`, `INSUFFICIENT_MODEL_EVIDENCE`).

---

## 6. Supported Assets & Timeframes

### Core Assets (9 Total):
1. `EURUSD` — Forex Interbank (Primary: MT5)
2. `GBPUSD` — Forex Interbank (Primary: MT5)
3. `USDJPY` — Forex Interbank (Primary: MT5)
4. `AUDUSD` — Forex Interbank (Primary: MT5)
5. `XAUUSD` — Metals / Spot Gold (Primary: MT5)
6. `NAS100` — CME Index CFD (Primary: MT5)
7. `SPX500` — CME Index CFD (Primary: MT5)
8. `BTCUSD` (`BINANCE:BTCUSDT`) — Crypto (Primary: Binance Native API)
9. `ETHUSD` (`BINANCE:ETHUSDT`) — Crypto (Primary: Binance Native API)

### Supported Timeframes:
`1m`, `5m`, `15m`, `30m`, `1H`, `2H`, `4H`, `12H`, `1D`, `SWING`.

---

## 7. Data Providers & Truth Hierarchy

1. **Forex, Metals, Index CFDs:**
   - **Primary Live Source:** MetaTrader 5 Terminal IPC (`MT5DataProvider`).
   - **Offline / Disconnected Behavior:** Fails closed; returns `DATA_UNAVAILABLE`.
2. **Cryptocurrency:**
   - **Primary Live Source:** Binance Native REST / WebSocket (`BinanceCryptoDataProvider`).
   - **Offline / Disconnected Behavior:** Fails closed; returns `DATA_UNAVAILABLE`.
3. **Database (SQLite):**
   - Strictly secondary audit log and candle cache.
   - **Absolute Rule:** SQLite data can **never** masquerade as live market data.
4. **Fallback Prices:** Zero synthetic, mock, or random fallback prices exist in production pipelines.

---

## 8. Market Session & Trading Calendar Rules

Enforced in `app/core/market_session.py`:
- **Forex (EURUSD, GBPUSD, USDJPY, AUDUSD):** Opens Sunday 22:00 UTC, Closes Friday 21:00 UTC. Closed on weekends.
- **Crypto (BTCUSD, ETHUSD):** Open 24/7 continuous.
- **Metals & Indices (XAUUSD, NAS100, SPX500):** Mon-Fri market hours with daily/weekend closures.
- **Timezone:** Indian Standard Time (`Asia/Kolkata`, UTC+5:30) for display and logging.
- **Closed Market Invariant:** Actionable BUY/SELL trade signals are strictly prohibited when the relevant market is closed.

---

## 9. Prospective Ledger Invariants

- **Immutable $T_0$ Predictions:** Entry price, stop loss, take profit, confidence, and feature hashes cannot be modified retrospectively.
- **Conservative Same-Candle Ambiguity Rule:** If both TP and SL are touched in the same market bar, the trade is resolved as `LOST` (SL hit first).
- **Zero Lookahead:** All features at prediction time $T_0$ depend solely on information $t \le T_0$.
- **Permanent Real-Money Lockout:** `REAL_MONEY_ENABLED = False`, `BROKER_EXECUTION_ENABLED = False`, `EXECUTION_MODE = "DEMO"`.
