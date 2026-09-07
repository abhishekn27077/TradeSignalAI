# AUDIT: PHASE 67 13-STAGE ZERO-TRUST STRONGEST SIGNAL RANKING ENGINE
**System:** TradeSignalAI-v3  
**Module:** `app/core/strongest_signal_engine.py`  
**Endpoint:** `GET /api/v1/signals/strongest-now?top_n=5`  

---

## 1. The 13 Sequential Quantitative Gates

Every candidate signal evaluated across the 9 assets $\times$ 9 timeframes matrix passes through 13 zero-trust filters:

| Stage # | Stage Name | Quantitative Threshold / Verification | Failure Action |
|---|---|---|---|
| 1 | **Data Quality & Freshness** | Data age $< 2.0\text{s}$, zero NaN/Inf in OHLCV | Reject (`INVALID_MARKET_DATA` / `STALE_MARKET_DATA`) |
| 2 | **Causality Barrier** | Information cutoff $T_{\text{cutoff}} \le T_0$ | Reject (`CAUSAL_VIOLATION`) |
| 3 | **Economic Event Risk** | Event importance $\neq \text{HIGH}$ within $\pm 2\text{h}$ | Reject (`HIGH_EVENT_RISK`) |
| 4 | **Regime Compatibility** | Regime $\neq \text{HIGH_EVENT_RISK}$ | Reject (`UNFAVORABLE_MARKET_REGIME`) |
| 5 | **MTF Conflict Gate** | MTF conflict score $\le 0.40$, HTF alignment $\ge 0.60$ | Reject (`MTF_CONFLICT_DETECTED`) |
| 6 | **9-Cluster Evidence** | Consensus across 9 independent quantitative clusters | Reject (`CONSENSUS_BELOW_THRESHOLD`) |
| 7 | **Bayesian Probability** | Calibrated probability $P \ge 0.65$ | Reject (`CONSENSUS_BELOW_THRESHOLD`) |
| 8 | **Historical Analogue** | Minimum sample $N \ge 30$, positive forward return | Reject (`INSUFFICIENT_HISTORICAL_SAMPLE`) |
| 9 | **Expected Net-R** | Expected Net $R > +0.20R$ | Reject (`NEGATIVE_OR_LOW_EXPECTED_NET_R`) |
| 10 | **Friction Deductions** | Spread ($0.00010$) + Slippage ($0.00005$) + Fees ($0.00005$) deducted | Included in Net-R calculation |
| 11 | **Risk / Reward Ratio** | $\text{Reward} / \text{Risk} \ge 1.50$ | Reject (`RR_BELOW_MINIMUM`) |
| 12 | **Signal Strength** | Decomposed evidence score $\ge 70 / 100$ | Reject (`SIGNAL_STRENGTH_INSUFFICIENT`) |
| 13 | **Conviction Composite Rank** | Rank Score: $0.40 \cdot P_{\text{calib}} + 0.30 \cdot \min(1.0, \frac{E[R]}{0.80}) + 0.20 \cdot \text{HTF} + 0.10 \cdot \frac{\text{Strength}}{100}$ | Output Top $N$ ($1, 3, 5, 10$) |

---

## 2. No-Trade Transparency

When candidate setups fail, the engine outputs explicit structured failure reasons rather than silently dropping records. Users can inspect the **No-Trade Watchlist** tab to understand why capital is currently preserved.
