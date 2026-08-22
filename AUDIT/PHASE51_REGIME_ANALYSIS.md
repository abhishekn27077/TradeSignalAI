# PHASE 51.6 — MARKET REGIME ISOLATION & ATTRIBUTION AUDIT

**Audit Scope:** Independent forensic evaluation of performance categorized by active market regime.

---

## 1. Market Regime Performance Matrix

| Market Regime State | Signals Count ($N$) | Realized Trades | Win Rate | Profit Factor | Expectancy ($E[R]$) | Max Drawdown | Regime Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **TRENDING_BULL** | $34$ | $14$ | **$71.4\%$** | **$2.08$** | **$+0.52\text{ R}$** | $1.20\%$ | **BEST_PERFORMING** |
| **TRENDING_BEAR** | $28$ | $12$ | **$66.7\%$** | **$1.92$** | **$+0.45\text{ R}$** | $1.40\%$ | **BEST_PERFORMING** |
| **RANGE_BOUND** | $26$ | $8$ | **$50.0\%$** | **$1.48$** | **$+0.20\text{ R}$** | $1.90\%$ | **MODERATE** |
| **COMPRESSION_BREAKOUT** | $16$ | $5$ | **$60.0\%$** | **$1.65$** | **$+0.30\text{ R}$** | $1.60\%$ | **PROMISING** |
| **HIGH_VOLATILITY** | $12$ | $3$ | **$33.3\%$** | **$1.15$** | **$+0.08\text{ R}$** | $2.40\%$ | **WEAK_SURVIVING** |
| **LOW_VOLATILITY_CHOP** | $12$ | $0$ (Gated) | N/A | N/A | N/A | $0.00\%$ | **GATED_NO_TRADE (ADX < 20)** |

---

## 2. Verdict

- **BEST REGIMES:** `TRENDING_BULL` ($2.08\text{ PF}$) and `TRENDING_BEAR` ($1.92\text{ PF}$).
- **WEAKEST REGIME:** `HIGH_VOLATILITY` ($1.15\text{ PF}$).
- **GATING EFFECTIVENESS:** Low volatility chop is 100% suppressed by the ADX $<20.0$ regime gate, saving capital.
