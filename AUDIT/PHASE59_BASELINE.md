# PHASE 59 — CANONICAL RUNTIME BASELINE AUDIT

**Project:** TradeSignalAI-v3  
**Audit Timestamp:** 2026-08-24T11:08:00+05:30  
**Current Git Commit:** `94af80a`  
**Current Config Hash:** `79a4f8e12b79310d`  
**Execution Mode:** `DEMO` (`REAL_MONEY == STRICTLY_DISABLED`)  

---

## 1. System Architecture & Entrypoints

### Backend Architecture
- **Framework:** FastAPI / Uvicorn (Python 3.11 / Python 3.14 on Windows)
- **Primary Entrypoint:** [app/main.py](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/main.py)
- **Main Router:** [app/api/router.py](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/api/router.py) $\rightarrow$ [app/api/v1/router.py](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/api/v1/router.py)
- **Authoritative Canonical Signal Service:** [app/core/canonical_signal_service.py](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/core/canonical_signal_service.py)
- **Database:** SQLite (`tradesignal.db`), accessed asynchronously via SQLAlchemy in `app/database/manager.py` and synchronously in point-in-time stores.

### Frontend Architecture
- **Framework:** React 19, TypeScript, Vite, TailwindCSS v4
- **Dev Server:** Port 3000 (`http://localhost:3000`)
- **API Proxy Configuration:** [frontend/vite.config.ts](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/vite.config.ts) proxies `/api` $\rightarrow$ `http://127.0.0.1:8000` and `/ws` $\rightarrow$ `ws://127.0.0.1:8000`.
- **API Client:** [frontend/src/services/api-client.ts](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/services/api-client.ts) (`API_BASE = '/api/v1'`)

---

## 2. Active Processes & Runtime Identification

- **Frontend Server:** PID `19728` (`node.exe` running `vite.js` on port `3000`).
- **Running Backend Server:** PID `19488` (`python.exe` running `uvicorn app.main:app --port 8000`).
  - **Start Timestamp of PID 19488:** `24-08-2026 10:24:05` (Executed without `--reload`).
  - **Root Cause of UI Discrepancy:** The running uvicorn process (PID 19488) held in-memory bytecode from 10:24 AM (prior to Phase 58.4/58.5 code updates). While pytest spawned fresh Python processes and passed 221/221 tests, browser requests to `http://localhost:3000` forwarded to PID 19488 which served outdated Phase 45 responses.

---

## 3. Signal Engine & Route Map

| Category | Endpoint | Backing Service | Intended Canonical Source |
| :--- | :--- | :--- | :--- |
| **Canonical Runtime** | `GET /api/v1/system-intelligence/canonical-runtime` | `CanonicalSignalService` | `canonical_signal_service.get_canonical_runtime_metadata()` |
| **Canonical Signals** | `GET /api/v1/system-intelligence/canonical-signals` | `CanonicalSignalService` | `canonical_signal_service.get_all_canonical_asset_states()` |
| **H4 Intelligence** | `GET /api/v1/signals/h4-intelligence` | `CanonicalSignalService` | `canonical_signal_service.get_h4_intelligence_matrix()` |
| **Daily Command Today** | `GET /api/v1/live/today` | `CanonicalSignalService` | `canonical_signal_service.get_today_journal()` |
| **Live Status** | `GET /api/v1/live/status` | `CanonicalSignalService` + Schedulers | `canonical_signal_service.get_canonical_runtime_metadata()` |
| **Qualified Signals** | `GET /api/v1/signals/today` | `SignalLifecycleModel` | Database table for realized qualified signals today |

---

## 4. Frontend Consumer Pages

| Frontend Page | Source File | API Endpoints Called |
| :--- | :--- | :--- |
| **Trading Dashboard** | [TradingDashboard.tsx](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/pages/TradingDashboard.tsx) | `/signals/live`, `/signals/h4-intelligence`, `/live/today` |
| **Today's Signals** | [TodaysSignals.tsx](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/pages/signals/TodaysSignals.tsx) | `/signals/today`, `/signals/yesterday`, `/live/today` |
| **H4 Forecasts** | [H4Forecasts.tsx](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/pages/signals/H4Forecasts.tsx) | `/signals/h4-intelligence` |
| **Daily Command** | [DailyCommandCenter.tsx](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/pages/forecasts/DailyCommandCenter.tsx) | `/live/today`, `/live/status`, `/live/models` |
| **Tomorrow Forecast** | [TomorrowForecast.tsx](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/pages/forecasts/TomorrowForecast.tsx) | `/forecast/tomorrow` |
| **System Intelligence** | [SystemIntelligence.tsx](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/frontend/src/pages/SystemIntelligence.tsx) | `/system-intelligence/canonical-runtime`, `/system-intelligence/canonical-signals` |

---

## 5. Required Phase 59 Hardening Steps

1. Implement `GET /api/v1/system-intelligence/runtime-truth` with live PID, working directory, git commit, branch, config hash, and start time.
2. Implement FastAPI Canonical Fingerprint Middleware adding `X-Canonical-Engine-Version`, `X-Git-Commit`, `X-Config-Hash`, `X-Canonical-State-ID`, `X-Generated-At`, and `X-Market-Data-Timestamp` headers to all responses.
3. Enhance `CanonicalSignalService` with unique `canonical_state_id` per evaluation snapshot and sub-second market data age calculation.
4. Restart the running backend server with fresh code and verify live runtime truth via HTTP end-to-end testing.
