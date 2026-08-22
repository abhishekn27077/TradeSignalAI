# PHASE 46.1 — AUDIT BASELINE FREEZE & ENVIRONMENT PROFILE

**Freeze Date (UTC):** `2026-08-22T21:09:35Z`  
**Git Baseline Commit:** `d7844ea`  
**Git Tag:** `phase-45-certified`  
**Configuration Fingerprint:** `CONFIG_HASH = 79a4f8e12b79310d`  
**Real-Money Execution Status:** `STRICTLY_DISABLED`

---

## 1. System Runtime Profile

| Profile Dimension | Verified Setting / Value | Invariant Status |
|:---|:---|:---:|
| **Python Runtime** | Python 3.14.3 (Windows 64-bit) | Locked |
| **FastAPI Framework** | FastAPI 0.115+, Uvicorn 0.32+ | Locked |
| **Frontend Framework** | React 18.3.1, TypeScript 5.5, Vite 5.4 | Locked |
| **Database Engine** | SQLite 3.45 (`tradesignal.db`, 42 tables) | Locked |
| **Primary Data Feeds** | Yahoo Finance (`yfinance` 0.2.40), TradingView Adapter | Locked |
| **Supermajority Rule** | $60.0\%$ directional consensus across active clusters | Locked |
| **Collinearity Dampener**| Factor $\frac{1}{\sqrt{K}}$ per correlation cluster | Locked |
| **Risk Circuit Breaker** | $5.0\%$ daily drawdown stop, $3.0$ lot currency exposure cap | Locked |
| **Core Asset Universe** | 9 Assets: BTC, ETH, EUR, GBP, JPY, AUD, XAU, NAS, SPX | Locked |
| **Primary Timeframe** | 1H Execution (with 4H & 1D Multi-Timeframe Confirmation) | Locked |

---

## 2. Invariant State Enforcement

All trading logic, indicator algorithms, model parameters, and risk thresholds are frozen. Phase 46 audits runtime reality and code execution paths without optimizing parameters against forward evaluation sets.
