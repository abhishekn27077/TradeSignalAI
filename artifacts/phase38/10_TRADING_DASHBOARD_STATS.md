# Phase 38 Artifact 10: Trading Dashboard Core Performance Integration

## UI & Architecture (`frontend/src/pages/TradingDashboard.tsx`)

### 1. Header Information Strip
- Real-time IST Date & Time clock.
- Market session indicator (Asian / London / New York / Closed).
- Live backend API status & WebSocket connection status.
- Countdown to next H4 candle boundary.

### 2. Strongest Signal Hero Card / NO_VALID_SETUP Matrix
- If active actionable signal exists: Displays full entry, SL, TP, consensus, and model checks.
- If no trade passes Zero-Trust filters: Displays `NO_VALID_SETUP` card with live 9-asset multi-model intelligence scan matrix.

### 3. Core Daily Performance Grid (5 Cards)
1. **Today's Signals**: Total count generated today (IST).
2. **Today's Wins**: Count of trades that achieved `TP_HIT`.
3. **Today's Losses**: Count of trades that hit `SL_HIT`.
4. **Today's Net P&L**: Net realized P&L after friction deductions in USD.
5. **Active Trades**: Count of trades currently in progress.

### 4. Recent Signal Results Table
- Real-time view of latest 5 resolved trades displaying asset, direction, entry, exit, outcome badge, and net P&L.
