# AUDIT: PHASE 64 SIGNAL GENERATION & PRODUCT MODEL
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 64 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. Signal Product Architecture

Every canonical signal is modeled as an immutable `SignalProduct` with time-locked state:
- **Canonical ID:** Deterministic SHA-256 hash derived from `(asset, timeframe, data_cutoff_time, direction, config_hash)`
- **Temporal Locks:** `created_at` (generation time), `data_cutoff_time` (T0 barrier), `expiry_time` (precomputed horizon)
- **Execution Bounds:** `entry_price`, `stop_loss`, `take_profit`, `risk_reward` ($\ge 1.50$)
- **Empirical Probabilities:** `calibrated_probability`, $P(\text{TP First})$, $P(\text{SL First})$, $P(\text{Time Exit})$
- **Friction Accounting:** Pre-calculated Spread ($0.0001$), Slippage ($0.00005$), Broker Fees ($0.00005$)
- **Quality Grade:** $A+$, $A$, $B$, $C$, $\text{WATCH}$, $\text{REJECTED}$ based on multivariate empirical evidence

---

## 2. Multi-Timeframe Independent Horizons

| Timeframe | Default Horizon | Typical Expiry | TP/SL Multiplier | Primary Use Case |
|---|---|---|---|---|
| **5m** | 30 min | $T_0 + 30\text{m}$ | $1.5 \times \text{ATR}_{5\text{m}}$ | High-frequency Scalp |
| **15m** | 1 hour | $T_0 + 1\text{h}$ | $1.8 \times \text{ATR}_{15\text{m}}$ | Intraday Session Setup |
| **30m** | 2 hours | $T_0 + 2\text{h}$ | $2.0 \times \text{ATR}_{30\text{m}}$ | Intraday Trend Continuity |
| **1H** | 4 hours | $T_0 + 4\text{h}$ | $2.0 \times \text{ATR}_{1\text{h}}$ | Intraday Anchor Direction |
| **2H** | 8 hours | $T_0 + 8\text{h}$ | $2.2 \times \text{ATR}_{2\text{h}}$ | Inter-Session Rotation |
| **4H** | 24 hours | $T_0 + 24\text{h}$ | $2.5 \times \text{ATR}_{4\text{h}}$ | Daily Macro Momentum |
| **12H** | 48 hours | $T_0 + 48\text{h}$ | $2.8 \times \text{ATR}_{12\text{h}}$ | Multi-Day Swing |
| **1D** | 5 days | $T_0 + 5\text{d}$ | $3.0 \times \text{ATR}_{1\text{d}}$ | Weekly Positional Trend |
| **SWING** | 10 days | $T_0 + 10\text{d}$ | $3.5 \times \text{ATR}_{1\text{d}}$ | Macro Cyclical Position |

---

## 3. Idempotent Deduplication & Cooldown

- Repeated queries at the same candle timestamp return the identical canonical signal ID and content hash.
- Cooldown logic prevents generating multiple conflicting signals on adjacent sub-minute ticks.
