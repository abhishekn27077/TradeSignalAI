# Phase 38 Artifact 09: 5-Section Deep Signal Audit Drawer

## Architecture (`frontend/src/components/signals/SignalDetailPanel.tsx`)

### Tab 1: Signal Details
- Signal ID, Asset, Direction, Timeframe, Created Time (IST/UTC), Status badge.
- Entry Zone, Initial Stop Loss, Primary Target (TP1), Risk-to-Reward ratio, Expected Move %.

### Tab 2: Intelligence Snapshot
- Multi-model consensus score (e.g. 78.4%).
- Individual Model Breakdown:
  - Quant Baseline direction & score.
  - Kronos Mini direction & probability.
  - FAISS Historical Analog matches & analog win rate.
  - Time Pattern alignment & statistical edge.
- Market Regime classification (e.g. `BULL_TRENDING`, `VOLATILE_RANGE`).

### Tab 3: Risk Trace
- Trade Quality Grade (A+, A, B, C, F).
- Position sizing recommendation (Lot size).
- Maximum Drawdown threshold & Risk Gate approvals.

### Tab 4: Outcome & Costs
- Resolution status (`ACTIVE`, `TP_HIT`, `SL_HIT`, `TIME_EXIT`, `AMBIGUOUS`, `EXPIRED`).
- Exit price & Exit timestamp (IST).
- Realized Gross P&L vs Deductions:
  - Spread Cost
  - Slippage Cost
  - Broker Commission Fees
- Realized Net P&L & Final R-Multiple.

### Tab 5: Audit Trace
- Immutable SHA-256 Signal Hash.
- Upstream model provenance, latency logs, and database creation timestamp.
