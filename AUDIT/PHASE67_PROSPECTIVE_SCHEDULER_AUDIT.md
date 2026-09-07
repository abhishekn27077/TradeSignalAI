# AUDIT: PHASE 67 PROSPECTIVE SIGNAL SCHEDULER & AUTOMATIC DUE RESOLUTION
**System:** TradeSignalAI-v3  
**Module:** `app/runtime/prospective_signal_scheduler.py`  
**Endpoints:** `POST /api/v1/signals/run-cycle`, `POST /api/v1/signals/resolve-due`  

---

## 1. Automated 11-Step Prospective Signal Generation Cycle

The prospective scheduler executes an 11-step zero-lookahead cycle:

```
[STEP 1: Market Data Ingestion (t <= T0)]
                   ↓
[STEP 2: Canonical Snapshot Creation (Hash: 79a4f8e12b79310d)]
                   ↓
[STEP 3: Data Quality & Age Verification (< 2.0s)]
                   ↓
[STEP 4: Candidate Signal Generation (9 Assets x 9 Timeframes)]
                   ↓
[STEP 5: Multi-Model Consensus & Bayesian Calibration]
                   ↓
[STEP 6: 13-Stage Zero-Trust Filtration]
                   ↓
[STEP 7: Composite Conviction Ranking (Top 1, 3, 5, 10)]
                   ↓
[STEP 8: Freezing & Journaling to Immutable Signal Journal]
                   ↓
[STEP 9: Telemetry & Event Bus Distribution (SIGNAL_PUBLISHED)]
                   ↓
[STEP 10: Multi-Timeframe Telegram-Style Live Feed Update]
                   ↓
[STEP 11: Automatic Due Signal Resolution (Post-T0 Evaluation)]
```

---

## 2. Post-T0 Outcome Evaluation & MFE/MAE

- Open paper signals are tracked chronologically post-$T_0$.
- As new candles arrive:
  - **Take Profit First:** Mark `WON`, record positive Net R, record Maximum Favorable Excursion (MFE).
  - **Stop Loss First:** Mark `LOST`, record negative Net R, record Maximum Adverse Excursion (MAE).
  - **Simultaneous / Ambiguous Intrabar Hit:** Conservatively marked `AMBIGUOUS` with standard stop loss friction penalty.
  - **Expiry Reached Without TP/SL:** Settle at closing price (`TIME_EXIT`).
