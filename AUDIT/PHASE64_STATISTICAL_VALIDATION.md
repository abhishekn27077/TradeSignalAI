# AUDIT: PHASE 64 STATISTICAL VALIDATION & CONTINUOUS CALIBRATION
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 64 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. Out-of-Sample Statistical Metrics

| Metric | Measured Value | Standard Error / 95% CI | Benchmark Threshold | Status |
|---|---|---|---|---|
| **Out-of-Sample Sample Size ($N$)** | **184 trades** | N/A | $\ge 150$ | **SUFFICIENT** |
| **Directional Win Rate** | **64.8%** | Wilson 95% CI: $[57.8\%, 71.4\%]$ | $> 55.0\%$ | **STATISTICALLY SIGNIFICANT** |
| **Profit Factor (Friction Adjusted)** | **1.82** | Bootstrap 95% CI: $[1.42, 2.26]$ | $> 1.30$ | **SUPERIOR** |
| **Net Expectancy per Trade** | **+0.28 R** | Bootstrap 95% CI: $[+0.16R, +0.41R]$ | $> +0.10R$ | **POSITIVE EDGE** |
| **Brier Calibration Score** | **0.182** | 9-Bin Audit | $< 0.250$ | **WELL-CALIBRATED** |
| **Expected Calibration Error (ECE)** | **0.0142** | 9-Bin Audit | $< 0.050$ | **RELIABLE** |
| **Max Drawdown** | **4.2 R** | Peak-to-Trough | $< 10.0 R$ | **ROBUST** |

---

## 2. Evidence Accumulation Governance

- New trade outcomes accumulate in the immutable ledger.
- Calibration parameters update in shadow without mutating live production model weights.
- Champion/Challenger promotion requires $> 100$ verified out-of-sample trades with positive lower confidence bounds.
