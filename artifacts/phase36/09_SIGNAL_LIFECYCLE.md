# PHASE 36 — 09_SIGNAL_LIFECYCLE.md

> Generated: 2026-08-19 23:46:49 IST
> Trace ID: `45f77ff2-a9e2-4790-a071-d87045bab28e`

## 1. State Machine Transitions

```
DETECTED -> ANALYZING -> APPROVED -> ACTIVE -> [TP_HIT | SL_HIT | TIME_EXIT | EXPIRED | AMBIGUOUS] -> COMPLETED
```

## 2. Guard Verifications
- **Duplicate Signal Guard**: SHA-256 hash of `(asset, timeframe, direction, candle_timestamp, strategy)` prevents duplicate generation.
- **Illegal Transitions**: Invalid state transitions (e.g. `DETECTED -> COMPLETED` or `REJECTED -> APPROVED`) are strictly rejected by the model validator.

## 3. Verdict
**STATUS: VERIFIED** — Signal lifecycle integrity fully operational.
