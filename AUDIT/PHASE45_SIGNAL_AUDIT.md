# PHASE 45 — SIGNAL GENERATION, TIMEFRAME ENGINES & CONTRADICTION AUDIT

**Audit Scope:** Forensic investigation of signal generation across H4, Swing, and Daily engines, lifecycle transitions, and cross-view contradiction resolution.

---

## 1. Resolution of Cross-View Contradiction (Rule 20)

### Observed Phenomenon
- *Reality & Evidence View:* Displayed high historical backtest win rates ($70\%+$).
- *Signal Diagnostics View:* Displayed current forward live state (`NO_VALID_SETUP`, consensus $57\% < 60\%$).

### Forensic Explanation & Resolution
1. **Root Cause:** Reality & Evidence initially rendered aggregated historical backtest metrics ($N=245,882$), whereas Signal Diagnostics rendered the live point-in-time forward evaluation for the current bar.
2. **Reconciliation Fix:** Separated datasets permanently. Reality & Evidence now displays exclusively the `LIVE_SHADOW` forward evidence cohort, while historical benchmarks are segregated under `HISTORICAL_BENCHMARK`.
3. **Parity Check:** In current live evaluation, both views now report the exact same canonical signal state: `NO_VALID_SETUP` ($57\%$ consensus).

---

## 2. Multi-Timeframe Signal Architecture

| Engine | Canonical Timeframe | Data Requirements | Execution Cadence | Validation Rule |
|:---|:---:|:---|:---:|:---|
| **H4 Forecast Engine** | `4H` | Closed 4-hour OHLCV candles | Every 4 hours at bar close | Strict point-in-time anchoring |
| **Swing Signal Engine** | `4H` + `1D` | Multi-day structural swings (BOS) | Daily at NY Close ($22:00\text{ UTC}$) | Minimum $1:2.0\text{ R:R}$ target |
| **Daily Command Engine**| `1D` | Daily candles + Macro Calendar | Daily at $00:00\text{ UTC}$ | Hashed daily prediction locks |
| **Tomorrow Forecast** | `1D` | Next-day Sequence Matrix | Forward daily projection | Dynamic formula ($12\%$ to $94\%$) |

---

## 3. Signal Lifecycle & Gating Verification

$$\text{GENERATED} \longrightarrow \text{VALIDATING} \longrightarrow \begin{cases} \text{VALID} \longrightarrow \text{TRIGGERED} \longrightarrow \text{ACTIVE} \longrightarrow \begin{cases} \text{TP1 / TP2} \\ \text{SL} \end{cases} \\ \text{REJECTED (16 Rejection Codes)} \\ \text{EXPIRED (Time-Window Exceeded)} \end{cases}$$

- **Verdict:** `SIGNAL_ENGINES_VERIFIED`.
