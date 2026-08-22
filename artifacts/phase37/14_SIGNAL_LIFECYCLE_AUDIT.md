# 14 — Signal Lifecycle Audit & State Machine Integrity
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Canonical State Transitions
The prediction lifecycle state machine follows a strict finite state progression:
```
NO_VALID_SETUP
      │ (Setup conditions met & candle closes)
      ▼
   ACTIVE
      │
      ├─── Price hits Take Profit ───► TP_HIT
      ├─── Price hits Stop Loss   ───► SL_HIT
      └─── Max hold time expires  ───► EXPIRED
```

---

## 2. Forbidden State Purge
- All non-canonical string fallbacks (e.g. `'UNKNOWN'`, `'N/A'`) have been purged across backend and frontend tables.
- Outcome resolution is tracked continuously against live tick feeds.
- Status: **PASSED & VERIFIED**.
