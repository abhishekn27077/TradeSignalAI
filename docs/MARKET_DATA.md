# Market Data Architecture & Provider Specification

## 1. Overview

Market data is the foundational truth of TradeSignalAI-v3. In accordance with the platform's core axioms:
- **Never fabricate market data.**
- **Never synthesize Bid/Ask via `bid = close, ask = close`.**
- **Never treat generic symbols (e.g. `BTCUSD`) as globally fungible across distinct venues.**
- **Never use SQLite or cached candles as live market quotes.**

---

## 2. Primary Forex Provider: MetaTrader 5 (MT5)

- **Module**: `app/market_data/providers/mt5_provider.py`
- **Class**: `MT5MarketDataProvider`
- **Interface**: Implements `BaseMarketDataProvider`

### Capabilities
1. **Symbol Resolution**: Queries `mt5.symbol_info(symbol)` for broker-specific naming (e.g. `USDJPY`, `USDJPY.m`, `USDJPY.pro`).
2. **Current Tick Retrieval**: Queries `mt5.symbol_info_tick(symbol)` extracting:
   - `bid`: Real broker bid price
   - `ask`: Real broker ask price
   - `spread`: Real spread in price units (`ask - bid`)
   - `source_timestamp`: Timestamp reported directly by the MT5 broker terminal
   - `broker`: Broker company name
   - `server`: Connected server cluster
3. **OHLC Bars**: Queries `mt5.copy_rates_from_pos` for native timeframes: `M5`, `M15`, `M30`, `H1`, `H4`, `D1`.
4. **Provenance**: Every returned bar or tick embeds:
   - `provider`: `"MT5"`
   - `venue`: Broker/Server name
   - `source_timestamp`: Broker terminal tick time
   - `received_timestamp`: Local ingestion timestamp
   - `data_age_ms`: Computed ingestion latency

### Fail-Closed Behavior
- If `mt5.initialize()` fails or the broker terminal is disconnected:
  - Provider sets `is_connected = False`.
  - Live tick requests raise `ProviderUnavailableError` or return `freshness_status = UNAVAILABLE`.
  - **No fallback to SQLite or synthetic ticks.**

---

## 3. Primary Crypto Provider: Binance

- **Module**: `app/market_data/providers/binance_provider.py`
- **Class**: `BinanceMarketDataProvider`
- **Interface**: Implements `BaseMarketDataProvider`

### Capabilities
1. **Explicit Venue / Symbol**: Instruments are strictly addressed as `BINANCE:BTCUSDT`, `BINANCE:ETHUSDT`. Generic `BTCUSD` is explicitly mapped to `BTCUSDT` via `CanonicalAssetRegistry`.
2. **Book Ticker**: Queries `https://api.binance.com/api/v3/ticker/bookTicker` yielding exact `bidPrice`, `bidQty`, `askPrice`, `askQty`, and genuine book spread.
3. **OHLC Klines**: Queries `https://api.binance.com/api/v3/klines` for standard timeframes (`5m`, `15m`, `30m`, `1h`, `4h`, `1d`).
4. **Provenance**:
   - `provider`: `"BINANCE"`
   - `venue`: `"BINANCE"`
   - `source_timestamp`: Binance exchange millisecond timestamp

---

## 4. Secondary Reference Provider: TradingView

- **Module**: `app/market_data/providers/tradingview.py`
- **Class**: `TradingViewDataProvider`
- **Role**: `SECONDARY_VALIDATION`

### Capabilities & Limits
- **Validation Only**: TradingView data is used exclusively to verify parity, compare indicator outputs, or detect anomalies against the primary MT5/Binance feed.
- **Strict Prohibition**: TradingView never overwrites or supersedes primary live feeds.
- **Parity Engine**: `validate_secondary_parity(primary_data, secondary_data)` logs basis point discrepancies. If difference exceeds configured threshold, an audit warning is generated.

---

## 5. Historical & Backfill Provider: Yahoo Finance

- **Module**: `app/market_data/providers/yfinance_provider.py`
- **Class**: `YFinanceDataProvider`
- **Role**: `HISTORICAL_SECONDARY`

### Capabilities & Limits
- **Research & Deep Backtesting**: Used to pull long-horizon multi-year daily bars for baseline statistical calibration.
- **Strict Prohibition**: Yahoo Finance data is never tagged as `LIVE` and cannot trigger real-time prospective signals.

---

## 6. SQLite: Inverted Storage & Evidence Cache

- **Role**: `CACHE / HISTORICAL / FORENSIC EVIDENCE`
- **Isolation Keys**:
  - `(symbol, venue, timeframe, timestamp)`
  - Schema index: `idx_candles_sym_venue_tf_ts`
- **Query Guarantees**:
  - All candle queries require explicit `timeframe` and `venue`.
  - Zero cross-timeframe or cross-venue data leakage.
  - Written only *after* live market data is verified by `DataFreshnessService`.
