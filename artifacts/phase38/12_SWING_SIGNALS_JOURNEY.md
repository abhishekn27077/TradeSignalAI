# Phase 38 Artifact 12: Swing Signals Journey

## Architecture
- Endpoint: `GET /api/v1/signals/swing`
- Multi-day holding horizon evaluation (24h to 72h).
- Higher timeframe confluence: D1/H4 trend alignment verified before generation.
- Zero-Trust validation requires wider Stop Loss buffers to accommodate intrabar volatility without prematurely stopping out valid long-term setups.
