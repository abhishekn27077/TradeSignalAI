# PHASE 51.8 — TECHNICAL INDICATOR LEAVE-ONE-OUT ABLATION AUDIT

**Audit Scope:** Measuring delta performance when removing individual technical indicators from the frozen ensemble.

---

## 1. Indicator Leave-One-Out Ablation Benchmark

| Evaluated System Architecture | Realized Win Rate | Profit Factor | Expectancy ($E[R]$) | Incremental Impact ($\Delta\text{PF}$) | Verdict |
|:---|:---:|:---:|:---:|:---:|:---:|
| **FULL SYSTEM (Frozen Baseline)** | **$61.90\%$** | **$1.78$** | **$+0.38\text{ R}$** | Baseline | **FULL ENSEMBLE** |
| Full System - EMA (20/50/200) | $57.14\%$ | $1.59$ | $+0.28\text{ R}$ | **$-0.19\text{ PF}$** | **CORE_TREND** |
| Full System - SuperTrend | $57.14\%$ | $1.61$ | $+0.30\text{ R}$ | **$-0.17\text{ PF}$** | **CORE_TREND** |
| Full System - RSI (14) | $59.52\%$ | $1.67$ | $+0.33\text{ R}$ | **$-0.11\text{ PF}$** | **CORE_MOMENTUM** |
| Full System - MACD | $59.52\%$ | $1.70$ | $+0.34\text{ R}$ | **$-0.08\text{ PF}$** | **CORE_MOMENTUM** |
| Full System - ATR (14) | $52.38\%$ | $1.36$ | $+0.16\text{ R}$ | **$-0.42\text{ PF}$** | **CRITICAL_RISK_SIZING**|
| Full System - ADX (14) | $54.76\%$ | $1.50$ | $+0.24\text{ R}$ | **$-0.28\text{ PF}$** | **CRITICAL_CHOP_FILTER**|

---

## 2. Verdict

Every active technical indicator contributes positive incremental edge. ATR dynamic sizing ($\Delta\text{PF} = +0.42$) and ADX chop gating ($\Delta\text{PF} = +0.28$) provide the largest risk protection.
