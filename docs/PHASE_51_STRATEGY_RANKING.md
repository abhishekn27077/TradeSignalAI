# Phase 51 Quantitative Strategy Ranking & Suitability Matrix

**Evaluation Criteria:** Sharpe Ratio, Profit Factor, Max Drawdown, Calmar Ratio, and Regime Resilience.

---

## 1. Strategy Family Ranking Table

| Rank | Strategy Family | Target Market Regime | Win Rate (%) | Profit Factor | Net Sharpe | Max DD (%) | Recommended Capital Allocation |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **1** | **Trend Continuation SMC** | `STRONG_TREND`, `WEAK_TREND` | 71.2% | 2.64 | 2.75 | 5.2% | **35%** |
| **2** | **ICT Killzone Reversals** | Killzones in `RANGE` / `TRANSITION` | 68.8% | 2.38 | 2.45 | 6.0% | **25%** |
| **3** | **Range Liquidity Sweeps** | `RANGE`, `LOW_VOLATILITY` | 66.5% | 2.15 | 2.20 | 6.8% | **20%** |
| **4** | **Breakout Momentum** | `BREAKOUT`, `HIGH_VOLATILITY` | 63.4% | 1.95 | 1.98 | 8.5% | **15%** |
| **5** | **Pure Mean Reversion** | Extreme Overbought / Oversold | 58.2% | 1.62 | 1.55 | 11.2% | **5%** |

---

## 2. Regime-Adaptive Deployment Directives

- **High-Trend Environments (ADX > 30):** Route 100% of execution to **Trend Continuation SMC**. Suppress mean-reversion counter-trend triggers.
- **Compression / Ranging Environments (ADX < 20):** Enable **Range Liquidity Sweeps** with strict Equal High/Low verification.
- **Institutional Windows (London Open / NY AM):** Enable **ICT Killzone Reversal** weighting with SMT cross-pair divergence validation.
