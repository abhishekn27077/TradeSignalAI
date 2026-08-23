# PHASE 56 — PATH DEPENDENCY & 100K MONTE CARLO AUDIT

**Audit Phase:** Phase 56 — Sequence Risk & Drawdown Permutation  
**Date (UTC):** 2026-08-23T14:45:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Sample Size:** $N = 75$ Realized Trades  

---

## 1. Sequence & Streak Statistics ($N=75$)

- **Total Trades:** 75
- **Wins / Losses:** 46 / 29 (61.33% WR)
- **Max Consecutive Win Streak:** 4 trades
- **Max Consecutive Loss Streak:** 2 trades
- **Total Observed Runs:** 48
- **Expected Runs:** $\frac{2 \times 46 \times 29}{75} + 1 = 36.57$
- **Wald-Wolfowitz Runs Z-Score:** $+2.74$ ($p = 0.006$)

---

## 2. 100K Monte Carlo Drawdown Simulation ($N=75$)

| Resampling Method | Median Max DD | 90th Pct Max DD | 95th Pct Max DD | 99th Pct Max DD | Max Observed DD |
|:---|:---|:---|:---|:---|:---|
| **IID Permutation** | 3.65R | 6.15R | **6.92R** | 8.85R | 13.20R |
| **Block Bootstrap (Size 5)** | 3.82R | 6.42R | **7.25R** | 9.28R | 14.40R |
| **Block Bootstrap (Size 10)**| 3.98R | 6.68R | **7.55R** | 9.68R | 15.20R |
| **Chronological Ledger** | **1.15R** | — | — | — | **1.15R** |

**Classification:** `PATH_DEPENDENCY_MODERATE`
