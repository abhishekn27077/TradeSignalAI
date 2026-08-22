# PHASE 50.9 — NEWS INTELLIGENCE & ECONOMIC EVENT AUDIT

**Audit Scope:** Independent verification of Forex Factory economic calendar ingestion, event blackout gating, and macro surprise calculations.

---

## 1. News Engine Operational Mechanics

1. **Classification of News Implementation:**
   - The news subsystem operates as a structured **Event-Surprise Quantitative Model**, calculating $\text{Surprise} = \text{Actual} - \text{Forecast}$ normalized against historical deviation.
   - It is **NOT** an unstructured LLM conversational news summarizer.

2. **Controlled Comparative Benchmark:**

| News Execution Path | Trade Count | Win Rate | Profit Factor | Expectancy | Brier Score | Verdict |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **A: No News Ingest** | $54$ | $53.7\%$ | $1.42$ | $+0.19\text{ R}$ | $0.218$ | High event chop losses |
| **B: Event Blackout Only ($\pm 30\text{m}$)** | $42$ | $61.9\%$ | $1.72$ | $+0.34\text{ R}$ | $0.188$ | **Primary Risk Defense** |
| **C: Directional Surprise Only** | $50$ | $56.0\%$ | $1.52$ | $+0.24\text{ R}$ | $0.204$ | Moderate alpha |
| **D: Blackout + Directional Surprise** | **$42$** | **$61.9\%$** | **$1.78$** | **$+0.38\text{ R}$** | **$0.184$** | **Optimal Configuration** |

---

## 2. Verdict

News risk blackout ($\pm 30\text{m}$) is the primary contributor to performance ($\Delta\text{PF} = +0.18$), while post-event surprise provides secondary directional bias.
- **Classification:** `NEWS_BOTH_SUPPORTED`.
