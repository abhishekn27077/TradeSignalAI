# TradeSignalAI-v3 — Complete System Analysis & Roadmap
## Why Signals Are Inaccurate + What's Missing + How to Fix It

**Date:** 2026-08-26  
**Status:** Deep-dive analysis complete

---

## 1. ROOT CAUSE: Why Signals Are Not Accurate

### The Signal Generation Chain (Current State)

```
Market Data → Models → Consensus → Risk → Execution
     ↓            ↓         ↓         ↓        ↓
  STALE DB    PARTIAL    FAKE+REAL  BROKEN   PAPER
  (12-28d)    (Kronos    (hash +    (fixed)  (fixed)
              only)      Kronos)
```

### Problem #1: Market Data is STALE (Critical)

Your database has historical candles but they are **12-28 days old** for most timeframes:

| Symbol | Timeframe | Last Updated | Age |
|--------|-----------|-------------|-----|
| EURUSD | 1h | 2026-08-14 | 12.4 days |
| EURUSD | 4h | 2026-08-14 | 12.5 days |
| BTCUSD | 4h | 2026-08-14 | 12.5 days |
| XAUUSD | 1h | 2026-08-14 | 12.6 days |
| EURUSD | 1H (fresh) | 2026-08-26 | 2.4 hours ✓ |

**Only the `1H` timeframe (uppercase) has fresh data.** The `1h`, `4h`, `1d` timeframes are all stale.

**Why:** The data providers (`tvdatafeed` for TradingView, `yfinance`) are **NOT INSTALLED**:
```
pip list | grep -iE 'tvdatafeed|yfinance'
→ (empty — neither is installed)
```

So when the system tries to fetch live data, it fails silently and falls back to the stale SQLite store.

### Problem #2: Quant Baseline is FAKE (Critical)

The "Quant Baseline" model (Layer 1, weight 0.20) generates votes using a **hash of the timestamp**, not real technical analysis:

```python
# app/core/canonical_signal_service.py:384-388
ts_seed = dt_utc.strftime("%Y%m%d%H")
hash_seed = int(hashlib.sha256(f"{asset}_{ts_seed}_{CONFIG_HASH}".encode()).hexdigest()[:8], 16)
quant_dir = "BUY" if (hash_seed % 3 == 0) else "SELL" if (hash_seed % 3 == 1) else "NEUTRAL"
```

This means:
- Same hour → same signal (deterministic, not market-driven)
- The "evidence" string is hardcoded: `"RSI(14)=54.2, MACD=BullishCross"` — these numbers are FICTION
- This model contributes 20% of the consensus weight with ZERO real analysis

### Problem #3: Kronos Uses Stale Data (High)

Kronos IS a real PyTorch transformer model and IS loaded correctly:
```
"Successfully loaded PyTorch Kronos model from local cache."
```

But it runs inference on **12-day-old candles** from SQLite. So its predictions are based on outdated market conditions.

### Problem #4: AI Consensus Falls Back to Heuristic (High)

From the runtime logs:
```
OpenRouter server error (429), attempt 3
OpenRouter failed after 3 attempts
Gemini returned 404: models/openrouter/free is not found
Local Heuristic Engine analyzing prompt: You are the Chief Trader...
```

The LLM providers fail (rate limits, wrong model name), so the system falls back to the **HeuristicProvider** which:
- Computes `confidence = 0.75 + (volatility * 10)` — higher volatility = higher confidence (BACKWARDS)
- Adds pseudo-randomness via MD5 hash
- Is NOT an AI model at all

### Problem #5: Signal Repetition (Medium)

Confirmed in database:
```
SPX500   SELL  2026-08-25  x6  (same direction, 6 times in one day)
NAS100   SELL  2026-08-25  x4
XAUUSD   SELL  2026-08-25  x4
```

The `SignalIdentityGuard` exists but is **never called** in the signal generation hot path. No deduplication occurs.

### Problem #6: No Real-Time Price Feed (Critical)

The `RealtimeStreamManager` polls every 60 seconds, but:
- It reads from SQLite (stale data)
- No WebSocket connection to any exchange/broker
- No TradingView live feed (tvdatafeed not installed)
- The "price" used for signals is the last candle close from 12 days ago

---

## 2. WHAT THE SYSTEM CAN ACTUALLY DO (Honest Assessment)

