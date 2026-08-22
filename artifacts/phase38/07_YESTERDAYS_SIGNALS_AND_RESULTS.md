# Phase 38 Artifact 07: Yesterday's Signals & Outcomes

## UI & Architecture
- Direct access via the **Yesterday's Results** tab in `TodaysSignals.tsx`.
- Backend Endpoint: `GET /api/v1/signals/yesterday`
- Query logic uses exact IST previous day window:
  `start_utc = 2 days ago 18:30:00 UTC`, `end_utc = yesterday 18:30:00 UTC`.
- Outcome Visibility:
  - `TP_HIT`: Green highlight with realized Net P&L.
  - `SL_HIT`: Red highlight with realized risk deduction.
  - `TIME_EXIT`: Neutral highlight with exit price at candle close.
  - `AMBIGUOUS`: Amber warning stating both TP and SL were touched in the same bar.
  - `EXPIRED`: Unfilled/expired trade.
- Zero-Trust empty state when no signals were generated yesterday.
