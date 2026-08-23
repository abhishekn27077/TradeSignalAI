# PHASE 53 — HORIZON SEPARATION & SAMPLE GOVERNANCE

---

## 1. Independent Horizon Datasets

The 4 trading horizons are maintained as strictly independent evaluation datasets:

| Horizon | Total Signals | Realized Trades ($N$) | Wins / Losses | Win Rate (Point) | Realized Net PF | Expectancy ($R$) | Governance Classification |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **H1 (Intraday)** | 64 | 24 | 15 / 9 | 62.50% | 1.76 | +0.32R | `INSUFFICIENT_SAMPLE` ($N < 30$) |
| **H4 (Swing Momentum)** | 38 | 12 | 8 / 4 | 66.67% | 1.94 | +0.48R | `INSUFFICIENT_SAMPLE` ($N < 30$) |
| **SWING (Multi-Day)** | 16 | 4 | 2 / 2 | 50.00% | 1.55 | +0.14R | `INSUFFICIENT_SAMPLE` ($N < 30$) |
| **DAILY (Macro)** | 10 | 2 | 1 / 1 | 50.00% | 1.50 | +0.10R | `INSUFFICIENT_SAMPLE` ($N < 30$) |
| **AGGREGATE (ALL)** | **128** | **42** | **26 / 16** | **61.90%** | **1.78** | **+0.30R to +0.38R** | **`EARLY_FORWARD_EVIDENCE`** |

---

## 2. Horizon Governance Invariants

1. **No Horizon Pooling for Subgroup Claims:** Claims regarding horizon superiority (e.g. "H4 is best") cannot pool data across other horizons.
2. **Exploratory Label:** Because all 4 horizons individually possess $N < 30$, all horizon-specific rankings are classified as **`EXPLORATORY_ONLY`**.
3. **Zero Optimization:** Horizon parameters, lookbacks, and thresholds are strictly frozen.
