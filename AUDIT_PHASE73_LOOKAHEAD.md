# Phase 73 — Point-in-Time & Look-Ahead Bias Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **LOOK-AHEAD LEAKAGE DEFECTS CONFIRMED**

---

## 1. Executive Summary

An adversarial forensic inspection of rolling calculations, pivot detection, resamplings, database queries, and shadow predictions was conducted to ensure no future information is accessible at prediction time $T$.

Two significant look-ahead vulnerabilities were discovered in the codebase:
1. **Centering in Pivot Rolling Window (`center=True` in `market_structure.py`).**
2. **Unconstrained Date Fallback in `shadow_live_engine.py:249`.**

---

## 2. Forensic Findings

### Vulnerability 1: Centered Rolling Windows in Market Structure (`center=True`)
- **Location:** `app/strategies/indicators/market_structure.py:82-84`
- **Code:**
  ```python
  window = self.pivot_left + self.pivot_right + 1
  rolling_max = df['high'].rolling(window=window, center=True).max()
  rolling_min = df['low'].rolling(window=window, center=True).min()
  ```
- **Mechanism:**
  When `center=True` is used on a rolling window of length 11 (5 left, 5 right + 1), the calculation for bar $i$ uses values from bar $i - 5$ to bar $i + 5$.
- **Impact:**
  During historical backtesting or batch re-evaluation, pivot highs and lows at index $i$ are identified using future bars up to $i + 5$. A strategy evaluating pivots on historical data will identify swing highs/lows before the market actually forms them in real time.
- **Remediation:** Remove `center=True`. Calculate pivots using trailing windows only, confirming a pivot at bar $i$ only after $N$ subsequent bars have closed below/above it (lagged pivot confirmation).

---

### Vulnerability 2: Unconstrained Candle Fallback in `shadow_live_engine.py`
- **Location:** `app/shadow/shadow_live_engine.py:247-250`
- **Code:**
  ```python
  now = reference_dt or datetime.now(timezone.utc)
  rows = self._fetch_candles_from_candidates(asset, limit=120, before_iso=now.isoformat())
  if not rows or len(rows) < 30:
      rows = self._fetch_candles_from_candidates(asset, limit=120)
  ```
- **Mechanism:**
  When evaluating historical point-in-time predictions with `reference_dt`, if the database has fewer than 30 bars before `reference_dt`, line 249 fetches the latest 120 bars from the database **without any timestamp upper bound**.
- **Impact:**
  Historical predictions generated near the beginning of a dataset silently consume recent candles up to the current day.
- **Remediation:** Delete line 249. If `len(rows) < 30`, fail closed and return `NO_TRADE` with `INSUFFICIENT_DATA`.

---

### Vulnerability 3: Shift / Rolling Alignment in Indicators
- **`app/strategies/indicators/volatility.py:21`:**
  `close = df['close'].shift(1)`
  *Audit Verdict:* **CLEAN.** Correctly shifts previous close for True Range calculation at bar $t$.
- **`app/core/canonical_signal_service.py:162-167`:**
  Candles loaded from SQLite are sorted strictly by `timestamp ASC` before computing rolling features.
  *Audit Verdict:* **CLEAN.** No negative shifts (`shift(-1)`) or forward fills across timestamps.

---

## 3. Verdict
**FAIL / LOOK-AHEAD DEFECTS PRESENT.** Centered rolling windows in market structure and unconstrained date fallbacks in the shadow engine allow future data leakage during backtesting and retrospective validation.
