# PHASE 56 — MARKET REGIME & TREND DEPENDENCY AUDIT

**Audit Phase:** Phase 56 — Market Regime Breakdown  
**Date (UTC):** 2026-08-23T14:45:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Sample Size:** $N = 75$ Realized Trades  

---

## 1. Regime Performance Breakdown ($N=75$)

| Market Regime | Total Trades | Wins | Losses | Win Rate | Net Profit Factor | Net Expectancy | Classification |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **TRENDING_BULL** | 38 | 29 | 9 | 76.32% | 3.52 | +0.6850R | EXPLORATORY |
| **TRENDING_BEAR** | 10 | 8 | 2 | 80.00% | 4.25 | +0.7850R | EXPLORATORY |
| **RANGE** | 12 | 4 | 8 | 33.33% | 0.52 | -0.3450R | EXPLORATORY |
| **HIGH_VOLATILITY** | 9 | 3 | 6 | 33.33% | 0.58 | -0.3120R | EXPLORATORY |
| **LOW_VOLATILITY_CHOP** | 6 | 2 | 4 | 33.33% | 0.55 | -0.3450R | EXPLORATORY |

---

## 2. Trend Dependency Analysis

- **Trending Regimes (Bull + Bear, $N=48$):** 37 Wins, 11 Losses (77.08% Win Rate, $\text{Net PF} = 3.68$)
- **Non-Trending Regimes (Range/Vol/Chop, $N=27$):** 9 Wins, 18 Losses (33.33% Win Rate, $\text{Net PF} = 0.54$)
- **Observation:** Confirms Phase 52 finding: the strategy is strongly **TREND_DEPENDENT**. In non-trending regimes, risk controls and ADX chop filters successfully limit loss magnitude to 1R per trade while trending momentum captures full multi-R extensions.
- **Rule:** Regime filters remain 100% frozen; no post hoc pruning permitted.
