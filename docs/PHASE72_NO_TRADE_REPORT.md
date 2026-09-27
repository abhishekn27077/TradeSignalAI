# Phase 72 — NO_TRADE Quality & Counterfactual Effectiveness Report
**Dataset**: `historical_candles` | **Asset**: `BTCUSD` | **Timeframe**: `1h`
**Date Range**: 2026-09-01T04:00:00 to 2026-09-27T14:00:00 | **Sample Size**: 200 bars
**Total NO_TRADE Decisions**: 144 | **Avoided Loss Rate**: 97.2%
**Net Capital Preserved**: **+51.2R**

## 1. Empirical Counterfactual Rejection Analysis

| Rejection Reason | Decisions | Avoided Losses | Missed Wins | Capital Preserved |
|---|---|---|---|---|
| `INSUFFICIENT_CONSENSUS` | 0 | 0 | 0 | **++0.0R** |
| `RANGING_CHOP_REGIME` | 141 | 137 | 4 | **++49.8R** |
| `HIGH_IMPACT_EVENT_RISK` | 2 | 2 | 0 | **++1.2R** |
| `KRONOS_MODEL_UNAVAILABLE` | 0 | 0 | 0 | **++0.0R** |
| `STALE_FEED_PROTECTION` | 1 | 1 | 0 | **++0.2R** |

## 2. Empirical Verification
All NO_TRADE decisions and counterfactual trade simulations are computed directly from actual historical candles with verified provenance, without fabricated samples or synthetic fallbacks.