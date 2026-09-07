# AUDIT: PHASE 68 SIGNAL FREQUENCY CONTROL, DEDUPLICATION & CORRELATION EXPOSURE
**System:** TradeSignalAI-v3  
**Module:** `app/core/signal_frequency_controller.py`  

---

## 1. Frequency Control Gates & Cooldowns

To eliminate signal flooding and over-concentration, candidate setups pass through four quantitative frequency gates:

1. **Signal Deduplication Gate:**
   - Computes SHA-256 canonical fingerprint: $\text{SHA256}(\text{asset, timeframe, direction, snapshot\_hash, entry, SL, TP, policy})$.
   - If an identical fingerprint was journaled within the duplicate window ($1800\text{s}$), the setup is suppressed as `DUPLICATE_SIGNAL_SUPPRESSED`.
2. **Portfolio Capacity Limit:**
   - Caps total concurrent active paper signals at 15 ($15.0R$ maximum total exposure).
3. **Asset Capacity Limit:**
   - Caps simultaneous active signals per asset at 3.
4. **Opposite Direction Conflict Gate:**
   - Blocks conflicting signals on the same asset (e.g. attempting a SELL while an active BUY is open).

---

## 2. Multi-Asset Correlation & Cluster Exposure

The engine maps 9 assets into 4 correlated risk clusters:
- **`USD_FX`:** EURUSD, GBPUSD, USDJPY, AUDUSD (Max Cluster Risk: 4.0R)
- **`CRYPTO`:** BTCUSD, ETHUSD (Max Cluster Risk: 4.0R)
- **`METALS`:** XAUUSD (Max Cluster Risk: 4.0R)
- **`INDICES`:** NAS100, SPX500 (Max Cluster Risk: 4.0R)

When total simultaneous active risk exceeds thresholds, the system flags `CLUSTER_OVEREXPOSED` or `PORTFOLIO_CONCENTRATED`, preventing hidden risk multiplier traps across correlated instruments.
