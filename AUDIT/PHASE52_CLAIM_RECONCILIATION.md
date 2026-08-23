# PHASE 52 — CLAIM RECONCILIATION TABLE

---

## §52.37–52.38 — Comprehensive Claim Classification

| # | Claim | Source Phase | Raw Evidence | Independent Result | Status | Confidence | Notes |
|:---:|:---|:---:|:---|:---|:---:|:---:|:---|
| 1 | Win Rate = 61.90% | 23 | 26/42 | 26/42 = 61.90% | **VERIFIED** | High | Point estimate exact |
| 2 | Win Rate > 50% statistically | 23 | Wilson CI | CI = [46.8%, 75.0%] | **NOT CONFIRMED** | Low | Lower bound < 50% |
| 3 | PF = 1.78 | 23 | Paper trades | Requires heterogeneous R | **PARTIALLY_VERIFIED** | Medium | Uniform R yields 3.02 |
| 4 | PF > 1.0 at 95% CI | 23 | Bootstrap | 2.5th pctile = 0.94 | **NOT CONFIRMED** | Low | CI includes < 1.0 |
| 5 | PF > 1.0 at 90% CI | 52 | Bootstrap | 5th pctile = 1.04 | **SUPPORTED** | Medium | Marginal |
| 6 | Expectancy = +0.38R | 23 | Mean R | ~+0.30R heterogeneous | **PARTIALLY_VERIFIED** | Medium | Close but not exact |
| 7 | Expectancy > 0 at 95% CI | 23 | Bootstrap | 2.5th = -0.03R | **NOT CONFIRMED** | Low | `EDGE_UNCERTAIN` |
| 8 | Brier = 0.184 | 23 | Calibration | 0.229 (independent) | **PARTIALLY_VERIFIED** | Medium | Different method |
| 9 | ECE = 0.076 | 48 | Calibration | 0.063 | **PARTIALLY_VERIFIED** | Medium | Consistent range |
| 10 | Directional Accuracy = 64.3% | 23 | Signal audit | Consistent | **VERIFIED** | High | |
| 11 | Max DD = 2.40% | 23 | Equity curve | 15.68R uniform, ~3.86R het. | **PARTIALLY_VERIFIED** | Medium | Depends on R model |
| 12 | H4 Best Horizon (1.94 PF) | 51 | 12 trades | N=12, CI [34.9%, 90.1%] | **INSUFFICIENT_SAMPLE** | Low | Too few trades |
| 13 | H1 Primary Engine (1.76 PF) | 51 | 24 trades | N=24, CI [40.6%, 81.2%] | **INSUFFICIENT_SAMPLE** | Low | Below N=30 |
| 14 | EURUSD Best Asset (2.12 PF) | 51 | 7 trades | N=7, CI [29.0%, 96.3%] | **INSUFFICIENT_SAMPLE** | Very Low | |
| 15 | All 9 Assets Positive | 51 | Point estimates | All positive point est. | **PARTIALLY_VERIFIED** | Low | No per-asset significance |
| 16 | Trending Regimes Best | 51 | Bull 2.08, Bear 1.92 | System trend-dependent | **VERIFIED** | Medium | Expected for SMC |
| 17 | Signal Grade Monotonicity | 51 | A+ > A > B | Broken at B vs C | **PARTIALLY_VERIFIED** | Medium | C has tiny N |
| 18 | ATR = +0.42 PF | 51 | Ablation | Risk mgmt contribution | **VERIFIED** | High | Not prediction |
| 19 | ADX = +0.28 PF | 51 | Ablation | Trade removal effect | **VERIFIED** | High | 75% losses removed |
| 20 | SMC = +0.37 PF | 51 | Ablation | Joint contribution | **VERIFIED** | Medium | Overlap documented |
| 21 | TradingView = +0.08 PF | 51 | Ablation | Local Python, not live TV | **PARTIALLY_VERIFIED** | Medium | Not live TV data |
| 22 | News = +0.18 PF | 51 | Ablation | Blackout + surprise | **VERIFIED** | High | Temporal causality ok |
| 23 | AI = +0.26 PF | 49 | Ablation | Observational association | **PARTIALLY_VERIFIED** | Medium | Not causal |
| 24 | Technical-only PF = 1.52 | 49 | Ablation | Consistent | **VERIFIED** | Medium | |
| 25 | Gating 75% Precision | 48 | 54/72 | ~74.3% (52/70) | **PARTIALLY_VERIFIED** | Medium | Close, denominator differs |
| 26 | 128/128 Signals Reproduced | 50 | Determinism test | Consistent | **VERIFIED** | High | |
| 27 | Zero Lookahead | 50 | Temporal mutation | Zero future leakage | **VERIFIED** | High | |
| 28 | Zero Data Snooping | 50 | Codebase grep | Zero target ingestion | **VERIFIED** | High | |
| 29 | Non-Repainting | 46 | Indicator audit | Verified for all 14 | **VERIFIED** | High | |
| 30 | TV Pine/Python Parity | 46 | 1000-bar replay | Exact match | **VERIFIED** | High | |
| 31 | Frontend == Backend | 50 | 13 views | 100% equality | **VERIFIED** | High | |
| 32 | Real Money DISABLED | 22–51 | All paths | Locked at all layers | **VERIFIED** | High | |
| 33 | 14 Active Indicators | 49 | Registry | Exact match | **VERIFIED** | High | |
| 34 | Same-Candle Conservative | 50 | 3 affected trades | All SL-first | **VERIFIED** | High | |
| 35 | CONFIG_HASH Frozen | All | Git + code | 79a4f8e12b79310d | **VERIFIED** | High | |
| 36 | Monte Carlo 0% P(Loss) | 51 | 10K runs | 0/100K (bound 0.003%) | **VERIFIED** | High | Terminal R constant |
| 37 | 99th DD < 5% | 51 | 10K uniform | 7.73R heterogeneous | **PARTIALLY_REFUTED** | Medium | Model-dependent |
| 38 | Edge Diversified | 51 | Multi-dimension | MODERATELY_CONCENTRATED | **PARTIALLY_REFUTED** | Medium | Top-10 removal kills edge |
| 39 | p = 0.0018 Significant | 23 | Binomial test | Fails multiple testing | **REFUTED** | High | 73 hypotheses tested |
| 40 | Sharpe 2.34 | Historical | Not forward | Unverified | **UNVERIFIED** | N/A | Never forward-tested |
| 41 | WFE 86.5% | Historical | Not forward | Unverified | **UNVERIFIED** | N/A | Never forward-tested |
| 42 | R-multiples [1.82/-0.98] | 47 | Code default | Uniform idealization | **REFUTED** | High | Not real per-trade data |

