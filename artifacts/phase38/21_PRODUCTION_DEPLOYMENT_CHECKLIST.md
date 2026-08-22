# Phase 38 Artifact 21: Production Deployment Checklist

## Pre-Deployment Verification
- [x] OutcomeEngine resolves pre-expiry candle breaches (`TP_HIT`, `SL_HIT`, `TIME_EXIT`, `AMBIGUOUS`).
- [x] Gross to Net P&L deductions verified (spread, slippage, broker fees).
- [x] IST Day boundaries (00:00:00 to 23:59:59 IST) correctly converted to UTC for database queries.
- [x] REST API endpoints (`/today`, `/yesterday`, `/active`, `/history`, `/{signal_id}`, `/dashboard`) return standard schemas.
- [x] UI 5-tab Signal Audit Drawer renders all model consensus, risk traces, and cost breakdowns.
- [x] Trading Dashboard displays live daily performance stats and recent resolved trades.
- [x] Automated pytest test suite passes 100% (15/15 tests).
- [x] Frontend builds with 0 TypeScript/Vite errors.
