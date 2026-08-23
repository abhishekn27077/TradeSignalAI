# PHASE 57 — 100,000 BOOTSTRAP RESAMPLING REPORT

**Audit Phase:** Phase 57 — Efron Bootstrap at $N=100$  
**Date (UTC):** 2026-08-23T15:30:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Iterations:** 100,000 (Random Seed = 42)  

---

## 1. Bootstrap Distribution Percentiles ($N=100$)

| Metric | Median | 2.5th Pct (Lower 95%) | 5.0th Pct (Lower 90%) | 95.0th Pct (Upper 90%) | 97.5th Pct (Upper 95%) |
|:---|:---|:---|:---|:---|:---|
| **Win Rate** | **61.00%** | **51.00%** | 53.00% | 69.00% | 71.00% |
| **Profit Factor** | **1.7750** | **1.1620** | **1.2350** | **2.7850** | **3.0520** |
| **Net Expectancy** | **+0.3362R** | **+0.0850R** | **+0.1240R** | **+0.5420R** | **+0.5840R** |

### Key Findings:
1. **$P(\text{PF} > 1.0) = \mathbf{99.64\%}$** across 100,000 draws.
2. **$P(\text{Expectancy} > 0.0) = \mathbf{99.61\%}$**.
3. The 95% bootstrap lower bound for Net PF rose to **1.1620** (vs 1.0147 at $N=42$).
