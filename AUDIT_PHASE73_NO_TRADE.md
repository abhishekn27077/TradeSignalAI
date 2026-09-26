# Phase 73/74 Audit: NO_TRADE Quality & Counterfactual Analysis (Phase 20)

**Audit Date**: 2026-09-26  
**Auditor**: Independent Zero-Trust Forensic Auditor  
**Status**: **FABRICATED / SYNTHETIC REPORTING (CRITICAL FAILURE)**

---

## 1. Executive Summary

Previous documentation (`docs/PHASE72_NO_TRADE_REPORT.md`) claimed that the system generates and tracks high-conviction `NO_TRADE` decisions across assets, demonstrating that over **70.5%** of filtered trades would have lost money in counterfactual simulations, preserving **+44.0R** of trading capital.

Forensic examination of `app/analytics/no_trade_engine.py` demonstrates that:
1. **Zero actual market or database counterfactual simulation occurs.**
2. Although the engine opens a connection to SQLite (`tradesignal.db`), it executes **zero SQL queries**.
3. All metrics (decisions = 105, avoided losses = 74, avoided loss rate = 70.5%, capital saved = +44.0R) are **hardcoded in a static dictionary**.
4. The engine generates `docs/PHASE72_NO_TRADE_REPORT.md` directly by serializing this hardcoded dictionary to markdown.

---

## 2. Forensic Code Evidence

File: [`app/analytics/no_trade_engine.py`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/analytics/no_trade_engine.py#L43-L79)

```python
    def evaluate_no_trade_effectiveness(self) -> Dict[str, Any]:
        """
        Calculates counterfactual performance of rejected / NO_TRADE decisions.
        """
        conn = self._get_connection()
        if not conn:
            return {"success": False, "error": "Database unavailable"}

        try:
            # Analyze NO_TRADE decisions
            reasons_breakdown = {
                "INSUFFICIENT_CONSENSUS": {"count": 42, "counterfactual_losses": 28, "counterfactual_wins": 14, "saved_r": 14.5},
                "RANGING_CHOP_REGIME": {"count": 35, "counterfactual_losses": 26, "counterfactual_wins": 9, "saved_r": 17.0},
                "HIGH_IMPACT_EVENT_RISK": {"count": 18, "counterfactual_losses": 13, "counterfactual_wins": 5, "saved_r": 8.5},
                "KRONOS_MODEL_UNAVAILABLE": {"count": 6, "counterfactual_losses": 4, "counterfactual_wins": 2, "saved_r": 2.0},
                "STALE_FEED_PROTECTION": {"count": 4, "counterfactual_losses": 3, "counterfactual_wins": 1, "saved_r": 2.0},
            }

            total_no_trades = sum(v["count"] for v in reasons_breakdown.values())
            total_cf_losses = sum(v["counterfactual_losses"] for v in reasons_breakdown.values())
            total_cf_wins = sum(v["counterfactual_wins"] for v in reasons_breakdown.values())
            total_saved_r = sum(v["saved_r"] for v in reasons_breakdown.values())

            avoided_loss_rate = round((total_cf_losses / total_no_trades * 100.0), 1) if total_no_trades > 0 else 0.0
...
            self._write_no_trade_report(summary)
            return summary
        finally:
            conn.close()
```

### Mathematical Reproduction
- Sum of counts: $42 + 35 + 18 + 6 + 4 = 105$
- Sum of avoided losses: $28 + 26 + 13 + 4 + 3 = 74$
- Avoided loss percentage: $74 / 105 = 70.476\% \approx 70.5\%$
- Net capital saved: $14.5 + 17.0 + 8.5 + 2.0 + 2.0 = 44.0\text{R}$

The numbers match the claims in `docs/PHASE72_NO_TRADE_REPORT.md` to the decimal point because they were literally hardcoded in the script that emitted the report.

---

## 3. Real Production Path & Database Inspection

1. **Database Schema:**
   The SQLite database contains a table `no_trade_decisions` or `signals`, but `no_trade_engine.py` never reads from them.
2. **Runtime Execution:**
   In real execution (`app/strategies/execution_coordinator.py`), when consensus fails or confidence is below threshold, a signal with direction `NO_TRADE` or `HOLD` is produced. However, no counterfactual execution tracker is ever spawned or updated to evaluate the hypothetical outcome of the rejected trade over subsequent candles.
3. **Absence of Forward Price Simulation:**
   Genuine counterfactual analysis requires recording the timestamp, entry price, proposed SL/TP, and evaluating whether forward candles would have hit SL or TP first. This logic does not exist in `no_trade_engine.py`.

---

## 4. Verdict & Recommendations

| Item | Finding | Status |
|---|---|---|
| **NO_TRADE Engine** | Uses static dictionary instead of empirical counterfactual simulations | **FAIL** |
| **Claimed Capital Preserved (+44.0R)** | Unverified / Synthetic artifact | **FAIL** |
| **Claimed Avoided Loss Rate (70.5%)** | Hardcoded arithmetic | **FAIL** |

### Corrective Action:
1. Implement empirical counterfactual tracking in `canonical_ledger` or `shadow_predictions` where rejected signals are recorded along with hypothetical SL/TP levels.
2. Ingest subsequent 1m/5m candles to resolve whether hypothetical trades would hit SL or TP first.
3. Compute genuine empirical statistics on live/shadow data rather than static constants.
