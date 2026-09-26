# Phase 73 — Signal Identity & Deduplication Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **CRITICAL DEFECT CONFIRMED (TS-008 STILL BROKEN & FAIL-OPEN)**

---

## 1. Executive Summary

Previous audit finding **TS-008** identified that while `SignalIdentityGuard` existed in the codebase, it was not enforced in the production execution hot path.

A zero-trust forensic audit of the current codebase confirms:
1. `SignalIdentityGuard` is **NOT CALLED** anywhere in the active execution path (`app/execution/coordinator.py`, `app/strategies/manager.py`, or `app/execution/router.py`).
2. The method `SignalIdentityGuard.is_duplicate()` is **fail-open on database errors**.
3. Duplicate consensus events and identical trade proposals can trigger multiple duplicate orders without restriction.

---

## 2. Forensic Code Evidence

### 2.1 Invocation Absence Across Production Code
A recursive grep for `SignalIdentityGuard` across the entire `app/` directory yielded only references inside `app/core/signal_identity.py` itself:
- `app/core/signal_identity.py:4`
- `app/core/signal_identity.py:24` (class definition)
- `app/core/signal_identity.py:91`
- `app/core/signal_identity.py:98`

`SignalIdentityGuard` is **never imported or invoked** in:
- `app/execution/coordinator.py`
- `app/strategies/manager.py`
- `app/agents/consensus/voting.py`
- `app/core/canonical_signal_service.py`

### 2.2 Database Column Usage
The column `SignalLifecycleModel.duplicate_protection_hash` exists in `app/database/models/signal.py:30`:
```python
duplicate_protection_hash = Column(String(64), unique=True, nullable=True, index=True)
```
However, `SignalLifecycleModel` is populated in `coordinator.py` without setting or checking `duplicate_protection_hash`.

### 2.3 Fail-Open on Database Errors
In `app/core/signal_identity.py:90-93`:
```python
except Exception as e:
    logger.error(f"SignalIdentityGuard.is_duplicate error: {e}")
    # Fail open — do not block the signal on DB error
    return False
```
If the database connection fails, times out, or is locked, `is_duplicate()` returns `False`, allowing duplicate signals to pass.

---

## 3. Adversarial Duplication Scenarios

| Test Scenario | Expected Production Behavior | Actual Code Behavior | Verdict |
|:---|:---|:---|:---:|
| **1 Identical Signal** | Approved | Approved | PASS |
| **10 Duplicate Signals** | 1 Approved, 9 Rejected | **All 10 Approved & Dispatched** | **FAIL** |
| **Concurrent Duplicate API Requests** | Only 1 executes | **Both execute simultaneously** | **FAIL** |
| **Database Failure during Dedup Check** | Block / Fail Closed | **Returns False (Approved)** | **FAIL (Fail-Open)** |

---

## 4. Remediation Required
1. In `app/execution/coordinator.py:_execute_order()`, before creating an entry or running risk checks, calculate the SHA-256 identity hash:
   ```python
   identity_hash = SignalIdentityGuard.compute_hash(
       asset=trade_proposal["symbol"],
       timeframe=trade_proposal.get("timeframe", "H4"),
       candle_timestamp=trade_proposal.get("candle_timestamp", ""),
       direction=trade_proposal["direction"]
   )
   if await SignalIdentityGuard.is_duplicate(session, identity_hash):
       logger.warning(f"DUPLICATE SIGNAL REJECTED: {identity_hash}")
       return {"status": "REJECTED", "reason": "DUPLICATE_SIGNAL"}
   ```
2. In `app/core/signal_identity.py:90-93`, change the exception handler to **fail-closed**:
   ```python
   except Exception as e:
       logger.error(f"SignalIdentityGuard.is_duplicate error: {e}")
       return True  # Fail closed: suppress signal when database state is uncertain
   ```
