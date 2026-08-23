# PHASE 53 — 14-INDICATOR RUNTIME AUDIT & FUNCTIONAL CLASSIFICATION

**Authoritative Registry:** `config/feature_registry.json`  
**Config Hash:** `79a4f8e12b79310d`  
**Active Indicator Count:** 14

---

## 1. Functional Classification Matrix

Each of the 14 registered indicators is explicitly mapped to its exact functional role in the 15-stage quant pipeline:

| Index | Indicator Name | Category | Pipeline Stage | Functional Role | Decision Impact |
|:---:|:---|:---:|:---:|:---:|:---|
| 1 | `EMA_20` | Trend | Stage 4 (Feature Calc) | `DECISION` | Short-term trend momentum bias |
| 2 | `EMA_50` | Trend | Stage 4 (Feature Calc) | `DECISION` | Intermediate trend slope filter |
| 3 | `EMA_200` | Trend | Stage 4 (Feature Calc) | `DECISION` | Macro structural trend alignment |
| 4 | `RSI_14` | Momentum | Stage 4 (Feature Calc) | `FILTER` | Overbought/Oversold exhaustion filter |
| 5 | `MACD` | Momentum | Stage 4 (Feature Calc) | `DECISION` | MACD histogram divergence signal |
| 6 | `ATR_14` | Volatility | Stage 10 (Risk Engine) | `RISK` | Dynamic position sizing & SL distance |
| 7 | `ADX_14` | Regime | Stage 7 (Regime Engine) | `FILTER` | $\text{ADX} < 20$ chop market gate |
| 8 | `SuperTrend` | Trend | Stage 6 (Strategy Ensemble) | `DECISION` | Directional envelope tracking |
| 9 | `Bollinger_Bands` | Volatility | Stage 4 (Feature Calc) | `FILTER` | Volatility squeeze & breakout check |
| 10 | `Stochastic_RSI`| Momentum | Stage 4 (Feature Calc) | `FILTER` | Micro-timing entry confirmation |
| 11 | `VWAP` | Volume/Price| Stage 4 (Feature Calc) | `DECISION` | Institutional fair-value anchor |
| 12 | `OBV` | Volume | Stage 4 (Feature Calc) | `DECISION` | Volume accumulation/distribution |
| 13 | `Pivot_Points` | Support/Res | Stage 8 (Confluence Engine) | `RISK` | Key support/resistance levels |
| 14 | `CCI_20` | Momentum | Stage 4 (Feature Calc) | `DISPLAY` | Ancillary momentum cross-check |

---

## 2. Invariant Rules

1. **Role Separation:** No indicator classified as `RISK` (e.g. ATR) is claimed to provide directional prediction.
2. **Filter Independence:** Indicators classified as `FILTER` (e.g. ADX, RSI) act purely to eliminate low-probability market environments.
3. **Display Integrity:** Indicators marked `DISPLAY` (e.g. CCI) are exposed for user visual inspection and do not directly veto execution.
