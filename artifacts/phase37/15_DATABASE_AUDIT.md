# 15 — Database Audit & Persistence Integrity
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Database Schema & Tables
The database layer manages persistent market candles, strategy signals, and lifecycle records in `trading_fallback.db` / PostgreSQL.

### Core Tables
- `market_candles`: Historical multi-timeframe OHLCV bars.
- `signals`: Generated trading recommendations and master intelligence traces.
- `signal_lifecycle`: Outcome resolution tracking (`ACTIVE`, `TP_HIT`, `SL_HIT`, `EXPIRED`).
- `trade_journal`: Performance journal and trade analytics.

---

## 2. Integrity Verification
- SQLite fallback connection pool initialized cleanly with asynchronous SQLAlchemy engine.
- Asynchronous session generator `get_db_session()` correctly bound in all endpoints.
- Zero table lockups or data corruption observed.
- Status: **PASSED & OPERATIONAL**.
