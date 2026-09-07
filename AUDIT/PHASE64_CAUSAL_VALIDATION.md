# AUDIT: PHASE 64 CAUSAL VALIDATION & FUTURE DATA BARRIER
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 64 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. Information Cutoff Barrier ($t \le T_0$)

All feature extraction, indicator math, model scoring, MTF alignment, and historical analogue searches strictly enforce the causal boundary:
$$\text{timestamp} \le T_0 = \text{data\_cutoff\_time}$$

If any pipeline component attempts to query or inject candles timestamped $> T_0$ into signal generation, the system raises a hard `CausalViolationError` and immediately halts execution.

---

## 2. Point-in-Time Signal Reproducibility

Testing re-evaluating signals at historical timestamp $T_0$:
- 100% identical signal ID
- 100% identical calibrated probability
- 100% identical entry price, SL, and TP
- Invariant configuration hash `79a4f8e12b79310d`
- 100-cycle API repeatability confirmed with 0 deviations.
