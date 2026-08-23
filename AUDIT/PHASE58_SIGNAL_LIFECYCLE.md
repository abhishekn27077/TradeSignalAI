# PHASE 58 — END-TO-END FORWARD SIGNAL LIFECYCLE & TWO-PLANE ARCHITECTURE

**Audit Phase:** Phase 58 — Signal Lifecycle & Plane Separation  
**Date (UTC):** 2026-08-23T15:15:00Z  
**Configuration Hash:** `79a4f8e12b79310d` (FROZEN)  

---

## 1. Two-Plane System Architecture

```
+-----------------------------------------------------------------------------------+
|                           PLANE A: LIVE SIGNAL PLANE                             |
|  [Market Data] -> [14 Indicators] -> [SMC] -> [Regime] -> [News] -> [AI (2-5s)]  |
|         -> [Risk Score] -> [Decision] -> [Durable Signal Truth Ledger]            |
|                  (Synchronous, Deterministic, Low-Latency SLA < 1.0s)             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v  (Asynchronous Event Egress)
+-----------------------------------------------------------------------------------+
|                        PLANE B: RESEARCH & EVIDENCE PLANE                         |
|  [Unresolved Queue] -> [Causal Resolution] -> [Realized Trade Truth Ledger]       |
|      -> [Counterfactual Store] -> [100K Bootstrap] -> [100K Monte Carlo]          |
|      -> [Drift Analysis] -> [Daily Snapshots] -> [Safe Tiered Archival]           |
|                (Asynchronous, Heavy Compute, Zero Delay to Plane A)               |
+-----------------------------------------------------------------------------------+
```

---

## 2. 10-Stage Immutable Signal Lifecycle

1. **Candle Close Trigger:** Ingests latest closed candle for configured asset & timeframe.
2. **Decision Key Deduplication:** Checks `(asset, timeframe, candle_close_time, config_hash)` to prevent duplicate signal generation.
3. **14-Feature Calculation:** Computes EMAs, Supertrend, RSI, MACD, Volume Profile, ATR, and ADX synchronously.
4. **SMC Closed-Bar Confirmation:** Confirms BOS, CHoCH, Order Blocks, FVG, and Liquidity Sweeps on confirmed bar close ($T - 1$).
5. **Macro News Blackout Check:** Evaluates $\pm 30\text{min}$ blackout window for scheduled high-impact events.
6. **Bounded AI Consensus:** Queries Kronos + FAISS with strict 2–5s timeout. If timeout occurs $\rightarrow$ `AI_UNAVAILABLE` fail-closed.
7. **Consensus & Risk Scoring:** Verifies risk budget, portfolio exposure limits, and R:R ratio.
8. **Point-in-Time Snapshot:** Captures all 42 fields into a frozen `SignalTruthRecord`.
9. **Durable Ledger Commit:** Appends snapshot to `SignalTruthLedger` and computes SHA256 chain link.
10. **Asynchronous Resolution Hand-Off:** Enqueues signal to `ForwardResolutionEngine` for future causal resolution.