### Working ✓
- Kronos transformer model loads and runs inference (real PyTorch)
- XGBoost/RandomForest/HistGB statistical adapters exist
- Signal lifecycle tracking in database
- Paper trading executor (now fixed with input validation)
- Risk engine RR check (now fixed with correct key)
- Failsafe kill switch (now reads real balance)
- Auth system (now fail-closed)
- 892 tests passing
- Frontend dashboard renders

### Broken / Fake ✗
- Real-time market data (providers not installed)
- Quant Baseline model (hash-based, not real TA)
- AI consensus (falls back to heuristic)
- Signal deduplication (guard never called)
- Reconciliation engine (placeholder)
- Tomorrow forecast (exists but uses stale data)
- Fresh candle download (no working provider)

### Missing Entirely
- Walk-forward validation pipeline
- Model calibration tracking
- Signal accuracy measurement (hit rate tracking)
- Time-of-day seasonality analysis (your "15:05 BUY every day" idea)
- Multi-timeframe confluence scoring
- Proper backtesting with realistic slippage/fees
- A/B testing framework for model changes
- Alert system for signal changes

---

## 3. WHAT BIG COMPANIES DO (And What You Need)

### How Proprietary Trading Firms Test AI Models

| Practice | What They Do | What You Have | Gap |
|----------|-------------|---------------|-----|
| **Walk-Forward Validation** | Train on window N, test on N+1, roll forward | `walk_forward.py` exists but not integrated | HIGH |
| **Out-of-Sample Testing** | Never touch test set during development | Some OOS reports exist | MEDIUM |
| **Calibration Tracking** | "When model says 70%, does it hit 70%?" | `calibration_engine.py` exists | MEDIUM |
| **Signal Decay Monitoring** | Track if model edge degrades over time | `edge_drift_engine.py` exists | MEDIUM |
| **A/B Testing** | Run new model in shadow vs production | `champion_challenger_engine.py` exists | MEDIUM |
| **Real-Time Data Pipeline** | Sub-second market data via WebSocket/API | STALE SQLite only | CRITICAL |
| **Feature Store** | Versioned, point-in-time features | `feature_store.py` exists | LOW |
| **Model Registry** | Track model versions, promote/demote | `forecast_engine/registry/` exists | LOW |
| **Execution Analytics** | Slippage, fill rate, latency tracking | Basic paper executor | HIGH |
| **Risk-Adjusted Metrics** | Sharpe, Sortino, max DD, Calmar | Some in analytics | MEDIUM |

### The Critical Gap: DATA PIPELINE

Every serious trading system has this:
```
Exchange/Broker API → WebSocket → Normalizer → Feature Store → Models → Signals
       ↑                                                          ↓
       └──────────── Reconciliation ← Execution ← Risk ←──────────┘
```

Your system has the right architecture but the **first link is broken** — no live data source.

---

## 4. RECOMMENDED ROADMAP

### Phase A: Fix Data Pipeline (Week 1) — MOST CRITICAL

1. **Install data providers:**
   ```bash
   pip install tvDatafeed yfinance
   ```

2. **Add a free real-time forex source:**
   - Option 1: MetaTrader 5 (already installed!) — use `mt5` Python package for live ticks
   - Option 2: Twelve Data API (free tier: 800 credits/day)
   - Option 3: Alpha Vantage (free: 25 requests/day)
   - Option 4: Binance WebSocket (free, real-time crypto)

3. **Build a candle updater** that runs every 5 minutes:
   - Fetch latest candles from live source
   - Upsert into `historical_candles` table
   - Mark data freshness timestamp

4. **Fix the provider fallback chain:**
   - Priority: Live WebSocket → REST API → SQLite cache
   - Never use data older than 1 hour for signal generation
   - If no fresh data available → emit NO_TRADE, not a signal

### Phase B: Fix Model Layer (Week 2)

5. **Replace hash-based Quant Baseline with real indicators:**
   ```python
   # Instead of hash_seed % 3:
   rsi = compute_rsi(df['close'], 14)
   macd_signal = compute_macd_cross(df)
   ema_trend = df['close'] > df['close'].rolling(50).mean()
   # Combine into a real technical score
   ```

6. **Fix AI consensus model routing:**
   - Fix Gemini model name (remove `openrouter/free` prefix)
   - Add proper retry with exponential backoff
   - If all LLMs fail → use statistical models only, don't use heuristic

7. **Wire Kronos to fresh data:**
   - Ensure `_load_recent_candles()` gets data < 1 hour old
   - Add data freshness check before running inference
   - If data is stale → mark Kronos as UNAVAILABLE

