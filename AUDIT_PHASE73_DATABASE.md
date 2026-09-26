# Phase 73 — Database Security & Integrity Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **PASS ON CONSTRAINTS & WAL / HIGH REPOSITORY STORAGE OVERHEAD**

---

## 1. Executive Summary

A comprehensive forensic inspection was conducted on `tradesignal.db` (132 MB SQLite database), SQLite pragmas, table schemas, unique constraints, and transaction durability.

---

## 2. Database Schema & Storage Statistics

- **Database Engine:** SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`).
- **Synchronous Pragma:** `PRAGMA synchronous=NORMAL`.
- **Database File Size:**
  - `tradesignal.db`: 132,399,104 bytes (~132.4 MB)
  - `tradesignal.db-wal`: ~4.1 MB
  - `tradesignal.db-shm`: 32 KB
  - `trading_fallback.db`: 98,844,672 bytes (~98.8 MB)
- **Total Tables:** 53 tables.

### Key Table Record Counts
| Table Name | Row Count | Primary Purpose |
|:---|:---:|:---|
| `historical_candles` | **251,309** | Authoritative 1m, 1h, 4h, 1d OHLCV candle storage |
| `canonical_signal_ledger` | **42,273** | Signal records across multiple timeframes |
| `prospective_outcomes` | **8,608** | Resolved trade simulation outcomes |
| `forecast_results` | **7,602** | Individual model predictions |
| `data_sync_jobs` | **3,548** | Data synchronization job execution logs |
| `forecast_requests` | **1,096** | Forecast requests |
| `forecast_consensus` | **1,087** | Aggregated consensus predictions |
| `decision_history` | **939** | Historical execution decisions |
| `research_validations` | **1,167** | Out-of-sample research validation logs |
| `campaign_events` | **193** | Prospective campaign event tracking |
| `signal_lifecycle` | **68** | Signal state transition records |
| `symbols` | **21** | Supported asset definitions |
| `daily_evidence_seals` | **11** | SHA-256 daily cryptographic integrity seals |
| `shadow_predictions` | **1** | Immutable shadow predictions |
| `paper_orders` | **1** | Simulated paper orders |
| `users` | **1** | Admin user record |

---

## 3. Data Integrity & Constraint Analysis

### 3.1 Uniqueness Constraints
1. **`canonical_signal_ledger.signal_id`:** `UNIQUE`, indexed. Prevents duplicate signal IDs from being inserted into the canonical ledger.
2. **`signal_lifecycle.signal_id`:** `UNIQUE`, indexed. Ensures single lifecycle record per signal.
3. **`historical_candles`:** Unique index on `(symbol, timeframe, timestamp)` prevents duplicate candles.
4. **`users.username` & `users.email`:** `UNIQUE`, indexed.

### 3.2 Immutability Guarantees
- In `canonical_signal_ledger`, records are append-only. No `UPDATE` or `DELETE` cascades are defined on historical signals.
- In `daily_evidence_seals`, each seal contains a SHA-256 hash linking the previous day's hash, forming an append-only audit trail.

---

## 4. Concurrency & WAL Performance

- SQLite WAL mode allows concurrent readers while a single writer commits.
- Python database connections in `app/database/manager.py` use `check_same_thread=False` and a connection timeout of 30.0 seconds to prevent "database is locked" errors under moderate concurrency.
- Tests in `tests/test_chaos_idempotency_restart.py` and `tests/test_phase44_database_integrity.py` pass.

---

## 5. Storage Observations & Recommendations
1. `tradesignal.db` (132 MB) and `trading_fallback.db` (98 MB) are currently local untracked SQLite files.
2. They are correctly excluded from git by `.gitignore` (`*.db`, `*.sqlite`).
3. In a production cloud deployment, migrate state from SQLite to PostgreSQL (e.g. Supabase or RDS) with connection pooling (`asyncpg`).
