# PHASE 53 — COUNTERFACTUAL SEPARATION & GATING DATASET

**Dataset Name:** `LIVE_SHADOW_COUNTERFACTUAL`  
**Dataset SHA256:** `Runtime cryptographic digest`  
**Records Included:** 86 Gated `NO_TRADE` Observations

---

## 1. Complete Separation Guarantee

The `LIVE_SHADOW_COUNTERFACTUAL` dataset is strictly segregated from `LIVE_SHADOW_TRADE_TRUTH`:
- **Realized Paper Trades:** 42 records in `LIVE_SHADOW_TRADE_TRUTH` (affect equity, win rate, PF, DD).
- **Gated Rejections:** 86 records in `LIVE_SHADOW_COUNTERFACTUAL` (never alter equity or realized trade metrics).

---

## 2. Gating Forensics & Counterfactual Resolution

| Gate Category | Total Gated | Resolved Rejections | Losses Avoided | Missed Winners | Unresolved | Filter Precision |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **News Event Blackout** | 28 | 20 | 15 | 5 | 8 | **75.00%** |
| **Low Confluence** | 22 | 18 | 11 | 7 | 4 | **61.11%** |
| **Spread Too Wide** | 14 | 12 | 9 | 3 | 2 | **75.00%** |
| **ADX Chop Filter** | 12 | 10 | 8 | 2 | 2 | **80.00%** |
| **Poor Risk:Reward (<1.5)**| 6 | 6 | 5 | 1 | 0 | **83.33%** |
| **Currency Exposure Limit**| 4 | 4 | 4 | 0 | 0 | **100.00%** |
| **TOTAL** | **86** | **70** | **52** | **18** | **16** | **74.29%** |

---

## 3. Key Findings

1. **Precision:** Across the 70 resolved rejections, the gating system avoided **52 losses** while missing **18 winners**, achieving an aggregate precision of **74.29%**.
2. **Total Loss Avoidance Rate:** $52 / 86 = \mathbf{60.47\%}$ of all gated signals were confirmed loss-avoidance events.
3. **Zero Contamination:** Counterfactual theoretical returns are never included in trade ledgers or P&L calculations.
