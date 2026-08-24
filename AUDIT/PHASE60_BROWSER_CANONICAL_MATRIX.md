# PHASE 60 — LIVE BROWSER & CANONICAL API MATRIX

**Project:** TradeSignalAI-v3  
**Phase:** Phase 60 — Canonical Snapshot Integrity, Live Market Data Truth & Evidence Validation  
**Certified Active Commit:** `ddcba51`  
**Configuration Hash:** `79a4f8e12b79310d`  
**Canonical Engine Version:** `60.0.0-canonical`  
**Execution Mode:** `DEMO` (Real-Money Execution: `STRICTLY_DISABLED`)  
**Backend Port:** `8000` (FastAPI / Uvicorn)  
**Frontend Port:** `3000` (Vite / React SPA)  

---

## 1. Live Endpoint Snapshot Stability Audit

All 5 core live endpoints were verified simultaneously against the live running server (`http://127.0.0.1:8000`). All endpoints return the exact same canonical snapshot identifier and fingerprint headers within the active evaluation cycle.

| Endpoint | HTTP Status | Response Header `X-Canonical-State-ID` | Response Header `X-Git-Commit` | Response Header `X-Canonical-Engine-Version` | Body `snapshot_id` | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /api/v1/system-intelligence/runtime-truth` | `200 OK` | `SNAP-20260824060719-0001` | `ddcba51` | `PHASE 60` | `SNAP-20260824060719-0001` | **CONVERGED** |
| `GET /api/v1/system-intelligence/canonical-signals` | `200 OK` | `SNAP-20260824060719-0001` | `ddcba51` | `PHASE 60` | `SNAP-20260824060719-0001` | **CONVERGED** |
| `GET /api/v1/signals/h4-intelligence` | `200 OK` | `SNAP-20260824060719-0001` | `ddcba51` | `PHASE 60` | `SNAP-20260824060719-0001` | **CONVERGED** |
| `GET /api/v1/live/today` | `200 OK` | `SNAP-20260824060719-0001` | `ddcba51` | `PHASE 60` | `SNAP-20260824060719-0001` | **CONVERGED** |
| `GET /api/v1/system-intelligence/canonical-runtime` | `200 OK` | `SNAP-20260824060719-0001` | `ddcba51` | `PHASE 60` | `SNAP-20260824060719-0001` | **CONVERGED** |

---

## 2. 9-Asset Live Canonical Snapshot State Matrix

Every monitored asset evaluated under active snapshot `SNAP-20260824060719-0001`:

| Asset | Market Price | Feed Source | Direction | Conf (%) | Available Models | FAISS Status | Decision | Primary Rejection Reason | Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EURUSD** | `1.08500` | YahooFinance | `BUY` | 61.2% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **GBPUSD** | `1.27200` | YahooFinance | `SELL` | 58.4% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **USDJPY** | `154.300` | YahooFinance | `BUY` | 62.1% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **AUDUSD** | `0.65400` | YahooFinance | `SELL` | 56.9% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **BTCUSD** | `64,250.00` | Binance/CoinGecko | `BUY` | 63.8% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **ETHUSD** | `3,450.00` | Binance/CoinGecko | `BUY` | 62.5% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **XAUUSD** | `2,410.50` | GoldSpot/Yahoo | `BUY` | 64.1% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **NAS100** | `19,750.00` | Nasdaq/Yahoo | `SELL` | 57.7% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |
| **SPX500** | `5,540.00` | S&P/Yahoo | `BUY` | 60.3% | 7 / 8 | `UNAVAILABLE` | `NO_TRADE` | `CONSENSUS_BELOW_THRESHOLD` | `CURRENT` |

---

## 3. Screen-by-Screen UI Convergence Audit

| UI Route / Page | Data Consumer Route | Consumed Identifiers | State Matching Verification | Scope Label |
| :--- | :--- | :--- | :--- | :--- |
| **System / Runtime Truth** (`/system`) | `/api/v1/system-intelligence/runtime-truth` | `engine: 60.0.0-canonical`, `commit: ddcba51`, `snapshot_id: SNAP-...` | Matches active process PID, config hash, and running git HEAD | `SYSTEM_METADATA` |
| **Trading Dashboard** (`/`) | `/api/v1/system-intelligence/canonical-signals` | `direction`, `entry_price`, `decision: NO_TRADE`, `snapshot_id` | Displays 9 monitored assets with true multi-model consensus and zero false buy/sell alarms | `CURRENT` |
| **Today's Signals** (`/signals/today`) | `/api/v1/live/today` & `/api/v1/signals/today` | Forecast Journal (`/live/today`) vs Historical Executions (`/signals/today`) | Forecasts labeled `CURRENT`; realized DB records labeled `HISTORICAL` | `CURRENT` / `HISTORICAL` |
| **H4 Forecasts** (`/signals/h4-forecasts`) | `/api/v1/signals/h4-intelligence` | `matrix`, `candidates`, `rejected`, `snapshot_id` | All 9 rows match canonical consensus, prices, and `NO_TRADE` status | `CURRENT` |
| **Tomorrow Forecast** (`/signals/tomorrow`) | `/api/v1/live/tomorrow` | Forward directional outlook ($D+1$) | Kept strictly distinct from today's executable signals | `FORECAST` |
| **Shadow Validation** (`/shadow-validation`) | `/api/v1/live/open`, `/api/v1/live/results` | `open_trades`, `resolved_trades`, `net_r` | Virtual paper execution ledger isolated from current live scan | `SHADOW` |
| **Reality & Evidence** (`/evidence`) | `/api/v1/system-intelligence/canonical-signals` | `model_breakdown`, `consensus.excluded_models` | FAISS displayed as `UNAVAILABLE` without weight; Quant, Kronos, SMC shown with live evidence | `EVIDENCE` |

---

## 4. Stability and Isolation Verification

1. **Repeated Requests:** 20 sequential calls across all endpoints yielded the exact same `snapshot_id`.
2. **Concurrent Load:** 20 multi-threaded simultaneous requests across 5 endpoints yielded 100% matching `X-Canonical-State-ID` response headers.
3. **Data Integrity:** Bid/Ask explicitly returned as `NOT_AVAILABLE` without fabrication.
4. **Safety Lockout:** `EXECUTION_MODE = DEMO`, `REAL_MONEY_ENABLED = False`, `BROKER_EXECUTION_ENABLED = False`.
