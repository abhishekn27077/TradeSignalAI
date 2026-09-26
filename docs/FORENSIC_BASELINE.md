# Phase 0 — Pre-Remediation Forensic Baseline

**Recorded Date**: 2026-09-26T16:42:00+05:30  
**Environment**: Windows, Python 3.11.15, Node v24+, Vite 8.1.5, SQLite 3  
**Repository**: `TradeSignalAI-v3` (`d:\trading Bots\FinalTrade\TradeSignalAI-v3`)  
**Git Head Commit**: `8b7e502` on branch `master`  

---

## 1. System Entrypoints & Architecture Inventory

1. **Backend Entrypoint**:
   - `app/main.py`: FastAPI application mounting 22 API routers (`/api/v1/auth`, `/api/v1/signals`, `/api/v1/terminal`, `/api/v1/system`, etc.) and WebSocket `/ws`.
2. **Frontend Entrypoint**:
   - `frontend/src/main.tsx` -> `frontend/src/App.tsx`: React 19.2 + TypeScript + Vite SPA, Ant Design UI, lightweight-charts.
3. **Signal Generation Pipelines**:
   - **Pipeline A (Legacy/Ensemble)**: `app/strategies/strategy_manager.py` -> `app/agents/lifecycle_manager.py` -> `app/strategies/execution_coordinator.py`.
   - **Pipeline B (Canonical)**: `app/services/canonical_signal_service.py` -> `app/core/canonical_prospective_ledger.py`.
   - **Pipeline C (Signal Factory / Phase 62+)**: `app/signals/signal_factory.py` (String-hash pseudo-generation).
4. **Execution & Paper Trading**:
   - `app/core/execution_abstraction.py`: Blocks real money (`REAL_MONEY_ENABLED = False`).
   - `app/execution/paper_executor.py`: In-memory and SQLite paper execution simulator.
5. **Market Data Providers**:
   - `app/core/market_data_service.py`: Queries `tradesignal.db` (`market_data` table, 251,000 candles). Falls back to `SyntheticFeed` on error.
6. **Authentication & Authorization**:
   - `app/core/auth.py`: JWT-based token generation and password verification. `get_current_user` dependency implemented but only bound to 4 routes.
7. **Model / AI / Kronos Pipeline**:
   - `app/analytics/models/kronos/kronos_forensic_evaluator.py`: PyTorch-based sequence modeling with CPU fallback.

---

## 2. Test Suite Baseline Execution

Command executed:
```bash
python -m pytest tests/ -q
```

### Quantitative Baseline Results:
- **Total Tests Collected**: **958**
- **Passed**: **949**
- **Failed**: **9**
- **Skipped**: **0**
- **Errors**: **0**
- **Execution Time**: **170.69 seconds (02:50)**
- **Warnings**: 119 (datetime deprecations, asyncio deprecations)

### Baseline Failures Log:
1. `tests/test_deterministic_signal_reproduction.py::test_deterministic_signal_reproduction_across_runs`
2. `tests/test_forecast_immutability.py::test_shadow_prediction_immutability`
3. `tests/test_forecast_immutability.py::test_prediction_revisioning_via_supersedes_id`
4. `tests/test_live_duplicate_protection.py::test_duplicate_signal_influx_protection`
5. `tests/test_model_version_freezing.py::test_model_version_freezing_in_prediction`
6. `tests/test_phase48_runtime_truth.py::test_phase48_honest_no_trade_consensus`
7. `tests/test_phase58_5_canonical_pipeline.py::test_granular_no_trade_reasons`
8. `tests/test_phase58_5_canonical_pipeline.py::test_duplicate_state_prevention`
9. `tests/test_phase69a_terminal_canonical_ledger.py::test_yesterday_retrieval_consistency`

---

## 3. Frontend Production Build Baseline

Command executed:
```bash
cd frontend && npm run build
```

### Build Result:
- **Command**: `tsc -b && vite build`
- **Output Status**: **PASSED (0 TypeScript errors)**
- **Modules Transformed**: 6,341
- **Bundle Output**:
  - `dist/index.html`: 0.90 kB
  - `dist/assets/index-*.css`: 100.75 kB (gzip: 15.06 kB)
  - `dist/assets/index-*.js`: 3,129.61 kB (gzip: 882.19 kB)
- **Execution Time**: **4.24 seconds**

---

## 4. Key Pre-Remediation Vulnerabilities & Invariants

1. **Rule Zero**: Unconditionally locked (`REAL_MONEY_ENABLED = False`).
2. **Authentication Surface**: 61 state-changing endpoints accessible without authentication.
3. **Analytics Integrity**: Hardcoded static dictionaries in `no_trade_engine.py`, `ablation_engine.py`, `prediction_reality_engine.py`, and `latency_monitor.py`.
4. **Market Data Fail-Open**: Disconnection defaults to synthetic price generation (`ASSET_BASE_PRICES`).
5. **Deduplication**: `SignalIdentityGuard` returns `False` on storage error and is bypassed in the execution hot path.
