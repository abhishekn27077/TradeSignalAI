# Phase 38 Artifact 06: Today's Signals Journey

## UI & Architecture (`frontend/src/pages/signals/TodaysSignals.tsx`)
- Tabbed Navigation: Switch easily between **Today's Signals** and **Yesterday's Results**.
- Real-time IST Date Display: Shows exact IST day stamp.
- Comprehensive Table Columns:
  1. Time (IST)
  2. Asset & Direction badge
  3. Entry Zone & SL / TP targets
  4. Confidence & Consensus Score
  5. Current Lifecycle Status (`ACTIVE`, `TP_HIT`, `SL_HIT`, `TIME_EXIT`, `AMBIGUOUS`)
  6. Net P&L (USD)
  7. Audit Action Button (opens 5-tab deep inspection modal)
- Zero-Trust Empty State: Displays honest `NO_SIGNALS_TODAY` with dynamic explanation of why no trade passed risk/consensus filters, without inventing mock entries.
