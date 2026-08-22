"""
PHASE 16 — EXPERIMENT 1: SWING D1/W1 WALK-FORWARD VALIDATION
Zero-trust, zero-leakage expanding-window backtest for D1 and W1 timeframes.
Compares AI vs Buy&Hold, EMA crossover, RSI reversal, and Random baseline.
"""
import asyncio
import os
import sys
import json
import math
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# ─── Cost Model (matching Phase 16 H4 settings) ───────────────────────────────
SPREAD_PCT    = 0.001   # 0.10%
COMMISSION_PCT = 0.0002  # 0.02%
SLIPPAGE_PCT  = 0.0005  # 0.05%
TOTAL_COST    = SPREAD_PCT + COMMISSION_PCT + SLIPPAGE_PCT   # 0.17% round-trip

ASSETS = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]
TIMEFRAMES = ["1d", "1wk"]
HOLDING_DAYS = [1, 2, 3, 5, 7, 10]
MIN_TRAIN_BARS = 200   # minimum bars before first prediction

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation_outputs", "swing"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Data Loader ──────────────────────────────────────────────────────────────
async def load_data(symbol: str, timeframe: str, db_url: str) -> pd.DataFrame:
    engine = create_async_engine(db_url, echo=False)
    # map timeframe to DB key
    tf_map = {"1d": "1d", "1wk": "1wk", "D1": "1d", "W1": "1wk"}
    tf = tf_map.get(timeframe, timeframe)
    query = text("""
        SELECT timestamp, open, high, low, close, volume
        FROM historical_candles
        WHERE symbol = :s AND timeframe = :t
        ORDER BY timestamp ASC
    """)
    async with engine.connect() as conn:
        result = await conn.execute(query, {"s": symbol, "t": tf})
        rows = result.fetchall()
    await engine.dispose()

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


