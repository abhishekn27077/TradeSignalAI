# Market Session Policy & Session-Aware Gating

## 1. The Core Invariant

> **The system must NEVER generate an actionable signal for an asset whose market session is CLOSED.**

No strategy signals, pending setups, or simulated orders may be emitted during market closures.

---

## 2. Forex Session Schedule

- **Forex Standard Trading Week**:
  - **Open**: Sunday 21:00 UTC (02:30 AM Monday IST / 17:00 EST).
  - **Close**: Friday 21:00 UTC (02:30 AM Saturday IST / 17:00 EST).
  - **Weekend Closure**: Friday 21:00 UTC through Sunday 21:00 UTC.
  - **Daily Rollover / Broker Maintenance**: Typically 21:00 - 22:00 UTC (broker dependent).

### Sunday Evening Regression Protection
- **Example Scenario**: Sunday 27 September 2026, 19:17 IST (13:47 UTC).
  - **Forex (USDJPY)**: Session is **CLOSED** (remains closed until 21:00 UTC).
  - **Decision**: `SIGNAL_BLOCKED` (Reason: `MARKET_CLOSED`).
  - **UI Display**: **`MARKET CLOSED — Forex market opens Sunday 21:00 UTC`**.
  - **Crypto (BTCUSDT)**: Session is **OPEN** (24/7). Signal generation permitted if live feeds are fresh and strategy conditions are met.

---

## 3. Crypto Session Schedule

- **Continuous 24/7/365**:
  - `open_all_week = True`
  - Validated across venues (`BINANCE`).
  - Subject only to exchange-announced maintenance windows.

---

## 4. Pre-Flight Session Gating Architecture

Session verification occurs at the **point of execution**, immediately before candidate signal formation:

```python
# app/core/signal_factory.py & app/runtime/prospective_signal_scheduler.py
is_open = market_session_service.is_market_open(symbol=symbol, dt=evaluation_time)
if not is_open:
    logger.warning(f"[SESSION_BLOCK] {symbol} market is CLOSED at {evaluation_time.isoformat()}. Signal generation blocked.")
    return None  # Fail closed: reject signal creation
```

This prevents the critical flaw where background schedulers or stale candle pollers create "BUY" signals while global markets are shut.
