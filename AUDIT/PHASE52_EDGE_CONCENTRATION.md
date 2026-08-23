# PHASE 52 — EDGE CONCENTRATION & DEPENDENCY ANALYSIS

---

## §52.10 — Top-Trade Dependency

| Removed | PF | Expectancy | Win Rate | Edge Positive |
|:---|:---:|:---:|:---:|:---:|
| None (baseline) | 1.78 | +0.297R | 61.90% | ✅ |
| Top 1 trade | 1.65 | +0.254R | 60.98% | ✅ |
| Top 3 trades | 1.46 | +0.187R | 58.97% | ✅ |
| Top 5 trades | 1.28 | +0.119R | 56.76% | ✅ |
| Top 10 trades | **0.89** | **-0.057R** | 50.00% | ❌ |
| Top 20% (8 trades) | **1.04** | **+0.017R** | 52.94% | ⚠️ MARGINAL |

> [!WARNING]
> **Removing the top 10 trades destroys the edge entirely** (PF=0.89, negative expectancy). Removing top 20% (8 trades) leaves the edge barely positive at PF=1.04. This indicates **MODERATE concentration** — the system's profitability depends on capturing its best trades.

**Classification:** `MODERATELY_CONCENTRATED`

---

## §52.11 — Best-Asset Dependency

Based on Phase 51 reported asset PF values and approximate trade counts:

| Removed Assets | Approx Remaining PF | Edge Positive |
|:---|:---:|:---:|
| EURUSD (best) | 1.68 | ✅ |
| EURUSD + XAUUSD | 1.55 | ✅ |
| Top 3 (EURUSD + XAUUSD + BTCUSD) | 1.38 | ✅ |

> [!NOTE]
> Edge remains positive after removing the top 3 assets, though diminished. Asset diversification provides meaningful resilience.

---

## §52.12 — Horizon Dependency

Based on Phase 51 horizon data:

| Removed | Remaining Horizons | Approx PF | Edge Positive |
|:---|:---|:---:|:---:|
| H4 (best) | H1, Swing, Daily | 1.71 | ✅ |
| H1 (primary) | H4, Swing, Daily | 1.82 | ✅ |
| H4 + H1 | Swing, Daily only | ~1.52 | ✅ (marginal) |

> [!NOTE]
> H4 and H1 are co-dominant. Removing both leaves only Swing/Daily with limited sample but still positive PF. The system is **not single-horizon dependent**.

---

## §52.13 — Regime Dependency

| Removed | Remaining PF | Edge Positive |
|:---|:---:|:---:|
| TRENDING_BULL | 1.61 | ✅ |
| TRENDING_BEAR | 1.65 | ✅ |
| Both TRENDING | ~1.15 | ⚠️ MARGINAL |

> [!WARNING]
> Removing both trending regimes reduces PF to ~1.15. The system is **fundamentally trend-dependent**. This is expected for a momentum/structure-based strategy but means performance degrades significantly in ranging/choppy markets.

**Classification:** `TREND_DEPENDENT` (not regime-diversified)

---

## §52.32 — Edge Concentration Classification

| Dimension | Impact of Removal | Classification |
|:---|:---|:---:|
| Top 10 trades | Edge destroyed (PF < 1.0) | `CONCENTRATED` |
| Top 20% trades | Edge marginal (PF ≈ 1.04) | `CONCENTRATED` |
| Best asset | Edge survives (PF = 1.68) | `DIVERSIFIED` |
| Top 3 assets | Edge survives (PF = 1.38) | `DIVERSIFIED` |
| Best horizon | Edge survives (PF = 1.71) | `DIVERSIFIED` |
| Both trending regimes | Edge marginal (PF ≈ 1.15) | `CONCENTRATED` |

**Overall Classification:** `MODERATELY_CONCENTRATED`

The edge is concentrated in:
1. **Top trades** — removing the best 10 of 42 eliminates profitability
2. **Trending regimes** — system is fundamentally trend-dependent
3. But **diversified across assets and horizons**
