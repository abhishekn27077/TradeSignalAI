# Automated Test Suite & Regression Verification

## 1. Test Suite Overview

TradeSignalAI-v3 features a comprehensive automated test matrix verifying data truth, session gating, provider hierarchy, and regression behavior.

| Test File | Test Count | Scope |
| :--- | :--- | :--- |
| `tests/test_sunday_forex_regression.py` | 6 | Sunday evening regression, Forex closed, Crypto open, stale SQLite block |
| `tests/test_market_data_architecture.py` | 23 | Providers (MT5, Binance, TV, YF), Freshness, Timeframe/Venue Isolation, Bid/Ask truth |
| `tests/test_terminal_simplification_acceptance.py` | 6 | Terminal API `/today`, `/history`, `/timeframes`, `/performance`, Paper only |
| `tests/test_phase69a_terminal_canonical_ledger.py` | 20 | Canonical ledger invariants, forward outcome resolution, forensic durability |

**Total Core Architecture Tests: 55 Passing**

---

## 2. Key Verified Test Cases

### 1. Sunday Forex vs Crypto Session (`test_sunday_forex_regression.py`)
- **Date**: 2026-09-27 19:17:09 IST (Sunday evening).
- **USDJPY Result**: `is_market_open == False` -> `signal is None`, `SIGNAL_BLOCKED / MARKET_CLOSED`.
- **BTCUSDT Result**: `is_market_open == True` -> Evaluated against live feeds.
- **SQLite Fallback Check**: An old candle dated Friday in SQLite cannot trigger a Sunday signal.

### 2. Provider Hierarchy & Inversion (`test_market_data_architecture.py`)
- MT5 fails closed when terminal is disconnected (`DATA_UNAVAILABLE`).
- Binance retrieves real book tickers with genuine spread.
- TradingView provides secondary validation and calculates basis point divergence.
- Yahoo Finance is strictly tagged `HISTORICAL_SECONDARY`.
- SQLite is updated as a cache *only after* live provider validation.

### 3. Bid/Ask Truth
- Synthetic bid/ask (`bid = close, ask = close`) is blocked.
- If real bid/ask is unavailable, provider returns `None` and UI displays `BID/ASK UNAVAILABLE`.

### 4. Database Schema Timeframe & Venue Isolation
- Migrated schema with `venue` column and composite index `(symbol, venue, timeframe, timestamp)`.
- Prevents cross-timeframe or cross-venue candle leakage.

---

## 3. Running the Test Suites

```bash
# Run Sunday regression test
pytest tests/test_sunday_forex_regression.py -v

# Run market data architecture test
pytest tests/test_market_data_architecture.py -v

# Run combined core architecture & terminal tests
pytest tests/test_sunday_forex_regression.py tests/test_market_data_architecture.py tests/test_terminal_simplification_acceptance.py tests/test_phase69a_terminal_canonical_ledger.py -v
```
