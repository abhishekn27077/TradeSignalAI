# PHASE 50.11 — INDICATOR RUNTIME PERTURBATION & ATTRIBUTION AUDIT

**Audit Scope:** Controlled perturbation testing across all 14 indicators in `config/feature_registry.json`.

---

## 1. Perturbation & Decision Sensitivity Table

| Feature ID | Feature Name | Baseline Execution | Perturbed Value | Decision Changed? | Runtime Role |
|:---|:---|:---:|:---:|:---:|:---|
| `FEAT-EMA` | EMA 20/50/200 | Bullish Trend | Inverted Bearish | **YES (BUY $\rightarrow$ NO_TRADE)** | `CORE_SIGNAL` |
| `FEAT-SUPERTREND`| SuperTrend (10, 3.0) | Bullish | Bearish | **YES (BUY $\rightarrow$ NO_TRADE)** | `CORE_SIGNAL` |
| `FEAT-RSI` | RSI 14 | $64.2$ | $42.0$ | **YES (Confidence drops)** | `CORE_SIGNAL` |
| `FEAT-MACD` | MACD (12, 26, 9) | Positive Hist | Negative Hist | **YES (Confidence drops)** | `CORE_SIGNAL` |
| `FEAT-ATR` | ATR 14 | $0.0011$ | $0.0035$ | **NO (SL/TP widens)** | `RISK_ONLY` |
| `FEAT-ADX` | ADX 14 | $27.4$ | $14.5$ | **YES (Gated to NO_TRADE)**| `REGIME_ONLY` |
| `FEAT-BOS` | Break of Structure | True | False | **YES (BUY $\rightarrow$ NO_TRADE)** | `CORE_SIGNAL` |
| `FEAT-CHOCH` | Change of Character | False | True | **YES (Reversal flagged)** | `CORE_SIGNAL` |
| `FEAT-OB` | Order Blocks | Valid OB | No OB Zone | **YES (No Entry Anchor)** | `CORE_SIGNAL` |
| `FEAT-FVG` | Fair Value Gaps | FVG Present | No Imbalance | **YES (TP Anchor Adjusted)**| `CORE_SIGNAL` |
| `FEAT-SWEEP` | Liquidity Sweeps | Swept High | No Sweep | **YES (Confidence drops)** | `CORE_SIGNAL` |
| `FEAT-SMA` | SMA 50/200 | Golden Cross | Death Cross | NO (Background only) | `SUPPORTING_SIGNAL` |
| `FEAT-VWAP` | VWAP | Above VWAP | Below VWAP | NO (Background only) | `SUPPORTING_SIGNAL` |
| `FEAT-BB` | Bollinger Bands | Mid-band | Band Touch | NO (Background only) | `SUPPORTING_SIGNAL` |

---

## 2. Verdict

All 9 decisional features cause direct alterations to the signal decision or consensus score when perturbed. The 1 risk feature alters SL/TP distances, and the 1 regime feature enforces chop gating.
