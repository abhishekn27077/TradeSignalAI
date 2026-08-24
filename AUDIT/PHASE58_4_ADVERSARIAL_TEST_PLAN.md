# PHASE 58.4 — ADVERSARIAL, CHAOS & REPRODUCIBILITY TEST PLAN

**Project:** TradeSignalAI-v3  
**Frozen Configuration Hash:** `79a4f8e12b79310d`  
**Test Suite Target:** `tests/test_phase58_4_adversarial_audit.py`  
**Baseline Checkpoint:** `phase-58.3-runtime-verified` (`3be52ba`)  
**Execution Policy:** Zero-Trust, Fail-Closed, Causal Point-in-Time Enforcement  

---

## 1. Adversarial Test Categories Overview

| Category ID | Category Name | Core Invariant Under Attack |
| :--- | :--- | :--- |
| **A. Persistence** | SQLite & Durable Ledgers | Transaction atomicity, zero partial/orphan records on crash. |
| **B. Concurrency** | Parallel Bootstraps & Evals | Race conditions, double reconciliation, multiple instances. |
| **C. Crash Recovery** | Interrupted Replay / Writes | Mid-stream termination, restart recovery, dirty state resilience. |
| **D. Market Sessions** | Boundary & Transition Testing | 21:59 vs 22:00 UTC, Friday close, session switches, gating. |
| **E. Candle Integrity** | Sequence & Data Gaps | Duplicate candles, out-of-order candles, missing intervals, lookahead. |
| **F. Signal Idempotency**| Deduplication & Gating | 1x, 10x, 100x evaluations on identical candle produce exactly 1 signal. |
| **G. Trade Lifecycle** | SL / TP / Expiry Edge Math | Equality conditions (`HIGH == TP`), intra-candle dual breach handling. |
| **H. Statistics** | Metric Aggregations | Recomputation from persisted records, zero double-counting. |
| **I. API Consistency** | Endpoint Fault Injection | Malformed inputs, missing fields, negative limits, type safety. |
| **J. Frontend Consistency**| Zero-Fallback Integrity | Empty state rendering, absence of synthetic client mappings. |
| **K. Config Integrity** | Hash Verification | `79a4f8e12b79310d` immutability and drift detection. |
| **L. Replay Determinism**| Exact Bitwise Replay | Run A vs Run B produce identical outputs. |
| **M. Data-Provider Failure**| Network / Source Failures | Timeouts, 500 errors, fail-closed without synthetic filler. |
| **N. Security / Safety** | Real-Money Execution Locks | 7/7 broker execution vectors hard-disabled. |
| **O. Ledger Integrity** | Immutable Hash Chain | Tamper detection, deletion rejection, point-in-time causality. |

---

## 2. Detailed Test Specifications

### Category A: Persistence & Atomicity
- **Test A1: Transaction Atomicity During Trade Settlement**
  - **Input:** Trade settles; database write simulates interruption between `signal_lifecycle` update and `paper_orders` update.
  - **Expected State:** SQLite transaction rollback ensures no partial state exists.
  - **Pass Condition:** Either both tables reflect settlement or neither does (clean rollback).
  - **Fail Condition:** Trade marked closed in one table while remaining open in another.

### Category B: Concurrency & Race Conditions
- **Test B1: Simultaneous Parallel Bootstrap Calls**
  - **Input:** 5 concurrent threads invoke `execute_bootstrap_sequence()` simultaneously.
  - **Expected State:** Thread lock / transaction isolation serializes execution; exactly 0 duplicate trade outcomes.
  - **Pass Condition:** `trades_closed_during_recovery` and `open_trades_recovered` match single-threaded run.
  - **Fail Condition:** Same open trade reconciled multiple times or duplicate outcome records inserted.

- **Test B2: Concurrent Signal Evaluation on Same Closed Candle**
  - **Input:** 10 simultaneous evaluation requests for EURUSD M5 candle at timestamp $T$.
  - **Expected State:** Deduplication engine emits maximum 1 signal lifecycle record.
  - **Pass Condition:** `COUNT(signal_id) == 1` for candle timestamp $T$.
  - **Fail Condition:** Multiple signal records created for identical candle and config hash.

### Category C: Crash Recovery & Restart Storm
- **Test C1: Repeated Rapid Start/Stop Cycles**
  - **Input:** 10 consecutive restart cycles with an active open paper trade.
  - **Expected State:** Trade recovered cleanly on each startup; state remains deterministic.
  - **Pass Condition:** Open trade remains `PAPER_OPEN` until exit candle is encountered; exactly 1 resolution upon exit.
  - **Fail Condition:** Trade lost from memory or duplicate closed records generated.

