# PHASE 36 — 16_FRONTEND_DATA_LINEAGE.md

> Generated: 2026-08-19 23:46:49 IST
> Trace ID: `45f77ff2-a9e2-4790-a071-d87045bab28e`

## 1. Data Lineage Mapping

```
UI Component                -> API Endpoint             -> Backend Service       -> Source of Truth
------------------------------------------------------------------------------------------------------
Today's Best Trade Card     -> /api/v1/signals/live     -> StrategyManager       -> DB / Live Stream
Active Signals Table        -> /api/v1/signals/active   -> Database Session      -> SignalLifecycleModel
Signal History Table        -> /api/v1/signals/history  -> Database Session      -> SignalLifecycleModel
Candle Countdown Clock      -> /api/v1/signals/predict  -> CandleClock           -> Real Market Time
AI Consensus Breakdown      -> /{id}/ai-consensus   -> Database Session      -> model_trace / snapshot
```

## 2. Verdict
**STATUS: VERIFIED** — Full data lineage traced from UI to database.
