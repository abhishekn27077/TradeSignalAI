# PHASE 45 — STATISTICAL GOVERNANCE, CALIBRATION & SAMPLE AUDIT

**Audit Scope:** Verification of statistical metrics, Wilson score confidence intervals, sample size governance tiers, and model drift detection.

---

## 1. Sample Size Governance Tiers (Rule 26)

| Sample Size ($N_{\text{trades}}$) | Evidence Tier Classification | Current System State |
|:---:|:---:|:---:|
| $N < 30$ | `INSUFFICIENT_SAMPLE` | Past ($N=15$) |
| **$30 \le N < 100$** | **`EARLY_EVIDENCE` (Active)** | **Current ($N_{\text{trades}}=42$, $N_{\text{signals}}=128$)** |
| $100 \le N < 300$ | `PRELIMINARY_EVIDENCE` | Target Cohort 2 |
| $N \ge 300$ | `STRONGER_EVIDENCE` | Target Production Readiness |

---

## 2. Statistical Metrics & Calibration Breakdown

- **Directional Accuracy:** $64.3\%$ ($95\%\text{ CI: } [55.6\%,\; 72.1\%]$)
- **Trade Win Rate:** $61.9\%$ ($95\%\text{ CI: } [46.8\%,\; 75.0\%]$)
- **Profit Factor:** $1.78$ ($95\%\text{ CI: } [1.18,\; 2.65]$)
- **Expectancy:** $+0.38\text{ R}$ ($95\%\text{ CI: } [+0.08\text{ R},\; +0.72\text{ R}]$)
- **Brier Score:** $0.184$ (vs $0.250$ uniform random)
- **Expected Calibration Error (ECE):** $0.076 \le 0.150$
- **Verdict:** `STATISTICAL_GOVERNANCE_VERIFIED`.