### Category D: Market Session Boundaries & Transitions
- **Test D1: Forex Asian Session / Weekend Transition Boundary**
  - **Input:** Evaluate EURUSD at Sunday 21:59:59 UTC (`CLOSED`) vs Sunday 22:00:00 UTC (`OPEN`).
  - **Expected State:** 21:59 UTC rejected with `MARKET_CLOSED`; 22:00 UTC accepted for evaluation.
  - **Pass Condition:** Exact 1-second precision at market open boundary.
  - **Fail Condition:** 21:59 UTC accepted or 22:00 UTC blocked.

- **Test D2: Friday Weekend Close Boundary**
  - **Input:** Evaluate GBPUSD at Friday 20:59:59 UTC (`OPEN`) vs Friday 21:00:00 UTC (`CLOSED`).
  - **Expected State:** 20:59 UTC evaluated; 21:00 UTC rejected with `WEEKEND_FRIDAY_CLOSE`.
  - **Pass Condition:** Exact boundary transition without one-minute slippage.
  - **Fail Condition:** Signals generated past Friday 21:00 UTC.

### Category E: Candle Integrity & Sequence Attacks
- **Test E1: Duplicate Candle Ingestion**
  - **Input:** Candle stream `[T1, T2, T2, T3]` injected into reconciliation engine.
  - **Expected State:** Duplicate candle $T_2$ is detected and ignored.
  - **Pass Condition:** Replay processes 3 unique candles; holding bars increments by 3, not 4.
  - **Fail Condition:** Duplicate candle alters holding duration or triggers double evaluation.

- **Test E2: Out-of-Order Candle Stream**
  - **Input:** Candle stream `[T1, T3, T2, T4]` injected into reconciliation engine.
  - **Expected State:** Engine sorts sequence chronologically before evaluating price trajectory.
  - **Pass Condition:** Replayed strictly as `T1 -> T2 -> T3 -> T4`.
  - **Fail Condition:** $T_3$ evaluated before $T_2$, resulting in false premature exit.

- **Test E3: Missing Candle Gap**
  - **Input:** Candle stream `[T1, T2, T5]` (missing $T_3, T_4$).
  - **Expected State:** Engine detects timestamp delta $> 1$ bar interval, flags data gap, and pauses or evaluates known points without fabricating missing bars.
  - **Pass Condition:** Zero synthetic/interpolated candles generated.
  - **Fail Condition:** System fabricates fake OHLC prices for $T_3$ and $T_4$.

- **Test E4: Future Candle / Lookahead Injection**
  - **Input:** Candle timestamp $T_{\text{future}} > T_{\text{eval}}$ injected into feature generator.
  - **Expected State:** Feature extraction strictly filters `timestamp <= evaluation_time`.
  - **Pass Condition:** Future bar has zero impact on indicators, SMC, or consensus.
  - **Fail Condition:** Lookahead bias detected in any indicator or vote.

### Category F: Signal & Paper Trade Idempotency
- **Test F1: 100x Repeated Candle Evaluation Stress**
  - **Input:** Loop 100 evaluations on the same asset, timeframe, and closed candle.
  - **Expected State:** Exactly 1 signal lifecycle record in SQLite.
  - **Pass Condition:** Database row count increments by at most 1 on first iteration, 0 on remaining 99.
  - **Fail Condition:** Duplicate signal records generated.

### Category G: Trade Lifecycle & SL/TP Edge Conditions
- **Test G1: Exact High Equality to Take Profit (`HIGH == TP`)**
  - **Input:** BUY order TP = 1.0900. Candle High = 1.0900 (exact touch).
  - **Expected State:** Marked `TP_HIT` at exit price 1.0900.
  - **Pass Condition:** `status == "TP_HIT"`, `gross_r == +2.00R`.
  - **Fail Condition:** Touch missed or treated as ongoing open trade.

- **Test G2: Exact Low Equality to Stop Loss (`LOW == SL`)**
  - **Input:** BUY order SL = 1.0750. Candle Low = 1.0750 (exact touch).
  - **Expected State:** Marked `SL_HIT` at exit price 1.0750.
  - **Pass Condition:** `status == "SL_HIT"`, `gross_r == -1.00R`.
  - **Fail Condition:** Touch missed or treated as ongoing open trade.

