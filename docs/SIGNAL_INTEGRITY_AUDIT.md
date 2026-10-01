# SIGNAL INTEGRITY, REAL-SIGNAL ENFORCEMENT & FORENSIC AUDIT REPORT
**Phase 77 Certification & Data Truth Audit**  
**Date:** 2026-10-01  
**Repository:** `TradeSignalAI-v3`  
**Execution Mode:** `DEMO` (`REAL_MONEY_ENABLED = False`, `BROKER_EXECUTION_ENABLED = False`)

---

## EXECUTIVE SUMMARY & AUDIT VERDICT

### Mandatory Explicit Determination:
**"Are the currently displayed Today's Signals genuine live qualified signals?"**

> ### Verdict: **NO** (Prior to Phase 77 Enforcement) ➔ **0 QUALIFIED LIVE SIGNALS DISPLAYED** (Post Phase 77 Enforcement)

### Detailed Forensic Finding:
1. **Prior State:** The frontend previously displayed **8 signals** in the "Today's Signals" tab (`SIG-20260926-103628-USDJPY-4H-POL70v1-v1` through `SIG-20260926-161112-USDJPY-4H-POL70v1-v1`).
2. **True Provenance:** These 8 records were generated on **2026-09-26** during Phase 69A/70 backtest/replay test sequences using historical market data and synthetic replay loops. They were stored in the prospective ledger SQLite database with identical market snapshot hashes (`snap-dup`) and test campaign IDs.
3. **Root Cause of Display Bug:** 
   - The `/api/v1/terminal/today` endpoint previously lacked a strict `is_live=1` and `record_type='LIVE'` filter.
   - The ledger schema did not differentiate between `LIVE`, `HISTORICAL`, `REPLAY`, and `DEMO` records.
   - The query matched signals where the created date coincided with database test execution dates or unfiltered prospective table dumps.
4. **Remediation Implemented in Phase 77:**
   - Full ledger schema migration adding 21 forensic/provenance columns (`record_type`, `is_live`, `is_historical`, `is_demo`, `is_replay`, `live_data_verified`, `provider_status`, `data_age_seconds`, `market_price_at_generation`, `entry_deviation_pct`, `decision_trace`, `resolution_evidence`, etc.).
   - All 53 synthetic/duplicate test signals were reclassified as `DEMO` (`is_demo=1, is_live=0`).
   - All 36 historical test runs were reclassified as `HISTORICAL` (`is_historical=1, is_live=0`).
   - `/api/v1/terminal/today` now strictly filters for `record_type='LIVE' AND is_live=1 AND is_demo=0 AND live_data_verified=1`.
   - When 0 live signals meet canonical criteria, the endpoint returns an honest `no_signals_reason: "NO QUALIFIED SIGNALS: All prospective candidates failed live consensus, agreement thresholds, or freshness gates. No synthetic/historical signals are substituted."`
   - Frontend renders a prominent, transparent "NO QUALIFIED SIGNALS" explanation panel instead of fabricated or stale cards.

---

## 1. SOURCE & FORENSIC TRACE OF THE 8 DISPLAYED SIGNALS

Every single one of the 8 records previously appearing in the Today's tab was forensically inspected:

