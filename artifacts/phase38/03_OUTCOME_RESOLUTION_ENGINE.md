# Phase 38 Artifact 03: Outcome Resolution Engine Specification

## Engine Rules (`app/execution/outcome_engine.py`)

### 1. Zero Lookahead Bias
Candles evaluated are strictly filtered by `candle.timestamp > signal.prediction_timestamp`. The candle upon which the signal was formed is never evaluated for trade outcome.

### 2. Intermediate Closed Candle Checking
Rather than waiting for the entire holding horizon (e.g. 4 hours or 24 hours) to elapse, each closed subsequent candle is evaluated chronologically.
- If candle `High >= TP` (for BUY) or `Low <= TP` (for SELL) $\implies$ `TP_HIT` resolved at Take Profit price.
- If candle `Low <= SL` (for BUY) or `High >= SL` (for SELL) $\implies$ `SL_HIT` resolved at Stop Loss price.

### 3. Same-Candle Ambiguity
If both `High >= TP` and `Low <= SL` occur within the exact same candle bar, the engine cannot know intrabar order without tick-level order book replays. Under Zero-Trust rules, this is strictly marked as `AMBIGUOUS`.

### 4. Time Expiry Exit
When candle timestamp reaches or exceeds `expiry_time` and neither TP nor SL was touched, the trade is closed at that candle's `close` price with resolution method `TIME_EXPIRY`.