- **Test G3: Intra-Candle Dual Breach (`AMBIGUOUS_CANDLE_PATH`)**
  - **Input:** Candle with High $\ge$ TP (1.0950) AND Low $\le$ SL (1.0700) in the same bar.
  - **Expected State:** Documented deterministic resolution: `AMBIGUOUS_CANDLE_PATH`, Gross R: `0.00R`, Net R: $-Friction$.
  - **Pass Condition:** Deterministic non-random classification.
  - **Fail Condition:** Random coin-flip or optimistic assumption of TP first.

### Category H: Statistics Recomputation & Double-Count Prevention
- **Test H1: Repeated Bootstrap Statistics Stability**
  - **Input:** 10 consecutive bootstrap executions over historical trades.
  - **Expected State:** Win count, loss count, Net PF, Expectancy remain mathematically identical.
  - **Pass Condition:** Recomputed values match initial baseline to 6 decimal places.
  - **Fail Condition:** Statistics drift or double-count closed trades.

### Category I: API Fault Injection & Malformed Payloads
- **Test I1: Invalid Symbols, Negative Limits, and Future Timestamps**
  - **Input:** Requests to `/api/v1/market/status/INVALID_SYM`, `/api/v1/signals/history?limit=-50`, `/api/v1/forecasts/tomorrow?date=2099-01-01`.
  - **Expected State:** Clean HTTP 400/422/404 with structured error JSON; zero unhandled 500 exceptions.
  - **Pass Condition:** System responds gracefully and server remains healthy.
  - **Fail Condition:** Server crash or database corruption.

### Category J: Frontend Zero-Fallback Integrity
- **Test J1: Code-Level Scan for Forbidden Fallbacks**
  - **Input:** AST/Regex scan across `frontend/src/` for `signals.length === 0 ? forecasts : ...` or `Math.random`.
  - **Expected State:** Zero synthetic fallbacks found.
  - **Pass Condition:** Pure backend-driven rendering on all pages.
  - **Fail Condition:** Any client-side data substitution detected.

### Category K: Governance & Immutability Integrity
- **Test K1: Configuration Hash Propagation & Tamper Gate**
  - **Input:** Verify `CONFIG_HASH == "79a4f8e12b79310d"` across `canonical_decision_engine`, `signal_truth_ledger`, and `market_session_service`.
  - **Expected State:** All engines share identical frozen fingerprint.
  - **Pass Condition:** 100% match.
  - **Fail Condition:** Any parameter drift or hash mismatch.

### Category L: Deterministic Replay Verification
- **Test L1: Run A vs Run B Bitwise Replay**
  - **Input:** Feed identical 100-candle dataset to 2 separate isolated engine instances.
  - **Expected State:** Identical forecasts, model vote distributions, and signal decisions.
  - **Pass Condition:** 0 bit difference in output JSON.
  - **Fail Condition:** Nondeterministic variation between runs.

### Category M: Data Provider Failure & Fail-Closed Behavior
- **Test M1: Data Provider 500 / Network Timeout**
  - **Input:** Mock market data provider throwing `ConnectionError` or `TimeoutError`.
  - **Expected State:** Engine sets `status = DATA_UNAVAILABLE`, halts signal generation.
  - **Pass Condition:** Zero synthetic/random candles or fallback trades generated.
  - **Fail Condition:** System fabricates prices or continues trading on missing data.

### Category N: Real-Money Safety Audit
- **Test N1: Verification of 7 Broker Execution Attack Vectors**
  - **Input:** Audit broker execution dispatchers (`settings.ENABLE_REAL_MONEY_TRADING`, `EXECUTION_MODE`).
  - **Expected State:** All live broker order dispatch functions raise `RuntimeError("REAL_MONEY_STRICTLY_DISABLED")`.
  - **Pass Condition:** Real money execution is impossible.
  - **Fail Condition:** Any pathway allows live order transmission.

### Category O: Immutable Ledger Tamper Protection
- **Test O1: Ledger Row Modification Attack**
  - **Input:** Attempt direct SQL update to an existing `signal_lifecycle` record's `gross_r`.
  - **Expected State:** Truth ledger SHA256 cryptographic chain fails verification (`LEDGER_TAMPER_DETECTED`).
  - **Pass Condition:** Tamper detected immediately upon ledger integrity scan.
  - **Fail Condition:** Silent modification without detection.
