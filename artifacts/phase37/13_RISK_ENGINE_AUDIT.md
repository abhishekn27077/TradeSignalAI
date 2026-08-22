# 13 — Risk Engine Audit & Risk-Reward Enforcement
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Mathematical Risk Modeling
`RiskEngine` calculates volatility-adjusted trade parameters:
- **Stop Loss (SL):**
  $$\text{SL}_{\text{BUY}} = P_{\text{entry}} - 1.5 \times \text{ATR}_{14}$$
  $$\text{SL}_{\text{SELL}} = P_{\text{entry}} + 1.5 \times \text{ATR}_{14}$$
- **Take Profit (TP):**
  $$\text{TP}_{\text{BUY}} = P_{\text{entry}} + 3.0 \times \text{ATR}_{14}$$
  $$\text{TP}_{\text{SELL}} = P_{\text{entry}} - 3.0 \times \text{ATR}_{14}$$
- **Risk-Reward Ratio ($R:R$):**
  $$R:R = \frac{|\text{TP} - P_{\text{entry}}|}{|\text{SL} - P_{\text{entry}}|} = \frac{3.0 \times \text{ATR}_{14}}{1.5 \times \text{ATR}_{14}} = 2.00 \ge 1.50$$

---

## 2. Hard Invariants
- Minimum allowed $R:R$ is $1.50$. Any setup yielding $R:R < 1.50$ is immediately rejected with `POOR_RISK_REWARD`.
- ATR values must be positive and non-zero.
- Status: **PASSED & MATHEMATICALLY CERTIFIED**.
