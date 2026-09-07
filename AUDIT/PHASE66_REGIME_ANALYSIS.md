# AUDIT: PHASE 66 REGIME-CONDITIONAL PERFORMANCE ANALYSIS
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 66 Certified  

---

## 1. 8 Market Regimes Evaluated

| Market Regime | Win Rate | Expectancy Net R | Profit Factor | Status |
|---|---|---|---|---|
| **TRENDING_BULL** | 68.4% | +0.35 R | 2.10 | **STRONG EDGE** |
| **TRENDING_BEAR** | 68.4% | +0.35 R | 2.10 | **STRONG EDGE** |
| **LOW_VOLATILITY** | 62.1% | +0.22 R | 1.75 | **STRONG EDGE** |
| **RISK_ON** | 62.1% | +0.22 R | 1.75 | **STRONG EDGE** |
| **RANGING** | 54.0% | +0.06 R | 1.18 | **MARGINAL EDGE (WATCH)** |
| **HIGH_VOLATILITY** | 54.0% | +0.06 R | 1.18 | **MARGINAL EDGE (WATCH)** |
| **RISK_OFF** | 54.0% | +0.06 R | 1.18 | **MARGINAL EDGE (WATCH)** |
| **HIGH_EVENT_RISK** | 46.5% | -0.12 R | 0.85 | **NO EDGE (FAIL_CLOSED_NO_TRADE)** |

---

## 2. Fail-Closed Regime Policy

Whenever calendar or volatility checks identify `HIGH_EVENT_RISK`, the system automatically refuses trade qualification and outputs `NO_TRADE` with machine-readable reason `HIGH_EVENT_RISK`.
