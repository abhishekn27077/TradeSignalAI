# PHASE 75 — Forensic Baseline Audit

**Date**: 2026-09-27  
**Execution Context**: Independent Zero-Trust Audit & Remediation  
**Status**: ACTIVE BASELINE (Unremediated)

---

## 1. Initial Test Run Summary

Executed: `pytest tests/ -q --tb=short`
- **Total Tests Collected**: 1032
- **Passed**: 1026
- **Failed**: 6
- **Runtime**: 144.74s

### Confirmed Test Failures & Root Causes

1. **`tests/test_latency_monitor.py::test_latency_percentile_calculation`**
   - **Error**: `AssertionError: assert 'SLA_BREACH' == 'WITHIN_PRODUCTION_SLA'`
   - **Root Cause**: The test asserts that latency conforms to an unrealistic hardcoded production SLA (~183ms), whereas measured pipeline latency on actual execution breaches this threshold (`SLA_BREACH`).

2. **`tests/test_phase60_snapshot_integrity.py::test_market_data_freshness_enforcement`**
   - **Error**: `assert 141780.823483 < 7200.0`
   - **Root Cause**: The active snapshot in the test environment contains market data from Friday market close (age ~141,780 seconds / ~39.4 hours on Sunday), exceeding the test's static 2-hour window.

3. **`tests/test_single_source_of_truth_pipeline.py` (4 tests failing)**:
   - `test_all_market_statuses_returns_all_9_assets`
   - `test_bootstrap_sequence_generates_comprehensive_report`
   - `test_market_status_api_endpoint`
   - `test_bootstrap_status_api_endpoint`
   - **Error**: `AssertionError: assert 11 == 9`
   - **Root Cause**: `AssetTradingCalendar.ASSET_SCHEDULES` currently has 11 assets because `BTCUSDT` and `ETHUSDT` were registered alongside legacy `BTCUSD` and `ETHUSD`.

---

## 2. Codebase Forensic Defect Census

### Defect 1: Lookahead Bias in Indicators & Features
- **Files**:
  - `app/strategies/price_action/support_resistance.py` (Lines 21-22): `rolling(window=self.window, center=True).max()`
  - `app/strategies/indicators/otc/liquidity_sweep.py` (Lines 291-292): `rolling(window=window, center=True).max()`
  - `app/market_data/feature_store.py` (Lines 40-41): `rolling(window=5, center=True).max()`
- **Impact**: `center=True` incorporates future candles to identify peaks and troughs at the current index, introducing severe lookahead bias in historical and backtesting evaluation.

### Defect 2: Fabricated Metrics & Hash Arithmetic
- **Files**:
  - `app/core/signal_factory.py` (Line 330): `direction = "BUY" if (seed % 3 == 0) else ("SELL" if (seed % 3 == 1) else "WAIT")`
  - `app/analytics/daily_signal_journal.py` (Line 124): `is_win = (h % 3 != 0)  # ~66% win rate benchmark`
  - `app/analytics/paper_portfolio_engine.py` (Line 156): `is_win = (i % 3 != 0)`
  - `app/analytics/asset_timeframe_matrix_engine.py` (Lines 66, 72, 78, 94): Hardcoded Brier scores (`0.160 + ((seed_val % 30) / 1000.0)`) and drawdown percentages.
- **Impact**: Synthetic pseudo-random numbers and deterministic hash arithmetic manufacture win rates and calibration metrics rather than deriving them from actual trade outcomes.

### Defect 3: Permissive State-Changing API Endpoints
- **Files**:
  - `app/api/middleware.py`: `StateChangingAuthMiddleware` contains exemptions in `READ_ONLY_POST_PATHS` including mutating actions:
    - `/api/v1/signals/auto-resolve`
    - `/api/v1/signals/run-cycle`
    - `/api/v1/signals/resolve-due`
  - Multiple sub-routers declare POST/PUT/DELETE routes without `Depends(get_current_user)` or `Depends(require_role)`.
- **Impact**: Unauthenticated callers can trigger signal resolution, run engine cycles, or modify server state.

### Defect 4: Risk Engine Missing SL/TP Fail-Open Vulnerability
- **Files**:
  - `app/core/risk_engine.py` / `app/core/execution_coordinator.py`
- **Impact**: If a trade proposal lacks Stop Loss or Take Profit, or if the risk validation method encounters an unhandled exception, it must strictly fail closed (REJECT), not pass by default.

### Defect 5: Signal Deduplication Fail-Open Vulnerability
- **Files**:
  - `app/core/signal_identity_guard.py`
- **Impact**: If database connection or query fails during duplicate verification, the system must fail closed (REJECT / DEDUPLICATION_UNAVAILABLE), never allow the duplicate signal through.

### Defect 6: Walk-Forward Engine Strategy Fidelity
- **Files**:
  - `app/analytics/walk_forward_engine.py`
- **Impact**: Toy EMA rule (`c > ema20`) was used as a stand-in for full strategy logic, giving unrepresentative walk-forward results.

### Defect 7: RSI / Indicator Parity
- **Files**:
  - `app/strategies/indicators/rsi.py` (or equivalent technical indicator modules)
- **Impact**: Using Cutler's SMA-based RSI instead of Wilder's RMA-based RSI diverges from standard TradingView / MetaTrader calculation.

---

## 3. Plan of Remediation
All remediations will be applied iteratively with dedicated regression tests across Sections 2-28 of Phase 75.
