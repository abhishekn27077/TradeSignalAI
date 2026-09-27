# Architecture & Market Data Hierarchy — TradeSignalAI-v3

## 1. High-Level System Architecture

TradeSignalAI-v3 is designed as a **DATA-TRUTH-FIRST, SESSION-AWARE, PAPER-ONLY** quantitative trading research and prospective signal engine. The platform strictly enforces fail-closed execution semantics: missing, stale, ambiguous, or out-of-session data immediately blocks signal creation.

```
+---------------------------------------------------------------------------------------------------+
|                                   PRIMARY LIVE DATA PROVIDERS                                     |
|                                                                                                   |
|   +------------------------------------+             +----------------------------------------+   |
|   |   MT5 Broker Feed (Forex / CFD)    |             |   Binance Exchange Feed (Crypto)       |   |
|   |   - Direct broker terminal/gateway |             |   - api.binance.com native ticks/klines|   |
|   |   - Real Bid, Ask, Spread, Server  |             |   - Explicit venue (BINANCE:BTCUSDT)   |   |
|   +-----------------+------------------+             +-------------------+--------------------+   |
+---------------------|----------------------------------------------------|------------------------+
                      |                                                    |
                      +--------------------------+-------------------------+
                                                 |
                                                 v
+---------------------------------------------------------------------------------------------------+
|                                       MARKET DATA GATEWAY                                         |
|                               (app/market_data/market_data_gateway.py)                            |
|                                                                                                   |
|   1. Canonical Symbol Resolution (CanonicalAssetRegistry)                                         |
|   2. Primary Provider Routing (MT5 for Forex, Binance for Crypto)                                 |
|   3. Freshness Policy Evaluation (DataFreshnessService)                                           |
|   4. Bid/Ask Truth Verification (Real spread, no synthetic bid=close)                             |
|   5. Secondary Parity & Reference Validation (TradingView / Yahoo)                                 |
+------------------------------------------------+--------------------------------------------------+
                                                 |
                                                 v
+---------------------------------------------------------------------------------------------------+
|                                      MARKET SESSION ENGINE                                        |
|                                   (app/core/market_session.py)                                    |
|                                                                                                   |
|   - Pre-flight Session Check (Evaluated immediately prior to signal generation)                   |
|   - Forex: Closed Friday 21:00 UTC through Sunday 21:00 UTC, broker maintenance windows           |
|   - Crypto: 24/7 continuous session                                                               |
|   - State: OPEN -> proceed | CLOSED -> FAIL-CLOSED (SIGNAL_BLOCKED / MARKET_CLOSED)               |
+------------------------------------------------+--------------------------------------------------+
                                                 |
                                                 v
+---------------------------------------------------------------------------------------------------+
|                                   CANONICAL SIGNAL VALIDATOR                                      |
|                                  (app/core/signal_validator.py)                                   |
|                                                                                                   |
|   11-Point Validation Contract:                                                                   |
|   1. Asset exists in CanonicalAssetRegistry                                                       |
|   2. Primary provider available & connected                                                       |
|   3. Primary data fresh (within configured max_age_seconds)                                       |
|   4. Timestamp valid (source_timestamp in acceptable bounds)                                      |
|   5. Timeframe correct & supported (M5, M15, M30, H1, H4, D1)                                     |
|   6. Venue explicitly specified (e.g., BINANCE, MT5-Broker)                                       |
|   7. Market session verified OPEN                                                                 |
|   8. Strategy entry & indicator conditions met                                                    |
|   9. Risk rules satisfied (valid entry, SL, TP, positive R:R)                                     |
|   10. Idempotent signal hash (no duplicate identity)                                              |
|   11. Hard execution lock: PAPER_ONLY                                                             |
+------------------------------------------------+--------------------------------------------------+
                                                 |
                                                 v
+---------------------------------------------------------------------------------------------------+
|                           CANONICAL PROSPECTIVE SIGNAL LEDGER & SQLITE                            |
|                                                                                                   |
|   - SQLite is strictly an INVERTED CACHE & FORENSIC EVIDENCE STORE.                               |
|   - SQLite is NEVER queried first to establish live market prices or signals.                      |
|   - Timeframe & Venue Isolation: queries require (symbol, venue, timeframe, timestamp)             |
|   - Deterministic forward walk-forward resolution against genuine future market bars              |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Inverted Data Flow Paradigm

### Legacy Anti-Pattern (Eliminated)
Previously, legacy routines checked SQLite first:
`SQLite Cache -> Return old candle -> Generate stale signal during closed market`.

### New Data-Truth-First Architecture
The revised pipeline enforces:
`Primary Live Provider -> Freshness Validation -> Market Session Gate -> Canonical Strategy Signal -> Forensic Persistence to SQLite`.

SQLite is exclusively:
1. Forensic audit trail of validated incoming bars.
2. Historical source for retrospective walk-forward backtesting.
3. Cold evidentiary store for terminal historical records.

---

## 3. Provider Roles & Hierarchy

| Role | Provider | Asset Class | Venue | Authority Level | Fail-Closed Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Live** | MT5 Python Client | Forex, CFDs | Broker Terminal | **Authoritative Live Feed** | If MT5 disconnected or symbol unmapped -> DATA_UNAVAILABLE |
| **Primary Live** | Binance REST/WS | Crypto | `BINANCE` | **Authoritative Live Feed** | If Binance API down -> DATA_UNAVAILABLE |
| **Secondary Validation** | TradingView | Forex, Crypto, Indices | TV Feeds | **Reference / Parity Only** | Discrepancy logged; never replaces primary feed |
| **Historical / Secondary** | Yahoo Finance | Forex, Equities | YF | **Backfill / Historical Only** | Labeled HISTORICAL_SECONDARY; never live broker feed |
| **Cache / Evidence** | SQLite DB | All | Local DB | **Forensic Evidence Store** | Never authoritative for live ticks or signals |

---

## 4. Execution Safety Lock

Real-money execution is permanently locked out:
- `REAL_MONEY_ENABLED = False` (hardcoded default in config and runtime).
- `ExecutionMode.PAPER_ONLY` enforced across all order routers.
- Terminal UI persistently displays **`PAPER ONLY`** badge.
