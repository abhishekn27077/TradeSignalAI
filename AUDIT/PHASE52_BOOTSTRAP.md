# PHASE 52 — BOOTSTRAP CONFIDENCE ANALYSIS

**Seed:** `52` (deterministic)  
**Trade Model:** Heterogeneous R-distribution matching PF=1.78

---

## §52.6 — Profit Factor Bootstrap

| Iterations | 2.5% | 5.0% | 50.0% | 95.0% | 97.5% | Lower 95% > 1.0 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 10,000 | 0.9326 | 1.0409 | 1.7799 | 3.1724 | 3.5983 | ❌ NO |
| 50,000 | 0.9400 | 1.0430 | 1.7841 | 3.2188 | 3.6496 | ❌ NO |
| 100,000 | 0.9409 | 1.0453 | 1.7843 | 3.2095 | 3.6406 | ❌ NO |

> [!CAUTION]
> **The 2.5th percentile PF is consistently below 1.0** (~0.94 across all bootstrap sizes). This means the 95% confidence interval for PF **includes values below breakeven**. The edge cannot be declared statistically significant at the 95% level with N=42 trades.

### Key Observations
- The **5th percentile** (90% CI lower bound) is consistently **above 1.0** (~1.04), providing moderate confidence
- The **median PF** is stable at ~1.78 across all bootstrap sizes, confirming numerical stability
- The **right tail** extends to PF ~3.5–3.6, indicating high positive skew

---

## §52.7 — Expectancy Bootstrap

| Iterations | 2.5% | 5.0% | 50.0% | 95.0% | 97.5% | Lower 95% > 0 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 10,000 | -0.0361R | +0.0209R | +0.2979R | +0.5632R | +0.6131R | ❌ NO |
| 50,000 | -0.0320R | +0.0222R | +0.2977R | +0.5671R | +0.6170R | ❌ NO |
| 100,000 | -0.0316R | +0.0231R | +0.2974R | +0.5663R | +0.6163R | ❌ NO |

> [!CAUTION]
> **FLAG: `EDGE_UNCERTAIN`**
>
> The 2.5th percentile expectancy is **negative** (~-0.03R) across all bootstrap sizes. This means the 95% CI for expectancy includes zero and slightly negative values. The edge is **not proven** at the 95% confidence level.

### Key Observations
- The **5th percentile** (90% CI lower bound) is **barely positive** (~+0.02R)
- The **median expectancy** is stable at ~+0.30R
- This is **expected behavior** for N=42 — the sample size is simply too small to establish statistical significance at the 95% level
- The edge classification remains `EARLY_FORWARD_EVIDENCE` which is appropriate

---

## Adversarial Verdict

| Claim | Status | Confidence |
|:---|:---:|:---:|
| PF > 1.0 at 95% CI | **NOT CONFIRMED** | 2.5th percentile = 0.94 |
| PF > 1.0 at 90% CI | **SUPPORTED** | 5th percentile = 1.04 |
| Expectancy > 0 at 95% CI | **NOT CONFIRMED** | 2.5th percentile = -0.03R |
| Expectancy > 0 at 90% CI | **MARGINALLY SUPPORTED** | 5th percentile = +0.02R |
| Bootstrap numerical stability | **VERIFIED** | 3 tiers converge |

**Classification: `EDGE_UNCERTAIN` at 95% CI, `MARGINALLY_SUPPORTED` at 90% CI**
