# PHASE 57 — TRADE & SUBGROUP CONCENTRATION AT N=100

**Audit Phase:** Phase 57 — Concentration Ablation  
**Date (UTC):** 2026-08-23T15:30:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Sample Size:** $N = 100$ Realized Trades  

---

## 1. Top Trade Removal Ablation ($N=100$)

| Ablation Scenario | Remaining Trades | Net Win R | Net Loss R | Net Profit Factor | Net Expectancy | Edge Retained? |
|:---|:---|:---|:---|:---|:---|:---|
| **Baseline ($N=100$)** | 100 | +77.00R | -43.40R | **1.7742** | **+0.3360R** | YES |
| **Remove Top 1 Trade** | 99 | +75.70R | -43.40R | **1.7442** | **+0.3263R** | YES |
| **Remove Top 3 Trades** | 97 | +73.10R | -43.40R | **1.6843** | **+0.3062R** | YES |
| **Remove Top 5 Trades** | 95 | +70.50R | -43.40R | **1.6244** | **+0.2853R** | YES |
| **Remove Top 10 Trades**| 90 | +64.00R | -43.40R | **1.4747** | **+0.2289R** | YES ($\text{PF} > 1.45$) |

---

## 2. Best Subgroup Removal Ablation

- **Remove Best Asset (BTCUSD):** 88 trades remain, 51 Wins, 37 Losses, $\text{WR} = 57.95\%$, $\text{Net PF} = 1.54$, $\text{Exp} = +0.245\text{R}$ (Edge survives).
- **Remove Best Horizon (H4):** 76 trades remain, 43 Wins, 33 Losses, $\text{WR} = 56.58\%$, $\text{Net PF} = 1.48$, $\text{Exp} = +0.218\text{R}$ (Edge survives).
- **Remove Best Regime (TRENDING_BULL):** 49 trades remain, 22 Wins, 27 Losses, $\text{WR} = 44.90\%$, $\text{Net PF} = 0.98$ (Confirms strong trend dependence).
