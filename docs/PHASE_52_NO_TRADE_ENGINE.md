# Phase 52 NO-TRADE Rejection Engine Specification

**Objective:** Institutional Capital Preservation via Strict Pre-Trade Gating.

---

## 1. Catalog of Explicit Rejection Reasons

1. `DATA_STALE`: Market data feed older than $2.5\times$ candle interval.
2. `DATA_UNAVAILABLE`: Primary and secondary data providers offline.
3. `DATA_CORRUPTED`: Impossible OHLC relationship (e.g. High < Low, negative price, future timestamps).
4. `HIGH_SPREAD`: Current bid/ask spread exceeds asset maximum threshold (e.g. >4.0 pips on EURUSD).
5. `LOW_LIQUIDITY`: Volume below 20-period moving average cutoff.
6. `CONFLICTING_STRUCTURE`: Direction directly opposes active BOS/CHoCH structural bias.
7. `NO_HTF_ALIGNMENT`: Setup attempts to trade against the 4H/1D higher timeframe trend.
8. `LOW_CONFLUENCE`: Composite multi-layer score below 50.0.
9. `POOR_RR`: Risk-to-Reward ratio below 1.2:1 minimum gate.
10. `HIGH_VOLATILITY`: Abnormal ATR expansion exceeding $3.0\times$ normal baseline.
11. `EVENT_RISK`: High-impact macroeconomic news release (NFP, CPI, FOMC, Rate Decision) within $\pm 30$ minutes.
12. `ENTRY_EXPIRED`: Real-world time exceeds authoritative dynamic entry window.
13. `SIGNAL_INVALIDATED`: Invalidation price level breached before fill.
14. `PORTFOLIO_RISK`: Portfolio daily drawdown exceeds 5.0% circuit breaker.
15. `CORRELATED_EXPOSURE`: Correlated currency exposure limit exceeded (e.g. >3.0 lots short USD).
16. `INSUFFICIENT_EVIDENCE`: Split strategy ensemble without directional consensus.
