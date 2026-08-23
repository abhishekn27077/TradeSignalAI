# PHASE 52 — CONFIDENCE CALIBRATION & SIGNAL GRADE FORENSICS

---

## §52.28 — Confidence Calibration

| Bucket | Predicted P | N | Actual Freq | Gap | Tiny N |
|:---|:---:|:---:|:---:|:---:|:---:|
| 0.50–0.55 | 0.525 | 8 | 0.500 | 0.025 | No |
| 0.55–0.60 | 0.575 | 6 | 0.500 | 0.075 | No |
| 0.60–0.65 | 0.625 | 10 | 0.600 | 0.025 | No |
| 0.65–0.70 | 0.675 | 7 | 0.714 | 0.039 | No |
| 0.70–0.75 | 0.725 | 5 | 0.800 | 0.075 | No |
| 0.75–0.80 | 0.775 | 3 | 0.667 | 0.108 | **YES** |
| 0.80–0.85 | 0.825 | 2 | 0.500 | 0.325 | **YES** |
| 0.85–1.00 | 0.900 | 1 | 1.000 | 0.100 | **YES** |

| Metric | Value | Status |
|:---|:---:|:---:|
| Brier Score | **0.229** | ⚠️ Higher than reported 0.184 |
| ECE | **0.063** | ⚠️ Higher than reported 0.076 |
| Tiny-N Buckets | 3/8 | ⚠️ 37.5% of buckets unreliable |

> [!WARNING]
> **Brier Score Discrepancy:** Independent computation yields Brier = 0.229, which is worse than the reported 0.184. This suggests the reported Brier may use a different calculation method (e.g., per-signal rather than per-trade, or different bucket boundaries).

> [!CAUTION]
> **3 of 8 confidence buckets have N < 5**, making their reliability questionable. The 0.80–0.85 bucket shows the largest gap (0.325) between predicted and actual probability. **Do not call confidence "calibrated" based on this data.**

**Classification:** `PARTIALLY_VERIFIED` — reasonable calibration in lower buckets (0.50–0.75), unreliable in upper buckets (0.75–1.00).

---

## §52.29 — Signal Grade Forensics

| Grade | N | Wins | Losses | Win Rate | PF | Expectancy | 95% CI (WR) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| A+ | 7 | 5 | 2 | 71.43% | 2.14 | +0.56R | [29.0%, 96.3%] |
| A | 15 | 9 | 6 | 60.00% | 1.72 | +0.32R | [32.3%, 83.7%] |
| B | 14 | 8 | 6 | 57.14% | 1.38 | +0.18R | [28.9%, 82.3%] |
| C | 6 | 4 | 2 | 66.67% | 1.48 | +0.24R | [22.3%, 95.7%] |

### Monotonicity Check

| Comparison | PF | WR | Monotonic |
|:---|:---:|:---:|:---:|
| A+ > A | 2.14 > 1.72 | 71.43% > 60.00% | ✅ YES |
| A > B | 1.72 > 1.38 | 60.00% > 57.14% | ✅ YES |
| B > C | 1.38 < **1.48** | 57.14% < **66.67%** | ❌ **BROKEN** |

> [!CAUTION]
> **Monotonicity is BROKEN at B vs C.** Grade C (N=6) has higher WR and PF than Grade B (N=14). This is likely a small-sample artifact (N=6 for Grade C is `INSUFFICIENT_SAMPLE`).
>
> **Classification: `MONOTONIC_POINT_ESTIMATE_ONLY`** — monotonicity holds for A+/A/B but fails at C due to tiny sample.

### Confidence Interval Overlap

All grade-level CIs **heavily overlap**, meaning no individual grade's win rate is statistically distinguishable from any other at the 95% level. The monotonicity in point estimates is not statistically significant.

**Verdict:** Signal grading provides reasonable ranking but should not be treated as statistically validated quality stratification with current sample sizes.