### Phase C: Signal Quality (Week 3)

8. **Implement signal deduplication:**
   - Call `SignalIdentityGuard.is_duplicate()` before persisting any signal
   - Add cooldown: same asset+direction cannot repeat within 4 hours
   - Track "signal changed direction" events for the UI

9. **Add time-of-day seasonality analysis:**
   - For each asset, compute historical win rate by hour-of-day
   - Example: "EURUSD BUY at 15:00 IST has 68% win rate over 6 months"
   - Use this as a confidence booster/penalty in consensus

10. **Build tomorrow's signal schedule:**
    - At market close, run all models on today's data
    - Generate predicted signals for tomorrow with specific times
    - Store as `ForecastSnapshot` with immutable hash
    - Display in UI: "EURUSD BUY at 10:00, GBPUSD SELL at 14:00"

### Phase D: Validation & Monitoring (Week 4)

11. **Walk-forward validation pipeline:**
    - Train on months 1-6, test on month 7
    - Roll forward: train 2-7, test 8
    - Report: hit rate, avg R, Sharpe per window
    - If any window shows < 50% accuracy → flag model as degraded

12. **Signal accuracy dashboard:**
    - Track every signal's outcome (TP_HIT, SL_HIT, TIME_EXIT)
    - Compute rolling 7-day, 30-day accuracy per asset
    - Alert when accuracy drops below 55%

13. **Model calibration:**
    - When model says "70% confidence", track actual hit rate
    - If 70% confidence signals only hit 52% → model is overconfident
    - Apply calibration correction

14. **A/B testing (Champion/Challenger):**
    - Run new model versions in shadow mode
    - Compare against production model
    - Only promote if challenger beats champion over 100+ signals

---

## 5. SPECIFIC BUGS CAUSING ERRORS

| Bug | Location | Impact | Status |
|-----|----------|--------|--------|
| `tvdatafeed` not installed | requirements.txt | No TradingView data | UNFIXED |
| `yfinance` not installed | requirements.txt | No Yahoo Finance data | UNFIXED |
| Gemini model name wrong | `router.py:47` | AI consensus fails | UNFIXED |
| OpenRouter rate limited | Runtime | AI falls back to heuristic | UNFIXED |
| Quant baseline is hash-based | `canonical_signal_service.py:384` | Fake signals | UNFIXED |
| Signal dedup never called | `coordinator.py` | Repeated signals | UNFIXED |
| Stale data used for inference | `_load_recent_candles()` | Wrong predictions | UNFIXED |
| `1h` vs `1H` timeframe mismatch | DB queries | Some queries miss data | UNFIXED |

---

## 6. STRONG REBUILD PROMPT

Use this prompt with a capable AI agent to rebuild the signal pipeline properly:

---

```markdown
# TradeSignalAI-v3 — Signal Pipeline Rebuild

## Context
You are working on TradeSignalAI-v3 at D:/trading Bots/FinalTrade/TradeSignalAI-v3.
It's a FastAPI + React trading signal platform with:
- Kronos (PyTorch transformer) for time-series prediction
- XGBoost/RF/HistGB statistical models
- Multi-agent AI consensus (OpenRouter/Gemini)
- SQLite database (tradesignal.db) with historical_candles table
- Paper trading executor

## Current Problems (CONFIRMED)
1. No live market data — tvdatafeed and yfinance are NOT installed
2. Quant Baseline model uses sha256(timestamp) hash instead of real indicators
3. AI consensus falls back to a fake heuristic when LLMs fail
4. Signals repeat 4-6x per day (no deduplication in hot path)
5. Kronos runs on 12-day-old candles
6. No time-of-day seasonality analysis
7. No walk-forward validation integrated into signal generation

## Your Task: Rebuild the Signal Pipeline

### Step 1: Install Data Providers
```bash
pip install tvDatafeed yfinance MetaTrader5
```
Verify they import correctly. If tvDatafeed fails (it often does on Windows),
use MetaTrader5 as primary (already installed) and yfinance as fallback.

### Step 2: Build Live Data Service
Create `app/market_data/live_feed.py`:
- Connect to MetaTrader5 for forex/indices (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, NAS100, SPX500)
- Connect to Binance WebSocket for crypto (BTCUSD, ETHUSD)
- Every 60 seconds: fetch latest ticker prices
- Every 5 minutes: download and upsert new candles into historical_candles
- Track `last_updated_at` per symbol+timeframe
- If data is older than 15 minutes → mark as STALE, refuse to generate signals

### Step 3: Replace Hash-Based Quant Baseline
In `app/core/canonical_signal_service.py`, replace the hash_seed logic with REAL indicators:
```python
import pandas as pd
import numpy as np

