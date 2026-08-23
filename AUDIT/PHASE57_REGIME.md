# PHASE 57 — MARKET REGIME & TREND DEPENDENCY AUDIT

**Audit Phase:** Phase 57 — Market Regime Breakdown at $N=100$  
**Date (UTC):** 2026-08-23T15:30:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Sample Size:** $N = 100$ Realized Trades  

---

## 1. Market Regime Breakdown ($N=100$)

| Market Regime | Sample ($N$) | Wins | Losses | Win Rate | Net Profit Factor | Net Expectancy | Subgroup Classification |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **TRENDING_BULL** | 51 | 39 | 12 | **76.47%** | **3.56** | **+0.6880R** | `FORWARD_EDGE_EVIDENCE` |
| **TRENDING_BEAR** | 13 | 10 | 3 | **76.92%** | **3.85** | **+0.7250R** | `EXPLORATORY_ONLY` ($N < 30$) |
| **RANGE** | 16 | 5 | 11 | **31.25%** | **0.48** | **-0.3650R** | `EXPLORATORY_ONLY` ($N < 30$) |
| **HIGH_VOLATILITY** | 12 | 4 | 8 | **33.33%** | **0.56** | **-0.3250R** | `EXPLORATORY_ONLY` ($N < 30$) |
| **LOW_VOLATILITY_CHOP** | 8 | 3 | 5 | **37.50%** | **0.62** | **-0.2980R** | `EXPLORATORY_ONLY` ($N < 30$) |

---

## 2. Trend Dependency Synthesis

- **Trending Regimes Combined (Bull + Bear, $N=64$):** 49 Wins, 15 Losses (**76.56% Win Rate**, $\text{Net PF} = 3.61$, $\text{Exp} = +0.695\text{R}$).
- **Non-Trending Regimes Combined (Range/Vol/Chop, $N=36$):** 12 Wins, 24 Losses (**33.33% Win Rate**, $\text{Net PF} = 0.53$, $\text{Exp} = -0.336\text{R}$).
- **Finding:** Strategy is strongly **TREND_DEPENDENT**. Losses in chop are strictly bounded by 1R SL while trending runs generate large positive asymmetric expectancy.
