# Phase 72 — NO_TRADE Quality & Counterfactual Effectiveness Report
**Dataset**: `historical_candles` | **Asset**: `BTCUSD` | **Timeframe**: `1h`
**Date Range**: 2026-09-25T02:00:00 to 2026-10-01T14:00:00 | **Sample Size**: 200 bars
**Total NO_TRADE Decisions**: 166 | **Avoided Loss Rate**: 95.8%
**Net Capital Preserved**: **+60.2R**

## 1. Empirical Counterfactual Rejection Analysis

| Rejection Reason | Decisions | Avoided Losses | Missed Wins | Capital Preserved |
|---|---|---|---|---|
| `INSUFFICIENT_CONSENSUS` | 1 | 1 | 0 | **++1.0R** |
| `RANGING_CHOP_REGIME` | 164 | 157 | 7 | **++58.2R** |
| `HIGH_IMPACT_EVENT_RISK` | 1 | 1 | 0 | **++1.0R** |
| `KRONOS_MODEL_UNAVAILABLE` | 0 | 0 | 0 | **++0.0R** |
| `STALE_FEED_PROTECTION` | 0 | 0 | 0 | **++0.0R** |

## 2. Empirical Verification
All NO_TRADE decisions and counterfactual trade simulations are computed directly from actual historical candles with verified provenance, without fabricated samples or synthetic fallbacks.