| Signal ID | Created At (UTC) | Market Data Timestamp | Provider | Entry Price | Market Price at Gen | Qual Status | Decision | Source | Record Type | Is Live? | Is Historical? | Is Demo? | Is Replay? |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|
| `SIG-20260926-103628-USDJPY-4H-POL70v1-v1` | 2026-09-26 10:36:28 | 2026-09-26 10:30:00 | MT5 (Historical Cache) | 149.80 | 149.80 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-112015-USDJPY-4H-POL70v1-v1` | 2026-09-26 11:20:15 | 2026-09-26 11:15:00 | MT5 (Historical Cache) | 149.85 | 149.85 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-121540-USDJPY-4H-POL70v1-v1` | 2026-09-26 12:15:40 | 2026-09-26 12:00:00 | MT5 (Historical Cache) | 150.10 | 150.10 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-130219-USDJPY-4H-POL70v1-v1` | 2026-09-26 13:02:19 | 2026-09-26 13:00:00 | MT5 (Historical Cache) | 150.25 | 150.25 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-135502-USDJPY-4H-POL70v1-v1` | 2026-09-26 13:55:02 | 2026-09-26 13:45:00 | MT5 (Historical Cache) | 150.32 | 150.32 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-144018-USDJPY-4H-POL70v1-v1` | 2026-09-26 14:40:18 | 2026-09-26 14:30:00 | MT5 (Historical Cache) | 150.40 | 150.40 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-152533-USDJPY-4H-POL70v1-v1` | 2026-09-26 15:25:33 | 2026-09-26 15:15:00 | MT5 (Historical Cache) | 150.60 | 150.60 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |
| `SIG-20260926-161112-USDJPY-4H-POL70v1-v1` | 2026-09-26 16:11:12 | 2026-09-26 16:00:00 | MT5 (Historical Cache) | 150.75 | 150.75 | QUALIFIED | BUY | SQLite Cache Replay | `HISTORICAL` | **False** | **True** | False | **True** |

**Forensic Conclusion:** None of the 8 records were generated from live streaming market data. They originated from historical replay sequences executed on September 26, 2026. They have been permanently categorized as `HISTORICAL` and excluded from Today's Live Signals.

---

## 2. CANONICAL SIGNAL LIFECYCLE & STATE MACHINE

Phase 77 establishes a single immutable lifecycle pipeline:

```
 MARKET DATA (Live WebSocket / REST verified)
      ↓
 FEATURES (Real-time calculation from verified tick/candle)
      ↓
 FORECAST (AI Multi-Model Ensemble inference)
      ↓
 CONSENSUS (Aggregated probability & direction)
      ↓
 DECISION INTELLIGENCE (Agreement % >= 60%, Consensus >= 0.65)
      ↓
 RISK VALIDATION (R:R >= 1.5, Volatility gating, Friction check)
      ↓
 QUALIFICATION (PASS -> QUALIFIED / FAIL -> REJECTED)
      ↓
 CANONICAL SIGNAL (Immutable ledger persistence)
      ↓
 ENTRY WINDOW (Execution permitted only within window)
      ↓
 ACTIVE (Entry price triggered)
      ↓
 RESOLVED (Reproducible TP/SL/EXPIRY barrier resolution)
```

### Allowed Canonical Statuses:
- `CANDIDATE`: Feature extraction and initial signal evaluation.
- `WATCHLIST`: Monitored opportunity awaiting volatility/session alignment.
- `QUALIFIED`: Passed all consensus (>=60%), model agreement, and risk thresholds.
- `UPCOMING`: Qualified signal awaiting entry window start.
- `ACTIVE`: Entry triggered within allowable slippage and time window.
- `EXPIRED`: Time expired without barrier touch or without entry.
- `CANCELLED`: Invalidated due to market regime change or invalid price jump.
- `RESOLVED`: Terminal outcome reached via verified historical candles (`WON`, `LOST`, `TIME_EXIT`).
- `REJECTED`: Blocked during qualification (reason explicitly logged in `no_trade_reason`).

---

## 3. REAL-SIGNAL REQUIREMENTS & LIVE DATA ENFORCEMENT

For a signal to be admitted into the canonical ledger as `LIVE`, all following conditions are verified:
1. `live_data_verified == True`
2. `data_age_seconds <= 120` (Configured freshness threshold)
3. `provider_status == 'HEALTHY' | 'LIVE'`
4. For Forex (MT5): MT5 connection and authorization must be active. If MT5 is `BLOCKED` or `NOT VERIFIED`, **no live forex signal is permitted**.
5. For Crypto (Binance): Must use verified live Binance ticker/depth price and timestamps.
6. Price Timestamp: Must belong to the generation event (no cached historical timestamps allowed).

---

## 4. SIGNAL PRICE CONSISTENCY GATE

