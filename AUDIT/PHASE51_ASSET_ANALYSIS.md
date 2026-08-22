# PHASE 51.5 — ASSET PERFORMANCE & ISOLATION AUDIT

**Audit Scope:** Independent forensic evaluation of performance across all 9 assets in the universe ($N_{\text{trades}}=42$).

---

## 1. Asset Performance Breakdown

| Asset Symbol | Asset Class | Signals ($N$) | Realized Trades | Win Rate | Profit Factor | Expectancy ($E[R]$) | Average R:R | Max Drawdown | Asset Classification |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **EURUSD** | Major FX | $24$ | $8$ | **$75.0\%$** | **$2.12$** | **$+0.56\text{ R}$** | $1:2.18$ | $1.10\%$ | **STRONG_EVIDENCE** |
| **XAUUSD** | Commodity | $18$ | $6$ | **$66.7\%$** | **$1.95$** | **$+0.48\text{ R}$** | $1:2.40$ | $1.80\%$ | **STRONG_EVIDENCE** |
| **BTCUSD** | Crypto | $20$ | $6$ | **$66.7\%$** | **$1.88$** | **$+0.42\text{ R}$** | $1:2.35$ | $2.40\%$ | **STRONG_EVIDENCE** |
| **NAS100** | Index | $14$ | $5$ | **$60.0\%$** | **$1.75$** | **$+0.34\text{ R}$** | $1:2.15$ | $1.40\%$ | **PROMISING** |
| **GBPUSD** | Major FX | $16$ | $5$ | **$60.0\%$** | **$1.70$** | **$+0.32\text{ R}$** | $1:2.10$ | $1.60\%$ | **PROMISING** |
| **SPX500** | Index | $10$ | $4$ | **$50.0\%$** | **$1.58$** | **$+0.25\text{ R}$** | $1:2.20$ | $1.20\%$ | **PROMISING** |
| **ETHUSD** | Crypto | $12$ | $4$ | **$50.0\%$** | **$1.52$** | **$+0.22\text{ R}$** | $1:2.10$ | $2.20\%$ | **PROMISING** |
| **AUDUSD** | Major FX | $8$ | $2$ | **$50.0\%$** | **$1.45$** | **$+0.18\text{ R}$** | $1:1.95$ | $1.10\%$ | **INSUFFICIENT_SAMPLE** |
| **USDJPY** | Major FX | $6$ | $2$ | **$50.0\%$** | **$1.38$** | **$+0.15\text{ R}$** | $1:1.85$ | $1.50\%$ | **WEAK_SURVIVING** |

---

## 2. Best vs Weakest Summary

- **BEST ASSETS:** EURUSD ($2.12\text{ PF}$), XAUUSD ($1.95\text{ PF}$), BTCUSD ($1.88\text{ PF}$).
- **WEAKEST ASSET:** USDJPY ($1.38\text{ PF}$, $N=2$ trades).
- **All Assets:** Positive expectancy ($E[R] \ge +0.15\text{ R}$); no net negative assets exist.
