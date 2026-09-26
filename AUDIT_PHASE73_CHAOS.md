# Phase 73/74 Audit: Chaos, Idempotency & Fault Tolerance (Phase 22)

**Audit Date**: 2026-09-26  
**Auditor**: Independent Zero-Trust Forensic Auditor  
**Status**: **PARTIAL PASS (LEDGER ROBUST, BUT MULTIPLE FAIL-OPEN BYPASSES IN HOT PATH)**

---

## 1. Executive Summary

This forensic section audits system stability under process restarts, crash recovery, deduplication idempotency, concurrent multithreading, and examines whether critical subsystems fail-closed (secure/safe) or fail-open (unsafe/leaky).

### Key Findings:
1. **Ledger Idempotency & WAL Concurrency (PASS)**:
   - `CanonicalProspectiveLedger` safely handles process crashes and restarts without data loss.
   - Multi-threaded concurrent settlement of orders across 5 worker threads succeeded without SQLite lock errors or deadlocks (`test_chaos_idempotency_restart.py` PASSED 3/3 in 13.3s).
2. **Signal Deduplication Guard Fail-Open (FAIL — TS-008)**:
   - `SignalIdentityGuard.is_duplicate()` catches all database exceptions and returns `False` (allowing signals to proceed), and is decoupled from the hot execution path.
3. **Market Data Fail-Open to Synthetic Feed (FAIL)**:
   - When live price feeds are unreachable or stale, `market_data_service.py` falls back to `SyntheticFeed` (`ASSET_BASE_PRICES`) rather than halting signal dispatch.
4. **Risk Engine Missing SL/TP Fail-Open (FAIL — TS-005)**:
   - If an order proposal arrives without explicit SL/TP levels, `RiskEngine.evaluate()` approves the order unconditionally.
5. **In-Flight Queue Volatility (PARTIAL)**:
   - `EventBus` and `AgentLifecycleManager` rely on in-memory `asyncio.Queue` objects. Any ungraceful process crash terminates pending in-flight signals permanently.

---

## 2. Test Verification

Executing `tests/test_chaos_idempotency_restart.py`:
- `test_process_restart_recovery_and_persistence`: **PASSED**
- `test_deduplication_idempotency_under_duplicate_submissions`: **PASSED**
- `test_concurrent_multi_threaded_resolution`: **PASSED**
- Total: 3/3 passed in 13.32s.

---

## 3. Forensic Matrix: Fail-Closed vs Fail-Open

| Subsystem | Failure Scenario | Expected Behavior (Safe) | Actual Behavior (Codebase) | Verdict |
|---|---|---|---|---|
| **Rule Zero (Real Money)** | Config missing or corrupted | Disallow execution | `REAL_MONEY_ENABLED = False` throws `PermissionError` | **FAIL-CLOSED (PASS)** |
| **API Authentication** | Missing or malformed token | Reject request (401) | Anonymous fallback in 98.9% of endpoints | **FAIL-OPEN (FAIL)** |
| **Order Reconciliation** | Broker order status unreachable | Halt and mark `UNKNOWN` | Mark status `UNKNOWN`, freeze reconciliation | **FAIL-CLOSED (PASS)** |
| **Signal Identity Guard** | DB lock or write error | Reject signal | Catches exception, returns `False` (allows signal) | **FAIL-OPEN (FAIL)** |
| **Risk Validation** | Order lacks SL/TP | Reject proposal | Bypasses RR check, returns `APPROVED` | **FAIL-OPEN (FAIL)** |
| **Market Data Ingestion** | Live websocket disconnect | Halt strategy execution | Generates synthetic random prices | **FAIL-OPEN (FAIL)** |
| **Ledger Persistence** | Duplicate signal submission | Idempotent `INSERT OR IGNORE` | Primary key conflict handled cleanly | **PASS** |

---

## 4. Recommendations

1. **Fix SignalIdentityGuard Fail-Closed**: In `app/core/signal_identity.py`, re-raise database errors or return `True` (quarantine duplicate) upon storage exceptions.
2. **Block Synthetic Fallback in Production**: In `market_data_service.py`, enforce strict error emission if real prices are missing. Trading strategies must never fire on synthetic prices outside explicit sandbox unit tests.
3. **Reject Missing SL/TP in Risk Engine**: Update `app/risk/engine.py` to reject any order proposal lacking explicit stop loss and take profit thresholds.