# ─── Technical Indicators ─────────────────────────────────────────────────────
def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close  = (df["low"]  - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


# ─── Metrics Calculator ───────────────────────────────────────────────────────
def compute_metrics(returns: pd.Series, annualisation_factor: float = 252.0) -> dict:
    if len(returns) < 2:
        return {}
    r = returns.dropna()
    total_trades = len(r)
    wins = (r > 0).sum()
    losses = (r < 0).sum()
    win_rate = wins / total_trades if total_trades > 0 else 0.0

    gross_profit = r[r > 0].sum()
    gross_loss   = abs(r[r < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    avg_win  = r[r > 0].mean() if wins > 0  else 0.0
    avg_loss = r[r < 0].mean() if losses > 0 else 0.0
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

    net_return = r.sum()

    mean_r = r.mean()
    std_r  = r.std()
    sharpe = (mean_r / std_r) * math.sqrt(annualisation_factor) if std_r > 0 else 0.0

    # Sortino: downside deviation
    downside = r[r < 0].std()
    sortino = (mean_r / downside) * math.sqrt(annualisation_factor) if downside > 0 else 0.0

    # Calmar
    cumulative = (1 + r).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_dd = drawdown.min()
    calmar = (net_return / abs(max_dd)) if max_dd < 0 else float("inf")

    # Max consecutive losses
    loss_streak = max_consecutive_losses(r)

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "expectancy": round(expectancy, 6),
        "net_return": round(net_return, 6),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "calmar": round(calmar, 4),
        "max_drawdown": round(max_dd, 6),
        "avg_win": round(avg_win, 6),
        "avg_loss": round(avg_loss, 6),
        "max_consecutive_losses": loss_streak,
    }

def max_consecutive_losses(r: pd.Series) -> int:
    max_streak = cur = 0
    for v in r:
        if v < 0:
            cur += 1
            max_streak = max(max_streak, cur)
        else:
            cur = 0
    return max_streak


# ─── AI Swing Signal ──────────────────────────────────────────────────────────
def ai_signal(history: pd.DataFrame) -> Optional[dict]:
    """
    Produces a signal using only history_slice (no future data).
    Uses EMA trend + RSI momentum + ATR sizing.
    This is the 'consensus' approximation for swing timeframes.
    """
    if len(history) < 50:
        return None

    close = history["close"]
    ema20 = compute_ema(close, 20).iloc[-1]
    ema50 = compute_ema(close, 50).iloc[-1]
    rsi   = compute_rsi(close).iloc[-1]
    atr   = compute_atr(history).iloc[-1]
    price = close.iloc[-1]

    # Feature vector similarity (cosine) — last 20 bars vs prior 20-bar windows
    feat_len = 20
    if len(history) >= feat_len * 2:
        def bar_vec(df_slice: pd.DataFrame) -> np.ndarray:
            c = df_slice["close"].values
            returns = np.diff(c) / c[:-1]
            return returns / (np.linalg.norm(returns) + 1e-9)

        curr_vec = bar_vec(history.iloc[-feat_len:])
        best_sim = -1.0
        best_future_ret = 0.0
        num_matches = 0
        historical_bull = 0
        for j in range(feat_len, len(history) - feat_len - 5):
            hist_vec = bar_vec(history.iloc[j - feat_len:j])
            sim = float(np.dot(curr_vec, hist_vec))
            if sim > 0.90:  # high similarity threshold
                fut_ret = (history["close"].iloc[j + 5] - history["close"].iloc[j]) / history["close"].iloc[j]
                if sim > best_sim:
                    best_sim = sim
                    best_future_ret = fut_ret
                if fut_ret > 0:
                    historical_bull += 1
                num_matches += 1

        hist_bias = historical_bull / num_matches if num_matches > 0 else 0.5
    else:
        hist_bias = 0.5
        best_sim = 0.0

    # Trend direction
    if ema20 > ema50 and rsi < 70:
        direction = "BUY"
        confidence = 55 + min(20, (ema20 / ema50 - 1) * 1000) + (hist_bias - 0.5) * 20
    elif ema20 < ema50 and rsi > 30:
        direction = "SELL"
        confidence = 55 + min(20, (1 - ema20 / ema50) * 1000) + (0.5 - hist_bias) * 20
    else:
        return None   # no signal

    if confidence < 55:
        return None

    stop_dist = atr * 1.5
    target_dist = atr * 2.5
    if direction == "BUY":
        stop   = price - stop_dist
        target = price + target_dist
    else:
        stop   = price + stop_dist
        target = price - target_dist

    rr = target_dist / stop_dist if stop_dist > 0 else 0.0

    return {
        "direction": direction,
        "confidence": round(float(confidence), 2),
        "entry": float(price),
        "stop": float(stop),
        "target": float(target),
        "rr": round(float(rr), 2),
        "expected_move_pct": round(float(target_dist / price * 100), 4),
        "similarity": round(float(best_sim), 4),
    }


# ─── Baseline Signals ─────────────────────────────────────────────────────────
def ema_signal(history: pd.DataFrame) -> Optional[str]:
    if len(history) < 50:
        return None
    close = history["close"]
    ema10 = compute_ema(close, 10).iloc[-1]
    ema30 = compute_ema(close, 30).iloc[-1]
    prev_ema10 = compute_ema(close, 10).iloc[-2]
    prev_ema30 = compute_ema(close, 30).iloc[-2]
    if prev_ema10 <= prev_ema30 and ema10 > ema30:
        return "BUY"
    if prev_ema10 >= prev_ema30 and ema10 < ema30:
        return "SELL"
    return None

def rsi_signal(history: pd.DataFrame) -> Optional[str]:
    if len(history) < 20:
        return None
    rsi_series = compute_rsi(history["close"])
    rsi = rsi_series.iloc[-1]
    if rsi < 30:
        return "BUY"
    if rsi > 70:
        return "SELL"
    return None


# ─── Walk-Forward Engine ──────────────────────────────────────────────────────
def run_walkforward(df: pd.DataFrame, asset: str, holding_days: int, tf_label: str) -> Optional[dict]:
    """Strict expanding-window walk-forward. No future data is ever available at prediction time."""
    if len(df) < MIN_TRAIN_BARS + holding_days + 5:
        return None

    ai_trades, ema_trades, rsi_trades, rnd_trades = [], [], [], []

    # MFE/MAE tracking
    mfe_list, mae_list = [], []

    for i in range(MIN_TRAIN_BARS, len(df) - holding_days):
        history = df.iloc[:i + 1].copy()
        current_price = float(history["close"].iloc[-1])
        current_time  = history.index[-1]

        # Actual future outcome — look-ahead ONLY for evaluation, never for signal generation
        future_slice = df.iloc[i + 1: i + 1 + holding_days]
        if len(future_slice) < holding_days:
            continue

        exit_price = float(future_slice["close"].iloc[-1])

        # ── AI Signal ──────────────────────────────────────────────────────────
        sig = ai_signal(history)
        if sig is not None:
            d = sig["direction"]
            if d == "BUY":
                raw_ret = (exit_price - current_price) / current_price
                mfe_val = (future_slice["high"].max() - current_price) / current_price
                mae_val = (future_slice["low"].min()  - current_price) / current_price
            else:
                raw_ret = (current_price - exit_price) / current_price
                mfe_val = (current_price - future_slice["low"].min())  / current_price
                mae_val = (current_price - future_slice["high"].max()) / current_price

            net_ret = raw_ret - TOTAL_COST
            mfe_list.append(mfe_val)
            mae_list.append(mae_val)

            ai_trades.append({
                "timestamp": current_time.isoformat(),
                "asset": asset, "timeframe": tf_label,
                "holding_days": holding_days,
                "direction": d,
                "confidence": sig["confidence"],
                "entry": current_price, "exit": exit_price,
                "stop": sig["stop"], "target": sig["target"],
                "rr": sig["rr"],
                "expected_move_pct": sig["expected_move_pct"],
                "actual_move_pct": round(raw_ret * 100, 4),
                "gross_return": round(raw_ret, 6),
                "net_return": round(net_ret, 6),
                "fees": round(TOTAL_COST, 6),
                "spread": SPREAD_PCT, "commission": COMMISSION_PCT, "slippage": SLIPPAGE_PCT,
                "mfe": round(mfe_val, 6), "mae": round(mae_val, 6),
                "win": net_ret > 0,
            })

        # ── EMA Baseline ───────────────────────────────────────────────────────
        esig = ema_signal(history)
        if esig is not None:
            if esig == "BUY":
                raw_ret = (exit_price - current_price) / current_price
            else:
                raw_ret = (current_price - exit_price) / current_price
            ema_trades.append({"net_return": raw_ret - TOTAL_COST, "win": (raw_ret - TOTAL_COST) > 0})

        # ── RSI Baseline ───────────────────────────────────────────────────────
        rsig = rsi_signal(history)
        if rsig is not None:
            if rsig == "BUY":
                raw_ret = (exit_price - current_price) / current_price
            else:
                raw_ret = (current_price - exit_price) / current_price
            rsi_trades.append({"net_return": raw_ret - TOTAL_COST, "win": (raw_ret - TOTAL_COST) > 0})

        # ── Random Baseline ────────────────────────────────────────────────────
        r_dir = random.choice(["BUY", "SELL"])
        if r_dir == "BUY":
            raw_ret = (exit_price - current_price) / current_price
        else:
            raw_ret = (current_price - exit_price) / current_price
        rnd_trades.append({"net_return": raw_ret - TOTAL_COST, "win": (raw_ret - TOTAL_COST) > 0})

    # ── Buy & Hold ─────────────────────────────────────────────────────────────
    bh_start = float(df["close"].iloc[MIN_TRAIN_BARS])
    bh_end   = float(df["close"].iloc[-1])
    bh_return = (bh_end - bh_start) / bh_start if bh_start > 0 else 0.0

    def metrics_from_list(trade_list: list) -> dict:
        if not trade_list:
            return {"total_trades": 0}
        r = pd.Series([t["net_return"] for t in trade_list])
        return compute_metrics(r, annualisation_factor=float(252 // max(holding_days, 1)))

    ai_metrics  = metrics_from_list(ai_trades)
    ema_metrics = metrics_from_list(ema_trades)
    rsi_metrics = metrics_from_list(rsi_trades)
    rnd_metrics = metrics_from_list(rnd_trades)

    ai_metrics["avg_mfe"] = round(float(np.mean(mfe_list)), 6) if mfe_list else 0.0
    ai_metrics["avg_mae"] = round(float(np.mean(mae_list)), 6) if mae_list else 0.0

    return {
        "asset": asset,
        "timeframe": tf_label,
        "holding_days": holding_days,
        "ai": ai_metrics,
        "ema_baseline": ema_metrics,
        "rsi_baseline": rsi_metrics,
        "random_baseline": rnd_metrics,
        "buy_and_hold_return": round(bh_return, 6),
        "ai_trades_raw": ai_trades,
    }


# ─── Main ──────────────────────────────────────────────────────────────────────
async def main():
    db_url = "sqlite+aiosqlite:///./trading_fallback.db"
    all_results = []

    for asset in ASSETS:
        for tf in TIMEFRAMES:
            print(f"\n[SWING] Loading {asset} {tf}...")
            df = await load_data(asset, tf, db_url)
            if df.empty:
                print(f"  [x] No data for {asset} {tf} - skipping")
                continue
            print(f"  [OK] {len(df)} bars loaded ({df.index[0].date()} to {df.index[-1].date()})")

            for hold in HOLDING_DAYS:
                print(f"  -> hold={hold}d...", end=" ")
                result = run_walkforward(df, asset, hold, tf)
                if result is None:
                    print("not enough data")
                    continue

                ai = result["ai"]
                total = ai.get("total_trades", 0)
                wr    = ai.get("win_rate", 0.0) * 100
                pf    = ai.get("profit_factor", 0.0)
                net   = ai.get("net_return", 0.0) * 100
                sh    = ai.get("sharpe", 0.0)
                dd    = ai.get("max_drawdown", 0.0) * 100
                bh    = result["buy_and_hold_return"] * 100
                print(f"trades={total:4d} | WR={wr:.1f}% | PF={pf:.2f} | Net={net:+.1f}% | Sharpe={sh:.2f} | DD={dd:.1f}% | B&H={bh:+.1f}%")

                # Save raw trades CSV
                if result["ai_trades_raw"]:
                    trades_df = pd.DataFrame(result["ai_trades_raw"])
                    csv_path = os.path.join(OUTPUT_DIR, f"{asset}_{tf}_hold{hold}d_trades.csv")
                    trades_df.to_csv(csv_path, index=False)

                # Strip raw trades for summary
                result_summary = {k: v for k, v in result.items() if k != "ai_trades_raw"}
                all_results.append(result_summary)

    # Save summary JSON
    summary_path = os.path.join(OUTPUT_DIR, "swing_summary.json")
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[DONE] Swing summary saved: {summary_path}")

    # Write sentinel
    with open(os.path.join(OUTPUT_DIR, "phase16_swing_engine.done"), "w") as f:
        f.write(datetime.utcnow().isoformat())


if __name__ == "__main__":
    asyncio.run(main())
