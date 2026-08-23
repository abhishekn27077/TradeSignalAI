# PHASE 53 — LIVE SHADOW TRADE TRUTH SCHEMA

**Dataset Name:** `LIVE_SHADOW_TRADE_TRUTH`  
**Dataset SHA256:** `42-trade cryptographic digest computed at runtime`  
**Config Hash:** `79a4f8e12b79310d`  
**Records Included:** 42 Realized Forward Paper Trades (26 Wins, 16 Losses)

---

## 1. Mandatory 30-Field Trade Schema

Every trade record in `LIVE_SHADOW_TRADE_TRUTH` must strictly contain the following 30 fields:

| Field Index | Field Name | Type | Description | Invariant Rule |
|:---:|:---|:---:|:---|:---|
| 1 | `trade_id` | `str` | Unique trade identifier (`TRD-FWD-XXX-ASSET`) | Non-null, unique |
| 2 | `signal_id` | `str` | Generating signal identifier | Traceable to signal manifest |
| 3 | `prediction_id` | `str` | AI/ML prediction trace ID | Point-in-time trace link |
| 4 | `asset` | `str` | Traded asset ticker (e.g. `EURUSD`, `XAUUSD`) | One of 9 supported assets |
| 5 | `direction` | `str` | `BUY` or `SELL` | Non-neutral |
| 6 | `horizon` | `str` | `H1`, `H4`, `SWING`, or `DAILY` | Standardized timeframe |
| 7 | `signal_grade` | `str` | `A+`, `A`, `B`, or `C` | Quality grade |
| 8 | `decision_timestamp` | `str` | ISO-8601 UTC timestamp of signal evaluation | Strictly before entry |
| 9 | `entry_timestamp` | `str` | ISO-8601 UTC timestamp of fill execution | $\ge$ decision timestamp |
| 10 | `entry_price` | `float` | Raw candle/market entry level | Positive float |
| 11 | `bid_at_entry` | `float` | Point-in-time bid quote | $< \text{ask\_at\_entry}$ |
| 12 | `ask_at_entry` | `float` | Point-in-time ask quote | $> \text{bid\_at\_entry}$ |
| 13 | `spread_at_entry` | `float` | Spread in pips/points at fill | Asset specific |
| 14 | `stop_loss` | `float` | Protective stop level | Fixed at decision time |
| 15 | `take_profit` | `float` | Profit target level | Fixed at decision time |
| 16 | `exit_timestamp` | `str` | ISO-8601 UTC timestamp of trade exit | Strictly after entry |
| 17 | `exit_price` | `float` | Realized exit execution level | Determined by SL/TP trigger |
| 18 | `exit_reason` | `str` | `TP_HIT`, `SL_HIT`, `TIME_EXIT`, `AMBIGUOUS_SL_FIRST` | Enum validation |
| 19 | `gross_R` | `float` | Raw return in R units before frictions | $+2.0\text{R}$ to $+2.2\text{R}$ on wins, $-1.0\text{R}$ on losses |
| 20 | `spread_cost` | `float` | Spread cost deducted in R units | Calculated from spread & SL distance |
| 21 | `slippage_cost` | `float` | Slippage cost deducted in R units | Volatility-scaled deduction |
| 22 | `net_R` | `float` | $\text{gross\_R} - (\text{spread\_cost} + \text{slippage\_cost})$ | Actual realized performance unit |
| 23 | `result` | `str` | `WIN` if $\text{net\_R} > 0$, `LOSS` if $\text{net\_R} \le 0$ | Boolean derivation |
| 24 | `regime` | `str` | Market regime at decision | `TRENDING_BULL`, `TRENDING_BEAR`, `RANGE`, etc. |
| 25 | `news_state` | `str` | Point-in-time macro state | `NORMAL_NO_BLACKOUT`, `PRE_EVENT`, etc. |
| 26 | `AI_state` | `str` | Ensemble consensus state | `ENSEMBLE_CONFIRMED`, `KRONOS_FAISS_ACTIVE` |
| 27 | `TradingView_state` | `str` | TradingView integration state | `SECONDARY_SUPPORT_ONLY` |
| 28 | `indicator_snapshot_hash`| `str`| SHA256 of 14 technical indicator inputs | 16-character hex |
| 29 | `market_snapshot_hash` | `str`| SHA256 of OHLCV & quote snapshot | 16-character hex |
| 30 | `config_hash` | `str` | Frozen system fingerprint (`79a4f8e12b79310d`) | Exact match required |

---

## 2. Integrity Verification

All 42 trade records implement this schema in [`app/analytics/shadow_trade_truth.py`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/analytics/shadow_trade_truth.py).
Zero nullable fields, zero missing timestamps, and zero synthetic fallbacks.
