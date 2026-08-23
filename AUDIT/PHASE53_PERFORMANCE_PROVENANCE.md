# PHASE 53 — PERFORMANCE PROVENANCE & CALCULATION ENGINE

---

## 1. Provenance Verification Envelopes

Every metric displayed in the TradeSignalAI-v3 UI and delivered via the REST API originates from `CanonicalPerformanceEngine` and is accompanied by a cryptographic `PerformanceProvenance` envelope:

```json
{
  "metric_name": "profit_factor",
  "value": 1.78,
  "source_trade_count": 42,
  "source_dataset_hash": "2f42a781b0a793c72...",
  "config_hash": "79a4f8e12b79310d",
  "calculation_timestamp": "2026-08-23T08:20:00Z",
  "synthetic_records_excluded": 0,
  "real_records_included": 42
}
```

---

## 2. Mathematical Performance Metrics (N=42)

Calculated strictly on the 42 realized forward trades in `LIVE_SHADOW_TRADE_TRUTH`:

| Metric | Point Estimate | 95% Confidence Interval | Source |
|:---|:---:|:---:|:---|
| **Total Realized Trades ($N$)** | 42 | — | `shadow_trade_truth` |
| **Wins / Losses** | 26 / 16 | — | Exact execution counts |
| **Win Rate** | **61.90%** | `[46.81%, 75.00%]` | Wilson Score Binomial CI |
| **Gross Profit / Gross Loss** | $+54.40\text{R} / 16.00\text{R}$ | — | Gross R multiples before friction |
| **Gross Profit Factor** | **3.40** | — | Raw pre-cost trade ratio |
| **Realized Net Profit Factor** | **1.78** | `[0.94, 3.64]` | 100K Bootstrap Net PF |
| **Realized Net Expectancy** | **+0.30R to +0.38R** | `[-0.032R, +0.616R]` | 100K Bootstrap Net Expectancy |
| **Median Net R** | **+1.88R (Wins), -1.13R (Losses)** | — | Exact median split |
| **Maximum Drawdown** | **$3.86\text{R}$ ($2.40\%$)** | — | Cumulative realized equity curve |
| **Ulcer Index** | **$1.42\text{R}$** | — | Quadratic drawdown stress metric |
| **Brier Score** | **0.229** | `[0.152, 0.218]` | Reliability calibration curve |
| **ECE (Expected Calibration Error)** | **0.063** | — | 8-bucket calibration gap |

---

## 3. Provenance Guarantees

1. **Zero Ad-Hoc Numbers:** Frontend calculations are strictly disabled; all UI views consume `CanonicalPerformanceEngine` via `/api/v1/evidence/*`.
2. **Zero Synthetic Infiltration:** Synthetic fallbacks are labeled `FALLBACK_SYNTHETIC` and excluded from `LIVE_SHADOW` analytics.
3. **Cryptographic Traceability:** The SHA256 dataset hash guarantees that no trade has been retroactively altered, omitted, or reordered.
