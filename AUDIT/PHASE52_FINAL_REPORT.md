# PHASE 52 — MASTER ADVERSARIAL STATISTICAL INTEGRITY REPORT

**Audit Date (UTC):** `2026-08-22T17:23:00Z`  
**Auditor:** Adversarial Statistical Integrity Auditor  
**Frozen Baseline:** Git `889cda3` (`CONFIG_HASH = 79a4f8e12b79310d`)  
**Real-Money:** `STRICTLY_DISABLED`

---

## FINAL OUTPUT

```
====================================================================
PHASE 52 ADVERSARIAL STATISTICAL INTEGRITY REPORT
====================================================================

PHASE 52 STATUS:
EDGE_SUPPORTED_WITH_LIMITATIONS

RAW RECONSTRUCTION:
  Uniform R PF = 3.02 (REFUTED as real distribution)
  Heterogeneous R PF = 1.78 (RECONSTRUCTED)
  R-distribution in code = SIMPLIFIED_IDEALIZATION
  Gross Profit = 28.48R, Gross Loss = 16.00R

WIN RATE:
  Point Estimate: 61.90% (26/42)
  Wilson 95% CI: [46.81%, 75.00%]
  Clopper-Pearson 95% CI: [45.64%, 76.43%]
  Lower Bound > 50%: NO (at 95% level)

PROFIT FACTOR:
  Point Estimate: 1.78
  Bootstrap 95% CI: [0.94, 3.64]
  Lower 95% bound > 1.0: NO
  Lower 90% bound > 1.0: YES (5th pctile = 1.04)

EXPECTANCY:
  Point Estimate: +0.30R per trade
  Bootstrap 95% CI: [-0.03R, +0.62R]
  Lower 95% bound > 0: NO
  FLAG: EDGE_UNCERTAIN (at 95% CI)

BOOTSTRAP RESULTS:
  PF stable at ~1.78 across 10K/50K/100K iterations
  Expectancy stable at ~+0.30R
  Numerical convergence: VERIFIED

MONTE CARLO RESULTS:
  100,000 IID permutations
  Terminal R: +12.48R (constant)
  Negative terminal: 0/100,000 (upper bound 0.003%)
  Median Max DD: 3.86R
  99th Percentile DD: 7.73R
  Maximum Observed DD: 12.82R
  PATH_DEPENDENCY_RISK: FLAGGED (block bootstrap 99th = 24.7R)

MULTIPLE TESTING RESULT:
  73 hypotheses tested across Phases 22-51
  Base p = 0.0018
  Bonferroni threshold = 0.000685
  SURVIVES CORRECTION: NO
  Individual subgroup findings: EXPLORATORY ONLY

BEST HORIZON:
  H4 (66.67% WR, 1.94 PF, +0.48R)

HORIZON CONFIDENCE:
  ALL HORIZONS INSUFFICIENT_SAMPLE (N < 30 each)
  95% CIs overlap completely

BEST ASSETS:
  EURUSD (2.12 PF), XAUUSD (1.95 PF), BTCUSD (1.88 PF)

ASSET CONFIDENCE:
  ALL ASSETS INSUFFICIENT_SAMPLE (N < 30 each)
  95% CIs span near-zero to near-100%

REGIME RESULTS:
  TRENDING_BULL: 2.08 PF
  TRENDING_BEAR: 1.92 PF
  System is TREND_DEPENDENT
  Removing both trending regimes: PF ~1.15

INDICATOR CONTRIBUTION:
  ATR: +0.42 PF (VERIFIED, risk management only)
  ADX: +0.28 PF (VERIFIED, trade removal)

SMC CONTRIBUTION:
  +0.37 PF (VERIFIED, joint with 0.20 PF overlap)

TRADINGVIEW CONTRIBUTION:
  +0.08 PF (PARTIALLY_VERIFIED, local Python not live TV)

NEWS CONTRIBUTION:
  +0.18 PF (VERIFIED, temporal causality confirmed)

AI CONTRIBUTION:
  +0.26 PF (PARTIALLY_VERIFIED, observational not causal)

GATING QUALITY:
  ~74% resolved rejection precision
  System effectively avoids more losses than wins
  PARTIALLY_VERIFIED (denominator differs by 2)

COST ROBUSTNESS:
  Edge survives up to +200% friction (5.1 pips)
  Breakeven at ~3.5x base friction (5.9 pips)
  VERIFIED (robust)

CALIBRATION:
  Brier = 0.229 (higher than reported 0.184)
  ECE = 0.063
  3/8 buckets have N < 5
  PARTIALLY_VERIFIED

EDGE CONCENTRATION:
  MODERATELY_CONCENTRATED
  Top 10 trades removal destroys edge
  Asset/horizon diversification survives
  Trend-dependent

LOOKAHEAD:
  PASS (zero temporal leakage)

DATA SNOOPING:
  PASS (zero target variable ingestion)

FRONTEND == BACKEND:
  PASS (100% exact equality)

CLAIM RECONCILIATION:
  18/42 VERIFIED (42.9%)
  12/42 PARTIALLY_VERIFIED (28.6%)
  3/42 NOT_CONFIRMED (7.1%)
  3/42 INSUFFICIENT_SAMPLE (7.1%)
  3/42 PARTIALLY_REFUTED (7.1%)
  2/42 REFUTED (4.8%)
  2/42 UNVERIFIED (4.8%)
  1/42 SUPPORTED (2.4%)

FORWARD SAMPLE:
  128 Signals / 42 Realized Trades
  Tier 2: EARLY_FORWARD_EVIDENCE

REAL MONEY STATUS:
  STRICTLY DISABLED (7/7 attack vectors blocked)

FINAL CLASSIFICATION:
  EDGE_SUPPORTED_WITH_LIMITATIONS

LIMITATIONS:
  1. N=42 insufficient for 95% statistical significance
  2. Bootstrap PF CI includes values < 1.0
  3. Bootstrap expectancy CI includes negative values
  4. Path dependency risk flagged (block bootstrap)
  5. p-value fails multiple testing correction
  6. Per-asset and per-horizon samples all < 30
  7. Signal grade monotonicity broken at B vs C
  8. R-multiple distribution in code is idealized
  9. TradingView integration is local Python, not live feed
  10. AI contribution is observational, not causal

STRENGTHS:
  1. Zero lookahead, zero data snooping
  2. Zero real-money execution paths
  3. Cost robustness up to +200% friction
  4. Consistent positive point estimates across all dimensions
  5. Effective gating system (~74% precision)
  6. Deterministic reproducibility
  7. Frozen configuration integrity
  8. Same-candle conservative resolution
  9. Monte Carlo terminal R always positive
  10. 90% CI for PF includes only values > 1.0

NEXT ACTION:
  CONTINUE FROZEN FORWARD SHADOW ACCUMULATION
  Target: 100 realized trades for PRELIMINARY_EVIDENCE
  Target: 300 realized trades for STRONGER_FORWARD_EVIDENCE
  DO NOT ENABLE REAL MONEY
  DO NOT MODIFY STRATEGY
  DO NOT OPTIMIZE PARAMETERS
====================================================================
```

---

## Supporting Reports

1. [`PHASE52_RAW_RECONSTRUCTION.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_RAW_RECONSTRUCTION.md)
2. [`PHASE52_BOOTSTRAP.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_BOOTSTRAP.md)
3. [`PHASE52_MONTE_CARLO.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_MONTE_CARLO.md)
4. [`PHASE52_EDGE_CONCENTRATION.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_EDGE_CONCENTRATION.md)
5. [`PHASE52_GATING.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_GATING.md)
6. [`PHASE52_ATTRIBUTION.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_ATTRIBUTION.md)
7. [`PHASE52_MULTIPLE_TESTING.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_MULTIPLE_TESTING.md)
8. [`PHASE52_EXECUTION_COST.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_EXECUTION_COST.md)
9. [`PHASE52_CALIBRATION.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_CALIBRATION.md)
10. [`PHASE52_HORIZON.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_HORIZON.md)
11. [`PHASE52_ASSET.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_ASSET.md)
12. [`PHASE52_CLAIM_RECONCILIATION.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_CLAIM_RECONCILIATION.md)
13. [`PHASE52_FINAL_REPORT.md`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/AUDIT/PHASE52_FINAL_REPORT.md) (this file)
