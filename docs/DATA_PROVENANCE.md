# Data Provenance & Audit Trail — TradeSignalAI-v3

## 1. Provenance Schema

Every market quote, historical bar, and candidate signal in TradeSignalAI-v3 contains an immutable provenance envelope.

```json
{
  "symbol": "USDJPY",
  "canonical_symbol": "USDJPY",
  "venue": "MetaQuotes-Demo",
  "provider": "MT5",
  "data_role": "PRIMARY_LIVE",
  "asset_class": "FOREX",
  "timeframe": "H1",
  "source_timestamp": "2026-09-28T00:05:00.000000Z",
  "received_timestamp": "2026-09-28T00:05:00.245000Z",
  "data_age_ms": 245.0,
  "freshness_status": "FRESH",
  "broker": "MetaQuotes Software Corp.",
  "server": "MetaQuotes-Demo"
}
```

---

## 2. Mandatory Provenance Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `symbol` | string | Provider-specific symbol (e.g., `USDJPY.pro`, `BTCUSDT`) |
| `canonical_symbol` | string | Canonical identifier in `CanonicalAssetRegistry` |
| `venue` | string | Execution or broker venue (e.g., `BINANCE`, `Pepperstone-Live01`) |
| `provider` | string | Underlying driver: `MT5`, `BINANCE`, `TRADINGVIEW`, `YFINANCE` |
| `data_role` | string | `PRIMARY_LIVE`, `SECONDARY_VALIDATION`, `HISTORICAL_SECONDARY`, `CACHE` |
| `asset_class` | string | `FOREX`, `CRYPTO`, `EQUITY`, `COMMODITY` |
| `timeframe` | string | Normalized timeframe: `M5`, `M15`, `M30`, `H1`, `H4`, `D1` |
| `source_timestamp` | ISO8601 | Original timestamp provided by exchange/broker feed |
| `received_timestamp`| ISO8601 | Ingestion timestamp recorded upon gateway arrival |
| `data_age_ms` | float | Millisecond latency: `(received_time - source_time)` |
| `freshness_status` | enum | `FRESH`, `STALE`, `EXPIRED`, `UNAVAILABLE`, `INVALID` |

---

## 3. Signal Decision Audit Trail

When a candidate signal is created or blocked, the forensic record logs:
1. **Pre-flight Market Session Result**: `OPEN` / `CLOSED` (with local & UTC market timestamps).
2. **Freshness Assessment**: `data_age_ms` vs `max_age_seconds`.
3. **Primary Data Snapshot**: Bid, Ask, Spread, Last, OHLC array.
4. **Resolution Evidence**: Reference to actual future bars that resolved the signal.

This ensures zero ambiguity: every signal can be forensically explained from its underlying market data evidence.
