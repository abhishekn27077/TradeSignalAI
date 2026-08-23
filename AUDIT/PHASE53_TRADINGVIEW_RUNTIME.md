# PHASE 53 — TRADINGVIEW RUNTIME INTEGRATION AUDIT

---

## 1. Runtime Decision Path

TradingView indicators and alerts contribute to the `CanonicalDecisionEngine` strictly through the ensemble layer:

```
TradingView Strategy Alert (Local Pine Parity / Webhook)
    ↓
app/strategies/Ensemble/ensemble_engine.py
    ↓
StrategyVote(family="TREND", strategy="SUPERTREND_TV", confidence=0.85)
    ↓
Stage 8: Confluence Engine (Score Weight: 0.10)
    ↓
Stage 9: Consensus Gating (Requires 3+ Unanimous Clusters)
    ↓
CanonicalTradingSignal (Final Decision)
```

---

## 2. Functional Classification: `SECONDARY_SUPPORT_ONLY`

The adversarial audit established that:
1. TradingView technical indicators (SuperTrend, UT Bot) are implemented in local Python with verified Pine Script parity.
2. TradingView signals provide supporting votes in Stage 6 (Strategy Ensemble) and Stage 8 (Confluence Engine).
3. TradingView alone cannot generate a `TAKE_TRADE` signal — it requires confirmation from Market Structure (BOS/OB), Multi-Timeframe Trend, and Risk Gates.
4. **Classification:** **`SECONDARY_SUPPORT_ONLY`**. TradingView is a supporting consensus input, not the primary decision engine.

---

## 3. Signal Trace Invariant

Every live signal records:
- `tv_signal_present: bool`
- `tv_signal_direction: str`
- `tv_signal_timestamp: str`
- `tv_signal_hash: str`
- `tv_contribution: float` ($+0.08\text{ PF}$ marginal contribution)
- `tv_role: "SECONDARY_SUPPORT_ONLY"`
