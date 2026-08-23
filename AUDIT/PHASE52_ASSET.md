# PHASE 52 — ASSET FORENSICS

---

## §52.31 — Asset Forensics

| Asset | N Signals | N Realized | Wins | Losses | WR | PF | Expectancy | WR 95% CI | Sample Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---:|
| EURUSD | 18 | 7 | 5 | 2 | 71.43% | 2.12 | +0.54R | [29.0%, 96.3%] | `INSUFFICIENT` |
| XAUUSD | 16 | 6 | 4 | 2 | 66.67% | 1.95 | +0.44R | [22.3%, 95.7%] | `INSUFFICIENT` |
| BTCUSD | 14 | 5 | 4 | 1 | 80.00% | 1.88 | +0.52R | [28.4%, 99.5%] | `INSUFFICIENT` |
| GBPUSD | 14 | 5 | 3 | 2 | 60.00% | 1.72 | +0.30R | [14.7%, 94.7%] | `INSUFFICIENT` |
| USDJPY | 12 | 4 | 2 | 2 | 50.00% | 1.38 | +0.12R | [6.8%, 93.2%] | `INSUFFICIENT` |
| AUDUSD | 12 | 4 | 2 | 2 | 50.00% | 1.42 | +0.14R | [6.8%, 93.2%] | `INSUFFICIENT` |
| NAS100 | 14 | 4 | 2 | 2 | 50.00% | 1.55 | +0.18R | [6.8%, 93.2%] | `INSUFFICIENT` |
| USDCAD | 10 | 4 | 2 | 2 | 50.00% | 1.48 | +0.16R | [6.8%, 93.2%] | `INSUFFICIENT` |
| ETHUSD | 8 | 3 | 2 | 1 | 66.67% | 1.65 | +0.30R | [9.4%, 99.2%] | `INSUFFICIENT` |

> [!CAUTION]
> **ALL 9 assets have N_realized < 30**, placing every asset in `INSUFFICIENT_SAMPLE` territory. The per-asset PF rankings are point estimates only — every single 95% CI spans from near-0% to near-100% win rate.

### Key Findings

1. All 9 assets show **positive point-estimate expectancy** — this is promising but not statistically significant per-asset
2. The aggregate system (N=42 across all assets) is the only defensible statistical unit
3. **EURUSD** has the most trades (7) but still far below N=30
4. Asset-level rankings should be treated as **exploratory hypotheses**, not confirmed findings

---

## §52.33 — Out-of-Sample Boundary

| Check | Status |
|:---|:---:|
| All 42 trades generated after strategy freeze | ✅ VERIFIED |
| No pre-freeze observation counted as forward evidence | ✅ VERIFIED |
| Freeze timestamp: `CONFIG_HASH = 79a4f8e12b79310d` | ✅ VERIFIED |

---

## §52.34 — Forward Sample Governance

| Threshold | Status | Required For |
|:---|:---:|:---|
| N ≥ 30 | ✅ PASSED | `EARLY_FORWARD_EVIDENCE` |
| N ≥ 100 | ❌ NOT MET | `PRELIMINARY_EVIDENCE` |
| N ≥ 200 | ❌ NOT MET | Increased confidence |
| N ≥ 300 | ❌ NOT MET | `STRONGER_FORWARD_EVIDENCE` |

**Current Classification:** `EARLY_FORWARD_EVIDENCE` (N=42, Tier 2)

**Required checkpoints remaining:**
- 100 realized trades
- 200 realized trades
- 300 realized trades

**Classification:** `VERIFIED` — governance rules correctly applied.
