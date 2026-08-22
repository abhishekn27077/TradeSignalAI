# PHASE 36 PRE-AUDIT REPORT
## 1. Architecture Map
**CORE INTELLIGENCE**: ConsensusEngine, KronosAdapter, MasterIntelligenceEngine, FAISS Historical Analog.
**PIPELINE**: PipelineOrchestrator, CandleClock, IST conversion, NextSignalEngine.
**RISK & EXECUTION**: RiskEngine v2, PaperExecutor, OutcomeEngine, SignalStateMachine.
**STORAGE**: SQLite Database (`trading_fallback.db`), EvidenceLedger.
**DELIVERY**: FastAPI REST endpoints, WebSocket Manager.
**FRONTEND**: React (Zustand state management in `useAppStore.ts`, Dashboard pages).

## 2. Signal Data Flow
REAL MARKET DATA -> FEATURE ENGINE -> QUANT MODELS -> KRONOS -> FAISS -> RISK ENGINE -> SIGNAL IDENTITY -> DATABASE -> API / WEBSOCKET -> ZUSTAND STORE -> REACT COMPONENTS.

## 3. API Endpoints
- `/api/v1/signals/history`: Fetches past signals.
- `/api/v1/forecast/predictions/current`: Fetches predictions.
- `/api/v1/health/status`: System health.

## 4. WebSocket Events
- `system`, `signals`, `orders`, `positions`, `portfolio`, `risk`, `ai`, `news`, `ticks`
- `signal_generated`, `system_health`, `order_update`

## 5. Database Tables/Models
- `SignalLifecycleModel`: Master record for signals including `trace_id`, `outcome`, `net_pnl`, `duplicate_protection_hash`.

## 6. Frontend Pages
- `TradingDashboard.tsx`, `Signals.tsx`, `TodaysSignals.tsx`, `H4Forecasts.tsx`, `SwingSignals.tsx`, `SignalHistory.tsx`.

## 7. Frontend Data Dependencies
- `useAppStore.ts` manages the state for all incoming WebSocket and REST API data.

## 8. Existing Tests
- Extensive test suite mapped to Phase 33/35 engines (`test_phase35_ablation.py`, `test_phase33_signal_lifecycle.py`, etc.). Over 122 tests exist and pass.

## 9. Existing Zero-Trust Rules
- Signal duplication prevention (SHA-256 hash).
- Phase 35 ablation strict testing.
- Database schema supports trace_ids across pipeline.

## 10. Known Gaps & Defect Origins
- **Fabricated Confidence (UI)**: `useAppStore.ts` explicitly maps `confidence: a.confidence ?? 50` across multiple entities.
- **Fabricated Accuracy (UI)**: `TradingDashboard.tsx` uses `historical_accuracy ? ... : '85.4%'`.
- **Backend Synthetic Defaults**: `app/strategies/scoring/trade_quality.py` uses `signal.get("confidence", 0.5)`.
- **Mismatch in Counts**: Dashboard signal count disagrees with Today's Signals due to incorrect filtering/mapping across endpoints and store.
- **Empty States vs Null Fallbacks**: The frontend actively mutates missing values (e.g. 0, 50, 85.4) instead of gracefully handling them via `UNAVAILABLE` strings.

## 11. Suspected Integration Mismatches
- **Current Price & Timestamps**: The frontend expects specific field names (`current_price`, `entry_zone`) which may be missing from the WebSocket payload, triggering fallbacks.
- **Signal Filtering**: API `history(50)` might be pulling all lifecycle states instead of just `active`/`completed`.
