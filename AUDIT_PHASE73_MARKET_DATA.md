# Phase 73 — Real Market Data Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **CRITICAL DEFECT IDENTIFIED (DATA FABRICATION FALLBACKS & FAKE SIGNAL FACTORY)**

---

## 1. Executive Summary

A zero-trust forensic audit of market data sources, candle persistence, and real price feeds reveals that while the database contains genuine historical market data (251,309 candles), the production codebase contains **active fallback paths that fabricate synthetic market data and signals** rather than failing closed.

---

## 2. Market Data Inventory in SQLite (`tradesignal.db`)

Direct inspection of `historical_candles` in `tradesignal.db` confirms:
- **Total Candles:** 251,309 rows.
- **Crypto (BTCUSD, ETHUSD):** 1H candles present up to `2026-09-26T10:00:00+00:00` (live today).
- **Forex & Indices (AUDUSD, EURUSD, GBPUSD, NAS100, SPX500, USDJPY, XAUUSD):** 1H candles present up to `2026-09-25T22:00:00` (yesterday's market close prior to weekend).
- **Timeframes in DB:** 1H, 4h, 1d, 1wk, D1, M15.

The data in SQLite is authentic historical market data obtained from TradingView / Yahoo feeds.

---

## 3. Data Fabrication Defects Found in Code

### Defect 1: Synthetic Candle Generation in `canonical_signal_service.py`
- **Location:** `app/core/canonical_signal_service.py:149-160`
- **Code:**
  ```python
  if not rows or len(rows) < 10:
      base_p = ASSET_BASE_PRICES.get(asset, 100.0)
      now = datetime.now(timezone.utc)
      times = [now - timedelta(hours=i) for i in range(limit, 0, -1)]
      df = pd.DataFrame({
          'open': [base_p] * limit,
          'high': [base_p * 1.002] * limit,
          'low': [base_p * 0.998] * limit,
          'close': [base_p * 1.0005] * limit,
          'volume': [1000.0] * limit
      }, index=times)
      return df
  ```
- **Forensic Finding:** If fewer than 10 rows are returned from the database, the system constructs a fake DataFrame with constant prices derived from `ASSET_BASE_PRICES` (e.g. BTC=67450.0) and synthetic high/low/close multipliers. This DataFrame is passed to indicator calculation engines.
- **Expected Zero-Trust Behavior:** Fail closed immediately with `INSUFFICIENT_MARKET_DATA` error.

### Defect 2: Fallback Price in Single Asset Evaluation
- **Location:** `app/core/canonical_signal_service.py:450-455`
- **Code:**
  ```python
  if ref_price is None:
      ref_price = ASSET_BASE_PRICES.get(asset, 100.0)
  if age_seconds is None:
      age_seconds = 9999999.0
  ```
- **Forensic Finding:** If no candle exists, `ref_price` falls back to the static `ASSET_BASE_PRICES` dictionary.

### Defect 3: Synthetic Fallback in TradingView Paper Broker
- **Location:** `app/brokers/tradingview_broker.py:61-62`
- **Code:**
  ```python
  # Global fallback if no price ever fetched
  return 64000.0 if "BTC" in symbol else 1.0
  ```
- **Forensic Finding:** If TradingView market data is disconnected or rate-limited, the paper broker executes simulated orders at a hardcoded price of $64,000 for BTC or $1.00 for other assets!

### Defect 4: Signal Generation Without Market Data in `signal_factory.py`
- **Location:** `app/core/signal_factory.py:321-339`
- **Forensic Finding:**
  `signal_factory.generate_signal()` calls `tradingview_adapter.extract_indicator_observations()`, which returns hardcoded indicator values (`rsi_14 = 58.2`, `atr_normalized = 0.0045`), and then determines trade direction via:
  ```python
  seed_str = f"{asset}_{timeframe}_{now.strftime('%Y%m%d%H')}"
  seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16) % 1000000
  direction = "BUY" if (seed % 3 == 0) else ("SELL" if (seed % 3 == 1) else "WAIT")
  ```
  This path generates signals purely from timestamp strings without querying market prices or technical indicators.

---

## 4. Freshness and Stale Data Handling

In `canonical_signal_service.py:467-474`, the system defines:
```python
_TF_FRESHNESS_SECONDS = {
    "1m": 120, "5m": 600, "15m": 1800, "30m": 3600,
    "1h": 7200, "4h": 28800, "1d": 172800,
}
```
If `age_seconds > threshold`:
- Signals are correctly rejected with `qualification_reason = "STALE_MARKET_DATA"`.
- This was confirmed during our pytest run: `test_phase48_honest_no_trade_consensus` and `test_granular_no_trade_reasons` failed because the engine properly rejected candles as `STALE_MARKET_DATA`.

---

## 5. Remediation Required
1. Remove `ASSET_BASE_PRICES` completely from `app/core/canonical_signal_service.py`.
2. In `_load_recent_candles()`, if `len(rows) < 10`, return empty DataFrame and raise `InsufficientMarketDataError`.
3. In `tradingview_broker.py`, if price cannot be fetched, reject the order with `OrderStatus.FAILED` instead of returning 64000.0 or 1.0.
4. Refactor `signal_factory.py` to route through genuine canonical evaluation or eliminate `SignalFactory` in favor of `canonical_signal_service`.
