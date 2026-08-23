# PHASE 56 — TRADE & ASSET CONCENTRATION AT N=75

**Audit Phase:** Phase 56 — Concentration Ablation  
**Date (UTC):** 2026-08-23T14:45:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Sample Size:** $N = 75$ Realized Trades  

---

## 1. Top Trade Removal Ablation ($N=75$)

| Ablation Scenario | Remaining Trades | Net Win R | Net Loss R | Net Profit Factor | Net Expectancy | Edge Retained? |
|:---|:---|:---|:---|:---|:---|:---|
| **Baseline ($N=75$)** | 75 | +57.70R | -32.35R | **1.7836** | **+0.3380R** | YES |
| **Remove Top 1 Trade** | 74 | +56.40R | -32.35R | **1.7434** | **+0.3250R** | YES |
| **Remove Top 3 Trades** | 72 | +53.80R | -32.35R | **1.6631** | **+0.2979R** | YES |
| **Remove Top 5 Trades** | 70 | +51.20R | -32.35R | **1.5827** | **+0.2693R** | YES |
| **Remove Top 10 Trades**| 65 | +44.70R | -32.35R | **1.3818** | **+0.1900R** | YES ($\text{PF} > 1.35$) |

---

## 2. Asset Breakdown ($N=75$)

| Asset | Total Trades ($N$) | Wins | Losses | Win Rate | Net PF | Classification |
|:---|:---|:---|:---|:---|:---|:---|
| **EURUSD** | 12 | 9 | 3 | 75.00% | 3.25 | EXPLORATORY ($N < 100$) |
| **XAUUSD** | 10 | 7 | 3 | 70.00% | 2.58 | EXPLORATORY ($N < 100$) |
| **BTCUSD** | 9 | 8 | 1 | 88.89% | 8.85 | EXPLORATORY ($N < 100$) |
| **GBPUSD** | 9 | 5 | 4 | 55.56% | 1.38 | EXPLORATORY ($N < 100$) |
| **USDJPY** | 8 | 4 | 4 | 50.00% | 1.10 | EXPLORATORY ($N < 100$) |
| **USDCAD** | 8 | 4 | 4 | 50.00% | 1.12 | EXPLORATORY ($N < 100$) |
| **AUDUSD** | 7 | 3 | 4 | 42.86% | 0.82 | EXPLORATORY ($N < 100$) |
| **ETHUSD** | 6 | 4 | 2 | 66.67% | 2.45 | EXPLORATORY ($N < 100$) |
| **NAS100** | 6 | 3 | 3 | 50.00% | 1.20 | EXPLORATORY ($N < 100$) |

*Mandate: All subgroup conclusions remain EXPLORATORY.*
