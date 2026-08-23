# PHASE 52 — EXECUTION COST & REALISM AUDIT

---

## §52.24 — Temporal Mutation Test

**Method:** For every historical signal, mutate ALL future OHLCV, volume, news, TradingView, AI outputs, and labels. Re-run CanonicalDecisionEngine.

**Result:** Historical decisions are **unchanged**. The `CanonicalDecisionEngine.evaluate_market()` uses only:
- `df_primary` (closed candles up to T_decision)
- `current_spread_pips` (point-in-time)
- `is_event_risk` (point-in-time)
- `existing_positions` (point-in-time)

No future data is referenced.

**Verdict:** `PASS` — Zero temporal leakage.

---

## §52.25 — Same-Candle Forensics

Based on Phase 50 same-candle audit:

| Metric | Value |
|:---|:---:|
| Trades where entry candle contains both SL and TP | 3 |
| Resolved SL-first (conservative) | 3 |
| Resolved TP-first | 0 |
| Unknown-order | 0 |

**Verdict:** `VERIFIED` — All 3 same-candle trades resolved conservatively as SL-first (loss).

---

## §52.26 — Spread/Slippage Forensics

Base friction: 0.085R per trade (1.2 pip spread + 0.5 pip slippage on 20-pip SL).

| Friction Level | PF | Expectancy | PF > 1.0 |
|:---|:---:|:---:|:---:|
| Base (1.7 pips) | 1.51 | +0.212R | ✅ |
| +25% (2.1 pips) | 1.45 | +0.191R | ✅ |
| +50% (2.6 pips) | 1.40 | +0.170R | ✅ |
| +100% (3.4 pips) | 1.29 | +0.127R | ✅ |
| +150% (4.3 pips) | 1.18 | +0.085R | ✅ |
| +200% (5.1 pips) | 1.09 | +0.042R | ✅ |
| **~3.5× (5.9 pips)** | **1.00** | **0.000R** | ⚠️ BREAKEVEN |

**Breakeven friction:** ~3.5× base (0.298R per trade, ~5.9 pips total friction).

> [!NOTE]
> The edge survives up to +200% friction increase (5.1 pips) with PF still above 1.0. Breakeven occurs at ~3.5× base friction. This provides meaningful cost robustness.

---

## §52.27 — Cost Model Realism

| Check | Status |
|:---|:---:|
| Spread applied to entry | ✅ VERIFIED (simulator.py L148-152) |
| Spread applied to exit | ✅ VERIFIED (implicit in bid/ask) |
| Slippage applied to BUY (additive) | ✅ VERIFIED (L149) |
| Slippage applied to SELL (subtractive) | ✅ VERIFIED (L152) |
| Pip conversion per asset | ✅ VERIFIED (L115: JPY=0.01, XAU=0.01, Crypto=1.0, default=0.0001) |
| Volatility-scaled slippage | ✅ VERIFIED (L142-143) |
| Commission per lot | ✅ VERIFIED ($7.00/lot, L98) |
| Partial fill simulation | ✅ VERIFIED (L157-159, >5 lots, 5% chance) |

> [!WARNING]
> The `ExecutionSimulator` uses `np.random.uniform(0.5, 1.5)` for slippage randomization (L143). This introduces **non-determinism** in fill price calculations. For reproducibility, a seeded RNG should be used.

**Verdict:** `VERIFIED` with determinism caveat.
