# PHASE 50.3 — SIGNAL ACCURACY, CONFUSION MATRIX & QUALITY CALIBRATION

**Audit Scope:** Independent classification performance audit on the forward dataset ($N=128$, $N_{\text{trades}}=42$).

---

## 1. 2x2 Directional Confusion Matrix ($N_{\text{trades}} = 42$)

$$\begin{array}{c|cc}
& \text{Actual UP} & \text{Actual DOWN} \\
\hline
\text{Predicted UP (BUY)} & \mathbf{16}\; (\text{TP}) & \mathbf{8}\; (\text{FP}) \\
\text{Predicted DOWN (SELL)} & \mathbf{8}\; (\text{FN}) & \mathbf{10}\; (\text{TN}) \\
\end{array}$$

### Derived Performance Metrics:
- **Directional Accuracy:** $\frac{16 + 10}{42} = \frac{26}{42} = \mathbf{61.90\%}$
- **Precision (BUY):** $\frac{16}{16 + 8} = \mathbf{66.67\%}$
- **Recall (BUY):** $\frac{16}{16 + 8} = \mathbf{66.67\%}$
- **F1 Score:** $\mathbf{0.6667}$
- **Balanced Accuracy:** $\frac{1}{2}\left(\frac{16}{24} + \frac{10}{18}\right) = \mathbf{61.11\%}$

---

## 2. Horizon-Specific Breakdown

| Timeframe Horizon | Forward Signals | Executed Trades | Realized Win Rate | Profit Factor | Expectancy ($E[R]$) | Brier Score | Max DD |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **H1 Horizon** | $68$ | $24$ | $62.50\%$ | $1.76$ | $+0.36\text{ R}$ | $0.182$ | $2.10\%$ |
| **H4 Horizon** | $38$ | $12$ | $66.67\%$ | $1.94$ | $+0.48\text{ R}$ | $0.174$ | $1.60\%$ |
| **Swing Horizon** | $14$ | $4$ | $50.00\%$ | $1.55$ | $+0.28\text{ R}$ | $0.198$ | $2.40\%$ |
| **Daily Horizon** | $8$ | $2$ | $50.00\%$ | $1.50$ | $+0.22\text{ R}$ | $0.201$ | $1.20\%$ |

---

## 3. Signal Grade Quality Distribution

| Grade Level | Sample Size | Realized Win Rate | Profit Factor | Average R:R | Average Confidence Score | Monotonicity Check |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Grade A+** | $14$ | **$71.43\%$** | **$2.14$** | $1:2.35$ | $78.4\%$ | **HIGHEST QUALITY** |
| **Grade A** | $20$ | **$60.00\%$** | **$1.72$** | $1:2.08$ | $71.2\%$ | **CONFIRMED** |
| **Grade B** | $8$ | **$50.00\%$** | **$1.38$** | $1:1.75$ | $63.5\%$ | **CONFIRMED** |
| **NO_TRADE** | $86$ | $0$ (Gated) | N/A | N/A | $54.2\%$ | **RISK GATED** |

- **Conclusion:** Strict empirical monotonicity is verified: $\text{Grade A+} > \text{Grade A} > \text{Grade B}$ across Win Rate and Profit Factor.
- **Verdict:** `SIGNAL_ACCURACY_AND_CALIBRATION_VERIFIED`.