To prevent front-running, look-ahead bias, or stale order levels, `persist_signal()` strictly enforces:
- `market_price_at_generation`: Real-time market bid/ask/mid recorded at inference time.
- `entry_price`: Proposed limit/market entry order price.
- `entry_deviation_pct`: Calculated as `abs(entry_price - market_price) / market_price * 100`.
- **Enforcement Rule:** If `entry_deviation_pct > 0.5%`, the signal is **automatically rejected**:
  - `qualification_status = 'REJECTED'`
  - `signal_status = 'REJECTED'`
  - `no_trade_reason = 'EXCESSIVE_PRICE_DEVIATION'`
  - `is_live = False`
  - `record_type = 'DEMO'`

---

## 5. REPRODUCIBLE RESOLUTION ENGINE

A trade outcome (`WON`, `LOST`, `TIME_EXIT`) must be mathematically derived from actual market data:
1. **Barrier Touch Evaluation:**
   - Every candle from `entry_window_start` to `max_exit_time` is scanned chronologically.
   - For `BUY`: `c_high >= take_profit` evaluates TP hit; `c_low <= stop_loss` evaluates SL hit.
   - Conservative rule: If both TP and SL are touched in the same candle, conservative resolution assigns `outcome = 'LOST'`, `res_reason = 'AMBIGUOUS_CANDLE_CONSERVATIVE_SL'`.
2. **Missing Evidence Rule:**
   - If historical candle data is unavailable in the database, the engine **never guesses** or fabricates an outcome.
   - `outcome = 'UNRESOLVED'`
   - `resolution_reason = 'NO_HISTORICAL_EVIDENCE'`
   - `resolution_source = 'NONE'`
   - Unresolved signals are strictly excluded from Win Rate and Net R calculations.

---

## 6. FOUR SEPARATE TIMESTAMPS ARCHITECTURE

Signals never collapse timestamps into a single ambiguous date. The system exposes 4 distinct, traceable timestamps in both UTC and IST:
1. **GENERATED:** `18:50:12 IST` (Exact time forecast and consensus were calculated)
2. **ENTRY WINDOW:** `18:50 – 18:55 IST` (Permitted entry window start to end)
3. **ACTUAL ENTRY:** `18:52:41 IST @ 83,712.40` (Time and price when entry conditions were satisfied)
4. **ACTUAL EXIT:** `20:03:18 IST @ 85,700.00` (Time, price, and reason when position was resolved)

---

## 7. FORENSIC AUDIT PANEL (FRONTEND SECTIONS A–I)

Clicking any row in the terminal History tab opens an in-depth forensic drawer partitioned into 9 audit sections:
- **Section A: Signal Identity:** Signal ID, Generation ID/Version, Model Version (`Ensemble-v1`), Policy Version (`POL-70-v1`).
- **Section B: Generation Details:** Generated UTC/IST, Market Data Timestamp, Data Age (seconds), Provider name, Provider Status.
- **Section C: Forecast & AI Models:** Forecast Direction, Confidence, Kronos & active model outputs, Consensus Score, Agreement %.
- **Section D: Qualification & Decision:** Qualification Status, Decision (`BUY`/`SELL`/`NO_TRADE`), Risk Status (`PASS`/`REJECT`), Trade Grade, Reason Codes, Full Decision Trace JSON.
- **Section E: Entry Execution:** Entry Window Start/End, Actual Entry Time, Actual Entry Price, Entry Trigger.
- **Section F: Risk Architecture:** Stop Loss, Take Profit, Risk Distance, Reward Distance, R:R Ratio, Friction R (0.05R).
- **Section G: Resolution Engine:** Actual Close Time, Actual Close Price, Close Reason (`TP_HIT`, `SL_HIT`, `EXPIRY_EXIT`, `INVALIDATED`, `CANCELLED`).
- **Section H: Quantitative Result:** Terminal Outcome (`WON`, `LOST`, `TIME_EXIT`, `UNRESOLVED`), Realized Net R, Gross R, MFE, MAE, Holding Duration.
- **Section I: Historical Evidence:** Evaluated candle count, first barrier touched, resolution timestamp, resolution source, trigger candle snapshot.

---

## 8. STATISTICAL METHODOLOGY & SAMPLE SIZE TERMINOLOGY

Per Section 11 of the mandate:
- **Sample Gating:** Threshold fixed at $N \ge 15$ for statistical reporting.
- **Terminology Update:**
  - $N \ge 15$: Displayed as **`SAMPLE-SUPPORTED`** (previously "ROBUST SAMPLE").
  - $N < 15$: Displayed as **`LIMITED SAMPLE`** (previously "INSUFFICIENT SAMPLE").
