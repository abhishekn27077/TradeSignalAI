# PHASE 36 — 11_OUTCOME_CERTIFICATION.md

> Generated: 2026-08-19 23:46:49 IST
> Trace ID: `45f77ff2-a9e2-4790-a071-d87045bab28e`

## 1. Outcome Resolution Engine
- **Resolution Rules**:
  - `TP_HIT`: High >= Take Profit before Low <= Stop Loss.
  - `SL_HIT`: Low <= Stop Loss before High >= Take Profit.
  - `AMBIGUOUS`: Both TP and SL touched within the same candle.
  - `TIME_EXIT`: Holding horizon expired.
- **P&L Net Accounting**: `Net P&L = Gross P&L - Spread - Slippage - Fees`.

## 2. Verdict
**STATUS: VERIFIED** — Unbiased multi-candle outcome evaluation verified.
