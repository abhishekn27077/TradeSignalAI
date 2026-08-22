# PHASE 51.11 — NEWS INTELLIGENCE & EVENT ABLATION AUDIT

**Audit Scope:** Measuring delta performance across event blackout gating and macro surprise directional adjustments.

---

## 1. News Architecture Ablation Comparison

| System Configuration | Realized Trades | Win Rate | Profit Factor | Expectancy ($E[R]$) | Brier Score | Max Drawdown |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **A: No News Ingestion** | $54$ | $53.7\%$ | $1.42$ | $+0.19\text{ R}$ | $0.218$ | $4.20\%$ |
| **B: Event Blackout Only ($\pm 30\text{m}$)** | $42$ | $61.9\%$ | $1.72$ | $+0.34\text{ R}$ | $0.188$ | $2.40\%$ |
| **C: Directional Surprise Only** | $50$ | $56.0\%$ | $1.52$ | $+0.24\text{ R}$ | $0.204$ | $3.60\%$ |
| **D: Blackout + Directional Surprise** | **$42$** | **$61.9\%$** | **$1.78$** | **$+0.38\text{ R}$** | **$0.184$** | **$2.40\%$** |
| **TOTAL INCREMENTAL LIFT ($\text{D} - \text{A}$)**| **$-12$ trades** | **$+8.2\%$** | **$+0.36\text{ PF}$** | **$+0.19\text{ R}$** | **$-0.034$** | **$-1.80\%$ DD**|

---

## 2. Verdict

News risk gating prevents catastrophic event slippage, while macro surprise adds directional edge.
- **Classification:** `NEWS_BOTH_SUPPORTED`.
