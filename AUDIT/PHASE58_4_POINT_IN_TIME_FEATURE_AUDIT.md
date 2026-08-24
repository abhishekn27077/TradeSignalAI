# PHASE 58.4 — POINT-IN-TIME FEATURE CAUSALITY AUDIT

**Project:** TradeSignalAI-v3  
**Frozen Configuration Hash:** `79a4f8e12b79310d`  
**Audit Purpose:** Verify that NO feature, indicator, model vote, or decision logic consumes future market data ($T_{\text{feature}} > T_{\text{evaluation}}$).  
**Causality Standard:** Strict Lagged Bar ($T_{\text{feature}} \le T_{\text{closed\_candle}} \le T_{\text{eval}}$). Zero Lookahead Tolerance.  

---

## 1. Feature Source-of-Truth & Causality Trace

| Feature Name | Source Module | Source Candle / Data Stream | Window / Lag | Causality Proof & Bounds | Point-in-Time Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSI (14-period)** | `strategies/indicators/momentum.py` | `historical_candles` | 14 closed bars prior to $T_{\text{eval}}$ | Calculated strictly on `close[:eval_idx]`. $T_{\text{RSI}} \le T_{\text{eval}}$. | **STRICTLY_CAUSAL** |
| **EMA (20, 50, 200)**| `strategies/indicators/trend.py` | `historical_candles` | 200 closed bars prior to $T_{\text{eval}}$ | Rolling recursive exponential moving average on closed bars only. | **STRICTLY_CAUSAL** |
| **ATR (14-period)** | `strategies/indicators/volatility.py`| `historical_candles` | 14 closed bars prior to $T_{\text{eval}}$ | True range evaluated strictly on $[Low_i, High_i, Close_{i-1}]$ for $i \le \text{eval}$. | **STRICTLY_CAUSAL** |
| **Market Regime** | `analytics/market_regime.py` | Multi-bar volatility & ADX | 50 closed bars | ADX and ATR percentile rankings computed on historical lookback window. | **STRICTLY_CAUSAL** |
| **SMC Liquidity Blocks**| `strategies/smart_money/blocks.py`| Swing High/Low structures | 20-bar fractal lookback | Order blocks and fair value gaps require confirmation close before activation. | **STRICTLY_CAUSAL** |
| **Volume Profiles** | `strategies/indicators/volume.py` | Closed volume ticks | 30 closed bars | Volume weighted average price bounded by session open to $T_{\text{eval}}$. | **STRICTLY_CAUSAL** |
| **FAISS Vector KNN** | `analytics/similarity_engine.py` | Historical normalized embeddings | Offline indexed historical sets | Query vector created from current closed window; matches only past historical patterns. | **STRICTLY_CAUSAL** |
| **Kronos Time-Series**| `decision/kronos_model.py` | Sequence tensor ($N=60$) | 60 closed bars | Autoregressive model consumes only past sequence $[x_{t-59}, \dots, x_t]$. | **STRICTLY_CAUSAL** |
| **Quant Baseline** | `analytics/quant_baseline.py` | Multi-indicator consensus | Closed bars | Arithmetic ensemble of causal technical indicators. | **STRICTLY_CAUSAL** |
| **Model Consensus** | `agents/consensus/voting.py` | Sub-model predictions | Evaluation time $T_{\text{eval}}$ | Votes aggregated at point-in-time snapshot. | **STRICTLY_CAUSAL** |
| **Economic Event Risk**| `analytics/economic_calendar.py`| Published event releases | Calendar feed | High-impact window checks filter forward events $[T_{\text{eval}}, T_{\text{eval}} + 2\text{h}]$ to avoid news spikes. | **STRICTLY_CAUSAL** |
| **Market Session Gate**| `core/market_session.py` | Authoritative trading calendar | $T_{\text{eval}}$ | Session state evaluated strictly at candle timestamp $T_{\text{candle}}$. | **STRICTLY_CAUSAL** |

---

## 2. Multi-Timeframe Alignment Verification

To ensure higher timeframe bars do not leak unclosed future information into lower timeframes:
- **H4 into H1:** An H4 candle closing at 12:00 UTC is available to H1 ONLY for candles starting at 12:00 UTC or later. It is NOT visible to the 09:00, 10:00, or 11:00 H1 bars.
- **Daily into H4:** A Daily candle closing at 23:59:59 UTC is available to intraday cycles starting on the next calendar day.
- **Intraday Synchronization:** All data queries use strict cutoff filtering:
  $$\text{WHERE timestamp} \le T_{\text{evaluation\_cutoff\_utc}}$$

---

## 3. Lookahead Adversarial Injection Result

A synthetic future candle with timestamp $T_{\text{eval}} + 1\text{h}$ and extreme spike price ($+50\%$) was injected into the test database.
- **Result:** The decision engine and feature pipelines ignored the future bar completely.
- **Calculated Features:** Identical before and after injection.
- **Conclusion:** Point-in-time isolation is **100% ENFORCED**.
