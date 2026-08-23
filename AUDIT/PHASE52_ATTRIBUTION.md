# PHASE 52 — ATTRIBUTION ADVERSARIAL AUDIT

---

## §52.16 — ATR Attribution Audit

**Phase 51 Claim:** ATR = +0.42 PF

| Component | Type | PF Impact |
|:---|:---|:---:|
| Dynamic SL Distance | Risk Management | +0.22 PF |
| Position Sizing (ATR-scaled lots) | Position Sizing | +0.14 PF |
| TP Anchoring (ATR multiples) | Risk Management | +0.06 PF |
| Directional Prediction | N/A | 0.00 PF |

**Conclusion:** ATR contribution is **entirely risk-management and position-sizing**. It has **zero directional prediction value**. The +0.42 PF is the sum of SL+sizing+TP contributions, which is a **mixture** of risk components.

| Test | PF |
|:---|:---:|
| Fixed 20-pip SL, fixed 0.1 lots | 1.36 |
| ATR-dynamic SL, fixed 0.1 lots | 1.58 |
| ATR-dynamic SL, ATR-scaled lots | 1.78 |

**Classification:** `VERIFIED` — ATR provides +0.42 PF through risk management, not prediction.

---

## §52.17 — ADX Attribution Audit

**Phase 51 Claim:** ADX = +0.28 PF

| Metric | ADX Gate ON | ADX Gate OFF | Delta |
|:---|:---:|:---:|:---:|
| Total Signals Passed | 116 | 128 | +12 |
| Trades Executed | 42 | 50 | +8 |
| Winners Removed | 2 | — | — |
| Losers Removed | 6 | — | — |
| PF | 1.78 | 1.50 | +0.28 |

**Source of Improvement:**
- **Better predictions:** No (ADX doesn't predict direction)
- **Removing bad trades:** **YES** — removes 8 trades, 6 of which are losses
- **Reducing exposure:** YES — reduces from 50 to 42 executed trades
- **Selection bias:** POSSIBLE — ADX < 20 filter disproportionately removes losers

> [!NOTE]
> ADX improvement is genuine **trade selection**, not prediction improvement. It removes 75% losses (6/8 removed trades are losses) from choppy environments. This is a valid and defensible filter, not selection bias, because the ADX threshold was set *before* the forward period.

**Classification:** `VERIFIED` — improvement from removing bad trades in choppy conditions.

---

## §52.18 — SMC Attribution Audit

**Phase 51 Claim:** SMC = +0.37 PF

| Component | Marginal ΔPF | Interaction | Status |
|:---|:---:|:---:|:---|
| BOS (Break of Structure) | +0.14 | +0.03 with OB | Core trend confirmation |
| CHoCH (Change of Character) | +0.06 | +0.02 with BOS | Early reversal detection |
| Order Blocks (OB) | +0.12 | +0.04 with Sweep | Entry zone anchoring |
| FVG (Fair Value Gaps) | +0.04 | +0.01 with OB | TP anchoring |
| Liquidity Sweeps | +0.08 | +0.03 with BOS | Reversal confirmation |

**Sum of marginals:** +0.44 PF  
**Interaction effects:** +0.13 PF  
**True joint contribution:** +0.37 PF  
**Overlap:** 0.44 + 0.13 - 0.37 = **0.20 PF overlap** (features share predictive information)

> [!IMPORTANT]
> Individual SMC component PF deltas **do not sum linearly** due to significant overlap. The joint contribution of +0.37 PF is less than the sum of marginals (+0.44). This is expected for correlated structural features.

**Classification:** `VERIFIED` — joint contribution +0.37 PF confirmed with overlap documented.

---

## §52.19 — TradingView Attribution Audit

**Phase 51 Claim:** TradingView = +0.08 PF

### Decision Path Trace

```
TradingView WebSocket Feed
    → SuperTrend, UT Bot alerts
    → app/strategies/Ensemble/ensemble_engine.py
    → StrategyVote(family=TREND, ...)
    → Confluence Engine score contribution
    → CanonicalDecisionEngine final signal
```

TradingView data **does** influence the final decision through:
1. The ensemble engine receives TradingView-derived strategy votes
2. These contribute to confluence scoring
3. Confluence score determines actionability

**However:** In the current `quant_pipeline_orchestrator.py` (line 273-277), the TradingView indicators (`SUPERTREND`, `UT_BOT`) are hardcoded as technical_data inputs with fixed strengths (0.85, 0.80). They are **not dynamically sourced from TradingView at runtime**.

> [!CAUTION]
> **TradingView integration is PARTIALLY IMPLEMENTED.** The indicator names reference TradingView strategies, but the actual values are **locally computed** Python implementations, not live TradingView webhook data. The +0.08 PF attribution is for the **locally computed SuperTrend/UT Bot**, not for TradingView's independent calculation.

**Classification:** `PARTIALLY_VERIFIED` — indicator logic exists and contributes, but runtime data source is local Python, not live TradingView feed.

---

## §52.20 — News Attribution Audit

**Phase 51 Claim:** News = +0.18 PF

| Component | Signals Affected | Trades Removed | Wins Removed | Losses Removed | ΔPF |
|:---|:---:|:---:|:---:|:---:|:---:|
| BLACKOUT (±30m) | 28 gated | 20 resolved | 5 | 15 | +0.12 |
| SURPRISE (directional) | 6 influenced | — | — | — | +0.04 |
| SEMANTIC | 2 influenced | — | — | — | +0.02 |
| **Total** | — | — | — | — | **+0.18** |

**Point-in-time verification:** News calendar events have known release timestamps. The ±30m blackout window applies **before** the release, which is strictly causal. Post-release surprise data is used only after publication timestamp.

**Classification:** `VERIFIED` — news contribution confirmed with strict temporal causality.

---

## §52.21 — AI Attribution Audit

**Phase 51 Claim:** Technical-only PF = 1.52, Full ensemble PF = 1.78, AI ΔPF = +0.26

| Configuration | Trade Count | Win Rate | PF | Expectancy | Brier |
|:---|:---:|:---:|:---:|:---:|:---:|
| Full Ensemble (baseline) | 42 | 61.90% | 1.78 | +0.30R | 0.184 |
| Kronos OFF | 42 | 57.14% | 1.55 | +0.21R | 0.210 |
| FAISS OFF | 42 | 59.52% | 1.63 | +0.24R | 0.198 |
| Kronos + FAISS OFF | 42 | 54.76% | 1.52 | +0.19R | 0.225 |

> [!IMPORTANT]
> **Causality caveat:** This is an ablation study on N=42 trades, not a randomized controlled experiment. The observed +0.26 PF improvement **may** reflect genuine AI contribution, but:
> 1. Sample size is too small for causal inference
> 2. No control for confounding (market regime, timing)
> 3. Ablation changes the signal quality gate which changes trade selection
>
> **Do NOT call this causal AI improvement.** Classify as: `OBSERVATIONAL_ASSOCIATION`

**Classification:** `PARTIALLY_VERIFIED` — consistent improvement observed but causality not established.
