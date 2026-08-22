# PHASE 49.2 — INDICATOR COUNT RECONCILIATION & AUTHORITATIVE INVENTORY AUDIT

**Audit Scope:** Reconciling the historical discrepancy between "12 indicators" and "14 indicators" across the TradeSignalAI-v3 codebase.

---

## 1. Exhaustive Indicator Inventory Breakdown

| Classification Category | Indicators Included | Count | Direct Effect on `CanonicalTradingSignal` |
|:---|:---|:---:|:---|
| **CORE_SIGNAL** (Primary Decisional) | EMA (20/50/200), SuperTrend, RSI (14), MACD (12/26/9), BOS, CHoCH, Order Blocks, Liquidity Sweeps | **8** | Directly alters Direction (`BUY`/`SELL`) & Supermajority Consensus |
| **SUPPORTING_SIGNAL** (Context/Display) | SMA (50/200), VWAP, Bollinger Bands (20, 2.0) | **3** | Provides secondary contextual confirmation; non-blocking |
| **RISK_ONLY** (Position Sizing / SL) | ATR (14) | **1** | Dynamically calculates Stop Loss & Take Profit pip distances |
| **REGIME_ONLY** (Market State / Chop Filter) | ADX (14) | **1** | Gating filter: suppresses signals when $ADX < 20.0$ |
| **FILTER_ONLY / SMC STRUCTURE** | Fair Value Gaps (FVG) | **1** | Anchors take-profit target & imbalance mitigation gate |
| **TOTAL RUNTIME EXECUTED** | All items above in `config/feature_registry.json` | **14** | All executed in runtime pipeline |

---

## 2. Definitive Reconciliation Summary

- **TOTAL IMPLEMENTED:** **$14$** (In `app/indicators/`, `app/strategies/SmartMoney/`, and `app/strategies/indicators/`)
- **TOTAL RUNTIME EXECUTED:** **$14$** (Called by `CanonicalDecisionEngine.evaluate_market()`)
- **TOTAL DECISION-CONTRIBUTING:** **$9$** ($8\text{ Core Signal} + 1\text{ FVG}$)
- **TOTAL RISK-ONLY:** **$1$** (ATR 14)
- **TOTAL REGIME-ONLY:** **$1$** (ADX 14)
- **TOTAL SUPPORTING / DISPLAY-ONLY:** **$3$** (SMA, VWAP, Bollinger Bands)
- **TOTAL UNUSED / DEPRECATED:** **$0$** (Unused experimental indicators have been cleanly segregated from production)

- **Conclusion:** The authoritative single source of truth is [`config/feature_registry.json`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/config/feature_registry.json).
- **Verdict:** `INDICATOR_COUNT_RECONCILED (14 TOTAL, 100% AUDITED)`.
