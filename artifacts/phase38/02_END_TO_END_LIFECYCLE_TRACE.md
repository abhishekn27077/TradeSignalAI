# Phase 38 Artifact 02: End-to-End Signal Lifecycle Trace

## Lifecycle State Pipeline
```mermaid
flowchart TD
    A[Market Closed Candle] --> B[Feature Extraction & Quant Baseline]
    B --> C[Multi-Model Ensemble & Kronos Mini]
    C --> D{Consensus >= 65% & R:R >= 1.5?}
    D -- No --> E[NO_VALID_SETUP / REJECTED]
    D -- Yes --> F[Risk Gate Approval & Sizing]
    F --> G[SignalLifecycleModel Inserted - ACTIVE]
    G --> H[OutcomeEngine Continuous Monitor]
    H --> I{Subsequent Closed Candle Evaluation}
    I -- TP Breached --> J[TP_HIT + Net P&L]
    I -- SL Breached --> K[SL_HIT + Net P&L]
    I -- Both Breached in Same Candle --> L[AMBIGUOUS]
    I -- Expiry Reached --> M[TIME_EXIT at Candle Close]
    J & K & L & M --> N[Database Updated: COMPLETED & WS Broadcast]
```

## Stage Verification
1. **Candle Ingestion**: Real Binance/Forex rates fetched via `market_service`.
2. **Deterministic Hash**: SHA-256 hash generated on `(asset, timeframe, candle_ts, direction, entry, sl, tp)` prevents duplicate signal generation.
3. **Outcome Resolution**: `OutcomeEngine.resolve()` checks intermediate closed candles before expiry, preventing false pending states.
4. **WebSocket Sync**: `signal_outcome_updated` event dispatched to all connected clients immediately upon resolution.
