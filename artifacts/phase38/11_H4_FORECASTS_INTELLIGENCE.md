# Phase 38 Artifact 11: H4 Multi-Model Forecasts & Observability Matrix

## Architecture & Scan Matrix
- Endpoint: `GET /api/v1/signals/h4-intelligence`
- Monitored Assets: `BTCUSD`, `ETHUSD`, `SOLUSD`, `EURUSD`, `GBPUSD`, `USDJPY`, `SPX500`, `NAS100`, `XAUUSD`
- Columns in live matrix:
  - **Asset & Current Price**
  - **Regime**: Market volatility & trend structure
  - **Quant**: Rule-based momentum/mean-reversion score
  - **Kronos**: Deep time-series forecast & confidence
  - **FAISS**: Vector database analog matches & directional bias
  - **Consensus**: Weighted ensemble score (≥65% required)
  - **Risk Gate**: Spread, volatility, and exposure check
  - **Final**: `SIGNAL_READY` or specific rejection reason (e.g. `RR_LOW`, `SPREAD_HIGH`, `CONSENSUS_LOW`)
