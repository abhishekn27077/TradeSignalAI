# 01 — Repository Audit & System Overview
**Phase 37 Certification: TradeSignalAI-v3**
**Status:** Certified • Clean • Zero-Trust Compliant

---

## 1. Repository Purpose & Architecture
TradeSignalAI-v3 is an enterprise algorithmic trading intelligence engine designed to produce high-probability trade setups across 9 primary global assets (Forex, Crypto, Indices, Commodities) using closed-candle multi-model consensus.

### Core Processing Stack
1. **Market Data Layer:** Live data ingestion via TradingView and Yahoo Finance providers.
2. **Candle Timing Engine:** `CandleClock` calculating precise H4 candle close boundaries in UTC and IST.
3. **Candle Discipline Gate:** Strict enforcement that features and signals are only computed on verified completed candles (zero intra-candle lookahead).
4. **Quantitative Feature Engine:** 50+ institutional & technical indicators (RSI, MACD, Stochastic, ATR, Bollinger, ADX, FVG, Order Blocks, Liquidity Sweeps).
5. **Multi-Model Consensus:**
   - **Kronos-mini Foundation Model (50% Weight):** PyTorch time-series transformer.
   - **Quant Gradient Boosters (40% Total):** HistGradientBoosting (15%), XGBoost (15%), RandomForest (10%).
   - **FAISS Pattern Memory (10% Weight):** Vector similarity retrieval.
6. **Risk Management Engine:** ATR-based Dynamic Stop Loss (1.5x) and Take Profit (3.0x) enforcing strict $R:R \ge 1.50$.
7. **Signal State Machine:** Prediction lifecycle transitions (`NO_VALID_SETUP`, `ACTIVE`, `TP_HIT`, `SL_HIT`, `EXPIRED`).
8. **Delivery & Interface:** FastAPI REST endpoints, WebSocket event stream, and Vite/React Dashboard.

---

## 2. Directory Layout & Module Verification
| Directory / Component | Purpose | Status |
| :--- | :--- | :--- |
| `app/market_data/` | Real-time rate providers & symbol normalizer | Operational |
| `app/core/timing.py` | UTC/IST Candle boundaries & countdown | Operational |
| `app/analytics/feature_engine.py` | 50+ Quantitative technical indicators | Operational (Fixed NaN handling) |
| `app/analytics/consensus_engine.py`| Multi-model aggregation & consensus weights | Operational |
| `app/market_intelligence/h4_engine.py`| Scheduled H4 intelligence scanner | Operational (Loop repaired) |
| `app/api/v1/` | RESTful API endpoints & contracts | Operational (H4 matrix added) |
| `frontend/src/` | React/TypeScript Trading UI | Operational (Contracts synchronized) |
| `scripts/` | Autonomous diagnostic & audit tools | Certified |
| `tests/` | Comprehensive automated test suite | Certified |
