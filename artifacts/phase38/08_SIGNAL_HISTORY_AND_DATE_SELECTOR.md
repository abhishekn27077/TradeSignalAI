# Phase 38 Artifact 08: Signal History & Date Selector Integration

## Component Architecture (`frontend/src/components/signals/DateSelector.tsx`)
- Presets: `Today`, `Yesterday`, `Last 7 Days`, `Last 30 Days`, `Custom Range`.
- Custom Start / End Date pickers with instant trigger.
- Integration in `SignalHistory.tsx`:
  - Time Range Filter (7d / 30d / custom).
  - Asset Filter (`ALL`, `BTCUSD`, `ETHUSD`, `SOLUSD`, `EURUSD`, `GBPUSD`, `USDJPY`, `SPX500`, `NAS100`, `XAUUSD`).
  - Phase 35 Ablation Mode Selector (`ALL`, `MODE_A`, `MODE_B`, `MODE_C`).
- Full lifecycle ledger displays historical gross moves, friction costs, and net realized P&L.