---

## Summary Statistics

| Status | Count | Percentage |
|:---|:---:|:---:|
| **VERIFIED** | 18 | 42.9% |
| **PARTIALLY_VERIFIED** | 12 | 28.6% |
| **NOT CONFIRMED** | 3 | 7.1% |
| **INSUFFICIENT_SAMPLE** | 3 | 7.1% |
| **PARTIALLY_REFUTED** | 3 | 7.1% |
| **REFUTED** | 2 | 4.8% |
| **UNVERIFIED** | 2 | 4.8% |
| **SUPPORTED** (new) | 1 | 2.4% |

---

## §52.35 — Frontend/Backend Reconciliation

All 13 primary frontend views reconciled against API and CanonicalDecisionEngine.

**Result:** 100% exact equality. **VERIFIED.**

---

## §52.36 — Real-Money Security

| Attack Vector | Result |
|:---|:---:|
| REST execution endpoint | ❌ BLOCKED (PAPER mode only) |
| WebSocket execution | ❌ BLOCKED (no live adapter registered) |
| Broker adapter | ❌ BLOCKED (DummyBroker/PaperExecutor only) |
| Manual execution endpoint | ❌ BLOCKED (no route exists) |
| TradingView webhook execution | ❌ BLOCKED (no execution path) |
| Background worker | ❌ BLOCKED (ExecutionMode.PAPER) |
| Scheduled execution | ❌ BLOCKED (no scheduler registered) |

**Result:** 7/7 attack vectors blocked. Real money is **STRICTLY DISABLED**.
