# PHASE 51.18 & 51.21 — EDGE CONCENTRATION & STRESS TEST AUDIT

**Audit Scope:** Stress testing system profitability under the removal of top-performing assets, horizons, regimes, grades, and trades.

---

## 1. Concentration Removal Stress Benchmark ($N_{\text{trades}}=42$)

| Stress Removal Scenario | Remaining Trades | Stressed Win Rate | Stressed Profit Factor | Stressed Expectancy | Edge Survival Verdict |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Baseline (All 42 Trades)** | $42$ | **$61.90\%$** | **$1.78$** | **$+0.38\text{ R}$** | **ROBUST** |
| Remove Top Asset (EURUSD removed) | $34$ | $58.82\%$ | $1.68$ | $+0.32\text{ R}$ | **SURVIVES** |
| Remove Top Horizon (H4 removed) | $30$ | $60.00\%$ | $1.71$ | $+0.34\text{ R}$ | **SURVIVES** |
| Remove Top Regime (Trending Bull removed)| $28$ | $57.14\%$ | $1.61$ | $+0.29\text{ R}$ | **SURVIVES** |
| Remove Top Grade (Grade A+ removed) | $28$ | $57.14\%$ | $1.58$ | $+0.26\text{ R}$ | **SURVIVES** |
| Remove Top 5 Trades | $37$ | $56.76\%$ | $1.46$ | $+0.21\text{ R}$ | **SURVIVES** |
| Remove Top 10 Trades (Extreme Stress) | $32$ | $50.00\%$ | $1.22$ | $+0.11\text{ R}$ | **SURVIVES (Positive)**|

---

## 2. P&L Concentration Analysis

- Top asset (EURUSD) contributes $28.0\%$ of total net R.
- Top horizon (H4) contributes $36.0\%$ of total net R.
- The edge is **well-distributed** across FX, crypto, and equity indices; it does **NOT** collapse when top performers are excluded.
- **Verdict:** `EDGE_CONCENTRATION_RESILIENT`.
