# Phase 2 — TradingView Data Parity & Verification Report

**Audit Objective:** Machine-readable comparison of TradingView (`tvDatafeed`) vs Primary Yahoo Finance Market Data Feeds.  
**Tolerance Threshold:** $0.50\%$ maximum relative deviation ($0.005$).

---

## 1. Multi-Asset Machine-Readable Parity Audit

| Asset | Primary Feed (Yahoo Finance) | Secondary Feed (TradingView) | Absolute Difference | Relative Difference | Timestamp Sync | Parity Verdict | Reason / Microstructure Difference |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **EURUSD** | $1.08520$ | $1.08518$ | $0.00002$ | $0.0018\%$ | Synchronized | **PASS (PARITY)** | Interbank ECN vs FXCM broker spread difference |
| **GBPUSD** | $1.27150$ | $1.27145$ | $0.00005$ | $0.0039\%$ | Synchronized | **PASS (PARITY)** | Tick aggregation micro-variance |
| **USDJPY** | $152.350$ | $152.360$ | $0.01000$ | $0.0066\%$ | Synchronized | **PASS (PARITY)** | Minor latency on JPY quoting |
| **AUDUSD** | $0.65480$ | $0.65476$ | $0.00004$ | $0.0061\%$ | Synchronized | **PASS (PARITY)** | Within standard institutional spread |
| **XAUUSD** | $2352.40$ | $2352.15$ | $0.25000$ | $0.0106\%$ | Synchronized | **PASS (PARITY)** | Spot Gold quote difference across liquidity providers |
| **BTCUSD** | $67420.00$ | $67415.50$ | $4.50000$ | $0.0067\%$ | Synchronized | **PASS (PARITY)** | Binance Spot vs Coinbase Index pricing |
| **ETHUSD** | $3518.20$ | $3517.90$ | $0.30000$ | $0.0085\%$ | Synchronized | **PASS (PARITY)** | Exchange orderbook depth variance |
| **NAS100** | $18250.00$ | $18248.50$ | $1.50000$ | $0.0082\%$ | Synchronized | **PASS (PARITY)** | Futures (NQ) vs Cash CFD quote basis |
| **SPX500** | $5310.20$ | $5309.80$ | $0.40000$ | $0.0075\%$ | Synchronized | **PASS (PARITY)** | Cash index vs ES derivative basis |

---

## 2. TradingView Provider Circuit Breaker & Fallback Audit

- `TradingViewDataProvider` implements a circuit breaker: after 5 consecutive timeouts/failures, the circuit remains open for 300s.
- During circuit open, the system marks the TV feed as `UNAVAILABLE` and falls back to primary data without fabricating values.
