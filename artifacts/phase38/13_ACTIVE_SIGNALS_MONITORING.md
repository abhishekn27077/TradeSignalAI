# Phase 38 Artifact 13: Active Signals Monitoring & Continuous Lifecycle

## Lifecycle Worker (`app/forecast_engine/lifecycle.py`)
- Background Async Loop: Checks unresolved signals every 30 seconds.
- Continuous Resolution: Runs `OutcomeEngine.resolve()` on each active database record.
- Immediate DB Update: When an outcome is determined (`TP_HIT`, `SL_HIT`, `TIME_EXIT`, `AMBIGUOUS`), sets `status="COMPLETED"`, `signal_state=outcome`, `exit_price`, `exit_time`, `net_pnl`, `r_multiple`, `closed_at`.
- Real-time Broadcast: Dispatches `signal_outcome_updated` event to connected WebSocket clients to update UI with 0 page reloads.
