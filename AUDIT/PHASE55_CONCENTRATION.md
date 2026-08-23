# PHASE 55 — CONCENTRATION AUDIT AT CHECKPOINT N=50

**Audit Phase:** Phase 55 — Concentration & Subgroup Analysis  
**Date (UTC):** 2026-08-23T09:15:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  
**Sample Size:** $N = 50$ Realized Trades  

---

## 1. Top Trade Ablation

| Ablation Scenario | Remaining Trades | Net Win R | Net Loss R | Net Profit Factor | Net Expectancy | Edge Retained? |
|:---|:---|:---|:---|:---|:---|:---|
| **Baseline ($N=50$)** | 50 | +38.35R | -21.25R | **1.8047** | **+0.3420R** | YES |
| **Remove Top 1 Trade** | 49 | +37.05R | -21.25R | **1.7435** | **+0.3224R** | YES |
| **Remove Top 3 Trades** | 47 | +34.45R | -21.25R | **1.6212** | **+0.2809R** | YES |
| **Remove Top 5 Trades** | 45 | +31.85R | -21.25R | **1.4988** | **+0.2356R** | YES |
| **Remove Top 10 Trades**| 40 | +25.35R | -21.25R | **1.1929** | **+0.1025R** | YES |

---

## 2. Asset Concentration Breakdown ($N=50$)

| Asset | Total Trades | Wins | Losses | Win Rate | Net PF | Governance Tier |
|:---|:---|:---|:---|:---|:---|:---|
| **EURUSD** | 8 | 6 | 2 | 75.00% | 3.25 | EXPLORATORY ($N < 100$) |
| **XAUUSD** | 7 | 5 | 2 | 71.43% | 2.76 | EXPLORATORY ($N < 100$) |
| **BTCUSD** | 6 | 5 | 1 | 83.33% | 5.35 | EXPLORATORY ($N < 100$) |
| **GBPUSD** | 6 | 3 | 3 | 50.00% | 1.25 | EXPLORATORY ($N < 100$) |
| **USDJPY** | 5 | 2 | 3 | 40.00% | 0.81 | EXPLORATORY ($N < 100$) |
| **AUDUSD** | 5 | 3 | 2 | 60.00% | 1.63 | EXPLORATORY ($N < 100$) |
| **USDCAD** | 5 | 2 | 3 | 40.00% | 0.83 | EXPLORATORY ($N < 100$) |
| **NAS100** | 4 | 2 | 2 | 50.00% | 1.18 | EXPLORATORY ($N < 100$) |
| **ETHUSD** | 4 | 3 | 1 | 75.00% | 3.28 | EXPLORATORY ($N < 100$) |

*Mandate: In accordance with Phase 55 governance, all subgroup findings remain labeled EXPLORATORY.*