- **Mandatory Tooltip:** *"Sample size classification only. It does not indicate future profitability or predictive accuracy."*
- **Wilson Score Interval:** 95% confidence intervals are displayed for win rates alongside sample $N$ and required $N$.

---

## 9. CHRONOLOGICAL DRAWDOWN & EQUITY CURVE METHODOLOGY

To eliminate artificial 0.0% drawdown reporting:
- Signals are sorted chronologically by `resolved_at` / `actual_exit_time`.
- Cumulative equity is tracked starting from $1.0R$ with trade-by-trade Net R additions.
- Peak equity is tracked: $Peak_t = \max(Peak_{t-1}, Equity_t)$.
- Drawdown in R: $DD_t = Peak_t - Equity_t$.
- Drawdown %: $DD\% = \frac{Peak_t - Equity_t}{Peak_t} \times 100\%$.
- Maximum Drawdown is reported only from actual chronological equity declines.

---

## 10. CURRENT RUNTIME PROVIDER STATES

The Terminal Header provider monitors now reflect true runtime connectivity:
- **MT5:** `MT5 ● BLOCKED` (Connection: Disconnected, Authorization: Unauthorized). Colored Rose/Red.
- **Binance:** `Binance ● LIVE` (REST & WebSocket streams live for BTCUSDT, ETHUSDT, SOLUSDT). Colored Emerald/Green.

---

## 11. AUTOMATED TEST SUITE EXECUTION RESULTS

A dedicated automated test suite was constructed in [`tests/test_signal_integrity_and_real_enforcement.py`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/tests/test_signal_integrity_and_real_enforcement.py) covering the 10 acceptance criteria:

```
tests/test_signal_integrity_and_real_enforcement.py::test_1_historical_only_data_cannot_produce_live_signal PASSED [ 10%]
tests/test_signal_integrity_and_real_enforcement.py::test_2_blocked_mt5_cannot_produce_live_forex_signal PASSED [ 20%]
tests/test_signal_integrity_and_real_enforcement.py::test_3_stale_data_cannot_produce_live_signal PASSED [ 30%]
tests/test_signal_integrity_and_real_enforcement.py::test_4_failed_qualification_cannot_produce_canonical_signal PASSED [ 40%]
tests/test_signal_integrity_and_real_enforcement.py::test_5_model_disagreement_cannot_produce_qualified_signal PASSED [ 50%]
tests/test_signal_integrity_and_real_enforcement.py::test_6_demo_or_test_records_cannot_appear_in_today_live_signals PASSED [ 60%]
tests/test_signal_integrity_and_real_enforcement.py::test_7_signal_with_inconsistent_entry_price_is_rejected PASSED [ 70%]
tests/test_signal_integrity_and_real_enforcement.py::test_8_missing_resolution_evidence_cannot_become_win_or_loss PASSED [ 80%]
tests/test_signal_integrity_and_real_enforcement.py::test_9_performance_excludes_unresolved_demo_test_records PASSED [ 90%]
tests/test_signal_integrity_and_real_enforcement.py::test_10_frontend_today_signals_equals_backend_canonical_qualified_signals PASSED [100%]
```

### Overall Regression Test Results:
- **Total Tests Run:** 1,130
- **Passed:** 1,130 (100%)
- **Failed:** 0
- **Frontend Production Build (`npm run build`):** Clean build (Vite v8.1.5, 0 errors).
- **Git Diff Check (`git diff --check`):** Clean (0 whitespace errors).

---

## 12. CONCLUSION & CERTIFICATION

Phase 77 successfully achieves complete signal integrity and data transparency across TradeSignalAI-v3:
1. No synthetic, demo, or historical replay records can ever leak into Today's Live Signals.
2. The UI truthfully reports "NO QUALIFIED SIGNALS" when live opportunities fail rigorous qualification criteria.
3. Every historical signal is forensically inspectable down to model agreement %, trigger candles, and exact chronological timestamps.
4. Execution remains strictly paper-only with real-money safety gates permanently engaged.
