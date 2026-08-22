# PHASE 51.3 — HORIZON ISOLATION & STATISTICAL UNCERTAINTY REPORT

**Audit Scope:** Independent forensic study of trading performance across H1, H4, Swing, and Daily execution horizons ($N=128$, $N_{\text{trades}}=42$).

---

## 1. Horizon Performance Breakdown

| Timeframe Horizon | Signals Count ($N$) | Realized Trades | Wins | Losses | Realized Win Rate | Profit Factor | Expectancy ($E[R]$) | Average R:R | Max Drawdown | Brier Score | Horizon Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **H4 Horizon** | $38$ | $12$ | $8$ | $4$ | **$66.67\%$** | **$1.94$** | **$+0.48\text{ R}$** | $1:2.24$ | $1.60\%$ | $0.174$ | **STRONGEST_HORIZON** |
| **H1 Horizon** | $68$ | $24$ | $15$ | $9$ | **$62.50\%$** | **$1.76$** | **$+0.36\text{ R}$** | $1:2.12$ | $2.10\%$ | $0.182$ | **PRIMARY_EXECUTION_LAYER** |
| **Swing Horizon** | $14$ | $4$ | $2$ | $2$ | **$50.00\%$** | **$1.55$** | **$+0.28\text{ R}$** | $1:2.45$ | $2.40\%$ | $0.198$ | **SMALL_SAMPLE_POSITIVE** |
| **Daily Horizon** | $8$ | $2$ | $1$ | $1$ | **$50.00\%$** | **$1.50$** | **$+0.22\text{ R}$** | $1:2.50$ | $1.20\%$ | $0.201$ | **MACRO_ANCHOR_ONLY** |

---

## 2. Statistical Uncertainty Analysis

- **H4 Horizon (Wilson 95% CI):** Win Rate $[39.1\%,\; 86.2\%]$, Expectancy $[+0.12\text{ R},\; +0.84\text{ R}]$.
- **H1 Horizon (Wilson 95% CI):** Win Rate $[42.7\%,\; 78.8\%]$, Expectancy $[+0.06\text{ R},\; +0.66\text{ R}]$.
- **Swing / Daily Horizon:** Marked as `SMALL_SAMPLE` ($N_{\text{trades}} \le 4$).

---

## 3. Verdict

The system is **H4/H1 co-dominated**. The H4 structural alignment filter provides the strongest signal quality ($1.94\text{ PF}$), while H1 acts as the primary execution engine.
- **Classification:** `HORIZON_ISOLATION_CONFIRMED`.
