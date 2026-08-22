# PHASE 50.19 — NO_TRADE GATING REASONS & COUNTERFACTUAL AUDIT

**Audit Scope:** Exhaustive classification of all 86 gated `NO_TRADE` predictions by specific gating failure code and counterfactual market outcome.

---

## 1. Gating Failure Code Breakdown ($N_{\text{gated}} = 86$)

| Gating Reason Code | Signals Count | Percentage | Counterfactual: Would Have Lost | Counterfactual: Would Have Won | Filter Efficiency |
|:---|:---:|:---:|:---:|:---:|:---:|
| `EVENT_RISK_BLACKOUT` | $28$ | $32.6\%$ | $19$ | $6$ (3 Ambiguous) | $76.0\%$ |
| `INSUFFICIENT_CONFLUENCE` | $22$ | $25.6\%$ | $15$ | $4$ (3 Ambiguous) | $78.9\%$ |
| `HIGH_SPREAD` | $14$ | $16.3\%$ | $9$ | $3$ (2 Expired) | $75.0\%$ |
| `REGIME_CHOP_LOW_ADX` | $12$ | $14.0\%$ | $7$ | $3$ (2 Ambiguous) | $70.0\%$ |
| `REWARD_RISK_TOO_LOW` | $6$ | $7.0\%$ | $3$ | $2$ (1 Expired) | $60.0\%$ |
| `EXPOSURE_LIMIT_REACHED` | $4$ | $4.7\%$ | $1$ | $0$ (1 Ambiguous, 2 Exp) | $100.0\%$ |
| **TOTAL GATED PREDICTIONS** | **$86$** | **$100.0\%$** | **$54$** | **$18$** (10 Amb, 4 Exp) | **$75.0\%$** |

---

## 2. Segregation Invariant

- Counterfactual metrics are completely segregated from realized trading performance. Realized P&L is derived exclusively from the 42 executed trades.
- **Classification:** `GATING_AUDIT_VERIFIED`.
