# PHASE 61 — MARKET DATA VALIDATION & LINEAGE REPORT

**Project**: TradeSignalAI-v3  
**Audit Phase**: PHASE 61 — Adversarial Certification Repair, Boundary Testing & Live Canonical Truth  
**Generated At**: 2026-08-24T06:21:00Z  
**Configuration Hash**: `79a4f8e12b79310d`  
**Monitored Core Assets**: 9  

---

## 1. Asset Registry & Data Lineage

The system maintains a strictly defined market lineage for all 9 core monitored assets across 4 major asset classes:

| Symbol | Asset Class | Primary Data Feed | Secondary Source | Session Schedule | Base Price (Anchor) | Freshness Gate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EURUSD** | Forex Major | Yahoo Finance (`EURUSD=X`) | TradingView (`FX:EURUSD`) | Sun 22:00 – Fri 22:00 UTC | `1.0850` | `< 120.0s` |
| **GBPUSD** | Forex Major | Yahoo Finance (`GBPUSD=X`) | TradingView (`FX:GBPUSD`) | Sun 22:00 – Fri 22:00 UTC | `1.2720` | `< 120.0s` |
| **USDJPY** | Forex Major | Yahoo Finance (`JPY=X`) | TradingView (`FX:USDJPY`) | Sun 22:00 – Fri 22:00 UTC | `152.40` | `< 120.0s` |
| **AUDUSD** | Forex Major | Yahoo Finance (`AUDUSD=X`) | TradingView (`FX:AUDUSD`) | Sun 22:00 – Fri 22:00 UTC | `0.6550` | `< 120.0s` |
| **BTCUSD** | Crypto | Yahoo Finance (`BTC-USD`) | Binance / Coinbase | 24/7/365 Continuous | `67450.00` | `< 120.0s` |
| **ETHUSD** | Crypto | Yahoo Finance (`ETH-USD`) | Binance / Coinbase | 24/7/365 Continuous | `3520.00` | `< 120.0s` |
| **XAUUSD** | Metals / Commodities | Yahoo Finance (`GC=F`) | TradingView (`OANDA:XAUUSD`) | Sun 22:00 – Fri 21:00 UTC (Daily Break) | `2350.00` | `< 120.0s` |
| **NAS100** | Index CFD | Yahoo Finance (`NQ=F` / `^IXIC`) | TradingView (`NASDAQ:NDX`) | Mon–Fri US Trading (Settlement Break) | `18200.00` | `< 120.0s` |
| **SPX500** | Index CFD | Yahoo Finance (`ES=F` / `^GSPC`) | TradingView (`SP:SPX`) | Mon–Fri US Trading (Settlement Break) | `5300.00` | `< 120.0s` |

---

## 2. Boundary Validation Rules

1. **Numerical & Price Finite Check**:
   - Every price $P$ must be a finite real number: $P \in \mathbb{R}$, $P > 0.0$, and $P \notin \{\text{NaN}, +\infty, -\infty\}$.
   - Any price violation marks `data_freshness.status = "INVALID"` and immediately gates decision to `NO_TRADE` with `INVALID_MARKET_DATA`.

2. **Temporal Freshness Gate**:
   - Market data age $T_{\text{age}} = T_{\text{now}} - T_{\text{market\_data}}$.
   - $T_{\text{age}} < 120.0\text{s} \implies \text{FRESH}$ (Eligible for candidate signal).
   - $T_{\text{age}} \ge 120.0\text{s} \implies \text{STALE}$ (Hard gate to `NO_TRADE` with `STALE_MARKET_DATA`).

3. **Session State Gate**:
   - Forex, Metals, and Indices evaluate active session windows.
   - Closed sessions return `is_market_open = false` and gate to `NO_TRADE` with `MARKET_CLOSED`.
   - Crypto (`BTCUSD`, `ETHUSD`) operates 24/7 and is never gated by weekend closure.

---

## 3. Snapshot Data Flow Verification

```
┌────────────────────────────────────────────────────────┐
│               Live Market Data Providers               │
│   (Yahoo Finance / TradingView Secondary Verification) │
└──────────────────────────┬─────────────────────────────┘
                           │ Raw Ticks / Candles
                           ▼
┌────────────────────────────────────────────────────────┐
│           CanonicalSignalService (Engine 60.0)         │
│  - Mathematical Price Validation (Finite, >0)          │
│  - Monotonic Timestamp Verification                    │
│  - Freshness Calculation (< 120s)                      │
│  - Atomic Snapshot Generation (60s TTL Lock)           │
│  - Deterministic Content Hash Computation (SHA-256)    │
└──────────────────────────┬─────────────────────────────┘
                           │ CanonicalMarketSnapshot
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  H4 Matrix   │    │ Live Today   │    │Runtime Truth │
│  (/signals/  │    │ (/live/      │    │(/system-int/ │
│ h4-intell.)  │    │  today)      │    │runtime-truth)│
└──────────────┘    └──────────────┘    └──────────────┘
```
