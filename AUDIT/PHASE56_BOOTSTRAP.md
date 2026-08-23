# PHASE 56 — 100,000 BOOTSTRAP RESAMPLING REPORT

**Audit Phase:** Phase 56 — Efron Bootstrap at $N=75$  
**Date (UTC):** 2026-08-23T14:45:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Iterations:** 100,000 (Random Seed = 42)  

---

## 1. Bootstrap Distribution Percentiles ($N=75$)

| Metric | Median | 2.5th Pct (Lower 95%) | 5.0th Pct (Lower 90%) | 95.0th Pct (Upper 90%) | 97.5th Pct (Upper 95%) |
|:---|:---|:---|:---|:---|:---|
| **Win Rate** | **61.33%** | 50.67% | 52.00% | 70.67% | 72.00% |
| **Profit Factor** | **1.7820** | **1.1150** | **1.1920** | **2.9850** | **3.2850** |
| **Net Expectancy** | **+0.3382R** | **+0.0620R** | **+0.1045R** | **+0.5750R** | **+0.6150R** |

### Key Bootstrap Observations:
1. **$P(\text{PF} > 1.0) = \mathbf{99.12\%}$** across 100,000 resamples.
2. **$P(\text{Expectancy} > 0.0) = \mathbf{99.08\%}$**.
3. The 95% bootstrap lower bound for Net PF is **1.1150**, confirming profit factor edge robustness.
