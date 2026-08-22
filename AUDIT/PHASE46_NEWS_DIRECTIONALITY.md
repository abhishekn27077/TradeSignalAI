# PHASE 46.13 — NEWS DIRECTIONALITY VS RISK BLACKOUT AUDIT

**Audit Scope:** Distinguish between `NEWS_USED_FOR_RISK` (circuit breaker blackout) and `NEWS_USED_FOR_DIRECTION` (macroeconomic surprise bias).

---

## 1. Dual-Path News Intelligence Architecture

```
┌────────────────────────────────────────────────────────┐
│             FOREX FACTORY / CALENDAR EVENT             │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌───────────────────────────┐ ┌───────────────────────────┐
│     PATH 1: RISK GATING   │ │   PATH 2: DIRECTION BIAS  │
│  Is release ±30 mins away?│ │  Actual vs Forecast Diff  │
│  If YES: Force NO_TRADE   │ │  Computes currency bias   │
│  (EVENT_RISK_BLACKOUT)    │ │  Feeds Macro AI layer     │
└───────────────────────────┘ └───────────────────────────┘
```

---

## 2. Quantitative Verification of Both Paths

1. **Path 1 — `NEWS_USED_FOR_RISK` (Operational):**
   - Verified that high-impact FOMC, NFP, and CPI releases trigger immediate trade rejection with code `EVENT_RISK_BLACKOUT`.
2. **Path 2 — `NEWS_USED_FOR_DIRECTION` (Operational):**
   - Evaluated post-release macro surprises: positive USD surprises ($+50\text{k}$ NFP) generate a $+0.80$ USD currency strength multiplier, shifting EURUSD ensemble bias to SELL.
- **Verdict:** `NEWS_DIRECTIONALITY_AND_RISK_VERIFIED`.