def compute_real_technical_score(df: pd.DataFrame) -> tuple[str, float]:
    """Compute real technical analysis score from OHLCV data."""
    close = df['close']
    
    # RSI(14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macd_cross = macd.iloc[-1] > signal.iloc[-1]
    
    # EMA Trend
    ema50 = close.rolling(50).mean()
    trend_up = close.iloc[-1] > ema50.iloc[-1]
    
    # ATR for volatility
    high_low = df['high'] - df['low']
    high_close = (df['high'] - close.shift()).abs()
    low_close = (df['low'] - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    atr_pct = atr / close.iloc[-1]
    
    # Score: combine signals
    score = 0.0
    if rsi.iloc[-1] < 30: score += 0.3  # oversold = buy
    elif rsi.iloc[-1] > 70: score -= 0.3  # overbought = sell
    if macd_cross: score += 0.3
    else: score -= 0.3
    if trend_up: score += 0.2
    else: score -= 0.2
    
    direction = "BUY" if score > 0.2 else "SELL" if score < -0.2 else "NEUTRAL"
    confidence = min(0.95, 0.5 + abs(score))
    
    return direction, confidence, {
        "rsi": round(rsi.iloc[-1], 1),
        "macd_bullish": macd_cross,
        "ema_trend_up": trend_up,
        "atr_pct": round(atr_pct * 100, 3)
    }
```

### Step 4: Add Signal Deduplication
In the coordinator's `_on_consensus_completed()`, BEFORE persisting:
```python
from app.core.signal_identity import SignalIdentityGuard

identity_hash = SignalIdentityGuard.build_identity(trade_proposal)
async for session in get_db_session():
    if await SignalIdentityGuard.is_duplicate(session, identity_hash):
        logger.warning(f"Duplicate signal blocked: {trade_proposal['symbol']}")
        return
    break
```

Also add a 4-hour cooldown: same asset+direction cannot fire again within 4 hours.

### Step 5: Add Time-of-Day Seasonality
Create `app/analytics/seasonality_engine.py`:
- For each asset, analyze historical signals by hour-of-day (IST)
- Compute: win_rate_by_hour[asset][hour] over last 6 months
- When generating a signal, look up the historical win rate for that hour
- If win rate < 45% for that hour → reduce confidence by 0.1
- If win rate > 65% → boost confidence by 0.05
- Expose via API: GET /api/v1/analytics/seasonality?asset=EURUSD

### Step 6: Tomorrow Signal Schedule
Create `app/analytics/tomorrow_schedule.py`:
- At 21:00 IST daily (after market close), run all models on today's data
- For each asset, predict: direction, confidence, optimal entry time
- Use time-of-day seasonality to pick the best hour
- Store as immutable ForecastSnapshot
- API: GET /api/v1/live/tomorrow returns the schedule
- Frontend: display as a timeline "EURUSD BUY 10:00 | GBPUSD SELL 14:00 | ..."

### Step 7: Fix AI Consensus Fallback
In `app/agents/providers/router.py`:
- Fix Gemini model name: use "gemini-2.0-flash" not "openrouter/free"
- If ALL LLM providers fail → return None (don't use heuristic)
- In consensus engine: if AI layer returns None → mark as UNAVAILABLE, exclude from consensus
- Never let the heuristic provider override real model outputs

### Step 8: Walk-Forward Validation Gate
Before any signal is emitted:
- Check: has this model been validated on out-of-sample data in the last 30 days?
- If not → mark signal as "UNVALIDATED" and reduce confidence by 0.15
- Track validation status per model in a registry table

### Step 9: Signal Change Detection
When a new signal differs from the previous signal for the same asset:
- Log: "EURUSD changed from BUY to SELL at 14:30 IST"
- Store in a `signal_changes` table
- Broadcast via WebSocket to frontend
- Frontend shows: "⚠️ Signal Changed: EURUSD BUY→SELL"

### Step 10: Testing Requirements
For each change:
- Unit test with known inputs/outputs
- Integration test with real (or realistic mock) candle data
- Verify no lookahead bias: model at time T only sees data <= T
- Run full test suite: `python -m pytest tests/ -q`
- All 892+ tests must pass

## Constraints
- Do NOT use synthetic/fake data for signal generation
- Do NOT hash timestamps to create model votes
- Every model vote must be derived from actual OHLCV data
- If no fresh data is available → emit NO_TRADE, never a signal
- All timestamps in UTC internally, display in IST
- Maintain backward compatibility with existing API contracts
```

---

## 7. IMMEDIATE ACTIONS YOU CAN TAKE NOW

### Quick Wins (Do Today)

1. **Install data providers:**
   ```bash
   cd "D:/trading Bots/FinalTrade/TradeSignalAI-v3"
   pip install tvDatafeed yfinance
   ```

2. **Fix Gemini model name** (one line):
   In `app/agents/providers/router.py` line 47, change:
   ```python
   kwargs["model"] = "openrouter/free"
   ```
   to:
   ```python
   kwargs["model"] = "openrouter/auto"  # or remove this line entirely
   ```

3. **Add `.env` to `.gitignore`:**
   ```bash
   echo ".env" >> .gitignore
   echo "*.db" >> .gitignore
   ```

4. **Rotate exposed API keys** (they're in git history)

### Medium Effort (This Week)

5. **Use MetaTrader5 for live data** (already installed!):
   ```python
   import MetaTrader5 as mt5
   mt5.initialize()
   tick = mt5.symbol_info_tick("EURUSD")
   print(tick.bid, tick.ask)  # REAL live price
   ```

6. **Build a candle refresh script** that runs every 5 minutes via Windows Task Scheduler

7. **Wire the dedup guard** into the coordinator (5 lines of code)

---

## 8. ARCHITECTURE DIAGRAM (Target State)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                    │
│                                                                     │
│  MetaTrader5 ──┐                                                    │
│  Binance WS ───┼──► Normalizer ──► Candle Store (SQLite)            │
│  TradingView ──┘        │              │                            │
│                         ▼              ▼                            │
│                   Ticker Cache    Feature Store                     │
│                   (< 60s old)     (point-in-time)                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MODEL LAYER                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Quant TA     │  │ Kronos       │  │ XGBoost/RF   │              │
│  │ (RSI,MACD,   │  │ (PyTorch     │  │ (Statistical │              │
│  │  EMA,ATR)    │  │  Transformer)│  │  ML)         │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                      │
│         ▼                  ▼                  ▼                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │           CONSENSUS ENGINE                       │                │
│  │  Weighted vote + Seasonality + Regime filter     │                │
│  └──────────────────────┬──────────────────────────┘                │
│                         │                                           │
│                         ▼                                           │
│  ┌─────────────────────────────────────────────────┐                │
│  │           ZERO-TRUST GATES                       │                │
│  │  • Data freshness < 15 min                      │                │
│  │  • Consensus >= 65%                             │                │
│  │  • Models contributing >= 3                     │                │
│  │  • RR >= 1.5                                    │                │
│  │  • No high-impact news in 30 min                │                │
│  │  • Not duplicate (identity hash)                │                │
│  │  • Cooldown elapsed (4h same direction)         │                │
│  └──────────────────────┬──────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SIGNAL OUTPUT                                 │
│                                                                     │
│  • Current signals (real-time)                                      │
│  • Signal change alerts ("EURUSD BUY→SELL")                         │
│  • Tomorrow schedule ("EURUSD BUY 10:00 IST")                       │
│  • Seasonality heatmap ("Best hour: 15:00, 68% win rate")           │
│  • Accuracy dashboard ("7-day hit rate: 62%")                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. SUMMARY: Why You're Not Getting Strong Signals

| # | Reason | Severity | Fix Effort |
|---|--------|----------|------------|
| 1 | No live data providers installed | CRITICAL | 5 minutes |
| 2 | Quant model is hash-based fake | CRITICAL | 2 hours |
| 3 | Kronos runs on 12-day-old data | HIGH | 1 hour |
| 4 | AI consensus falls back to heuristic | HIGH | 30 minutes |
| 5 | No signal deduplication | MEDIUM | 30 minutes |
| 6 | No time-of-day analysis | MEDIUM | 4 hours |
| 7 | No walk-forward validation gate | MEDIUM | 1 day |
| 8 | Timeframe mismatch (1h vs 1H) | LOW | 30 minutes |

**The #1 fix is installing data providers.** Without live data, nothing else matters. Every model in the world is useless if it's predicting on 2-week-old candles.

---

*Generated by Agnes (Hermes Agent) — TradeSignalAI-v3 Deep Analysis*
