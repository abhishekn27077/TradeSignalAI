# PHASE 60 — MARKET DATA LINEAGE & FRESHNESS AUDIT

**Project:** TradeSignalAI-v3  
**Audit Timestamp:** 2026-08-24T11:30:00+05:30  
**Configuration Hash:** `79a4f8e12b79310d`  
**Execution Mode:** `DEMO` (`REAL_MONEY == STRICTLY_DISABLED`)  

---

## 1. End-to-End Market Data Lineage Map

```
[Real Feed: Yahoo Finance / TradingView]
                  ↓
[MarketProviderManager / MarketDataService]
                  ↓
[SQLite Database (tradesignal.db: historical_candles)]
                  ↓
[CanonicalMarketDataService / FeatureEngine]
                  ↓
[Point-In-Time Feature Snapshot (N=1450)]
                  ↓
[CanonicalMarketSnapshot (Immutable SNAP-ID)]
                  ↓
[8-Layer Multi-Model Evaluation & Zero-Trust Consensus]
                  ↓
       ┌───────────────────────────┬───────────────────────────┐
       ↓                           ↓                           ↓
[GET /signals/h4-intelligence] [GET /live/today] [GET /system-intelligence/canonical-signals]
       ↓                           ↓                           ↓
[H4Forecasts.tsx]          [TodaysSignals.tsx]     [TradingDashboard.tsx / DCC]
```

---

## 2. Asset Feed Lineage Table

| Asset | Primary Feed | Secondary Feed | Storage Table | Normalizer Service | Canonical Downstream Route | Frontend Consumers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EURUSD** | Yahoo Finance (`EURUSD=X`) | TradingView (`FX:EURUSD`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **GBPUSD** | Yahoo Finance (`GBPUSD=X`) | TradingView (`FX:GBPUSD`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **USDJPY** | Yahoo Finance (`JPY=X`) | TradingView (`FX:USDJPY`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **AUDUSD** | Yahoo Finance (`AUDUSD=X`) | TradingView (`FX:AUDUSD`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **BTCUSD** | Yahoo Finance (`BTC-USD`) | TradingView (`BINANCE:BTCUSDT`)| `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **ETHUSD** | Yahoo Finance (`ETH-USD`) | TradingView (`BINANCE:ETHUSDT`)| `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **XAUUSD** | Yahoo Finance (`GC=F`) | TradingView (`OANDA:XAUUSD`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **NAS100** | Yahoo Finance (`NQ=F`) | TradingView (`NASDAQ:NDX`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |
| **SPX500** | Yahoo Finance (`ES=F`) | TradingView (`SP:SPX`) | `historical_candles` | `CanonicalMarketDataService` | `/h4-intelligence`, `/live/today` | `H4Forecasts`, `TodaysSignals`, `Dashboard` |

---

## 3. Market Data Freshness Policy & Gating Rules

1. **Age Threshold ($T_{\text{fresh}} < 120\text{s}$):**
   - $\text{age} < 120\text{s} \implies \text{status} = \text{FRESH}$ (Eligible for Zero-Trust Strong Signal qualification).
   - $\text{age} \ge 120\text{s} \implies \text{status} = \text{STALE}$ (Strictly gates signal to `NO_TRADE` with reason `STALE_MARKET_DATA`).
2. **Temporal Monotonicity:**
   - If market timestamp regresses ($\Delta t < 0$), state is marked `INVALID`.
3. **Price Sanity & Finite Value Gate:**
   - If price is $\le 0$, $\text{NaN}$, or $\infty$, data is marked `INVALID` and gated.
4. **Bid/Ask Integrity:**
   - If bid/ask quote feeds are not provided by the exchange, explicit `bid: NOT_AVAILABLE` / `ask: NOT_AVAILABLE` is emitted — **never fabricated**.
