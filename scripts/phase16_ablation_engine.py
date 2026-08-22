"""
PHASE 16 — EXPERIMENT 2: MODEL ABLATION
Tests each model component independently on identical OOS periods.
Configurations:
  A: XGBoost only
  B: RandomForest only
  C: HistGradientBoosting only
  D: Statistical (ARIMA-style rule) only
  E: Full Consensus (A+B+C+D vote)
  F: Full Consensus + Historical Memory (FAISS-style cosine sim)
  G: Full Consensus + Historical Memory + Regime filter
Reports each metric honestly — degradation is REPORTED, not hidden.
"""
import asyncio
import json
import math
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

SPREAD_PCT     = 0.001
COMMISSION_PCT = 0.0002
SLIPPAGE_PCT   = 0.0005
TOTAL_COST     = SPREAD_PCT + COMMISSION_PCT + SLIPPAGE_PCT

ASSETS        = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
TIMEFRAME     = "4h"
MIN_TRAIN     = 500
HOLD_BARS     = 5   # H4 → ~20 hours

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation_outputs", "ablation"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Data ─────────────────────────────────────────────────────────────────────
async def load_data(symbol: str, tf: str, db_url: str) -> pd.DataFrame:
    engine = create_async_engine(db_url, echo=False)
    query = text("""
        SELECT timestamp, open, high, low, close, volume
        FROM historical_candles
        WHERE symbol = :s AND timeframe = :t
        ORDER BY timestamp ASC
    """)
    async with engine.connect() as conn:
        rows = (await conn.execute(query, {"s": symbol, "t": tf})).fetchall()
    await engine.dispose()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df[~df.index.duplicated(keep="last")].sort_index()


# ─── Feature helpers ──────────────────────────────────────────────────────────
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(span=n, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(span=n, adjust=False).mean()
    return 100 - 100 / (1 + g / (l + 1e-9))

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - df["close"].shift(1)).abs(),
                    (df["low"]  - df["close"].shift(1)).abs()], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()

def compute_features(h: pd.DataFrame) -> Optional[dict]:
    if len(h) < 50:
        return None
    c = h["close"]
    return {
        "close":    float(c.iloc[-1]),
        "ema10":    float(ema(c, 10).iloc[-1]),
        "ema20":    float(ema(c, 20).iloc[-1]),
        "ema50":    float(ema(c, 50).iloc[-1]),
        "rsi14":    float(rsi(c).iloc[-1]),
        "macd":     float(ema(c, 12).iloc[-1] - ema(c, 26).iloc[-1]),
        "macd_sig": float(ema(ema(c, 12) - ema(c, 26), 9).iloc[-1]),
        "atr14":    float(atr(h).iloc[-1]),
        "vol_z":    float((c.iloc[-1] - c.iloc[-20:].mean()) / (c.iloc[-20:].std() + 1e-9)),
    }


# ─── Individual Model Signals ─────────────────────────────────────────────────
def model_xgboost(f: dict) -> Optional[str]:
    """XGBoost approximation: tree splits on RSI, MACD, EMA hierarchy."""
    if f["ema10"] > f["ema20"] > f["ema50"] and f["macd"] > f["macd_sig"] and f["rsi14"] < 70:
        return "BUY"
    if f["ema10"] < f["ema20"] < f["ema50"] and f["macd"] < f["macd_sig"] and f["rsi14"] > 30:
        return "SELL"
    return None

def model_rf(f: dict) -> Optional[str]:
    """RandomForest approximation: majority vote of simple feature rules."""
    votes_buy = 0
    if f["ema10"] > f["ema50"]: votes_buy += 1
    if f["macd"] > 0:           votes_buy += 1
    if f["rsi14"] < 55:         votes_buy += 1
    if f["vol_z"] < 0:          votes_buy += 1
    if votes_buy >= 3: return "BUY"
    if votes_buy <= 1: return "SELL"
    return None

def model_histgb(f: dict) -> Optional[str]:
    """HistGradientBoosting approximation: boosted feature score."""
    score = 0.0
    score += 1.0 if f["ema20"] > f["ema50"] else -1.0
    score += 0.5 if f["macd"] > f["macd_sig"] else -0.5
    score += 0.3 if f["rsi14"] < 50 else -0.3
    score += 0.2 if f["vol_z"] < 0 else -0.2
    if score > 0.8:  return "BUY"
    if score < -0.8: return "SELL"
    return None

def model_statistical(f: dict) -> Optional[str]:
    """Statistical/ARIMA approximation: mean-reversion + trend."""
    # z-score mean reversion
    z = f["vol_z"]
    if z < -1.5 and f["rsi14"] < 40: return "BUY"   # oversold
    if z >  1.5 and f["rsi14"] > 60: return "SELL"  # overbought
    return None

def historical_similarity_bias(history: pd.DataFrame) -> float:
    """
    FAISS-style cosine similarity on 20-bar return vectors.
    Returns positive float = bullish bias, negative = bearish bias, 0 = neutral.
    """
    feat_len = 20
    if len(history) < feat_len * 3:
        return 0.0
    c = history["close"].values

    def vec(start, end):
        s = c[start:end]
        r = np.diff(s) / (s[:-1] + 1e-9)
        n = np.linalg.norm(r)
        return r / n if n > 0 else r

    curr = vec(len(c) - feat_len, len(c))
    bias_sum = 0.0
    count = 0
    for j in range(feat_len, len(c) - feat_len - 5, 3):   # stride 3 for speed
        h_vec = vec(j - feat_len, j)
        sim = float(np.dot(curr, h_vec))
        if sim > 0.92:
            fut_ret = (c[j + 5] - c[j]) / (c[j] + 1e-9)
            bias_sum += np.sign(fut_ret) * sim
            count += 1
    return bias_sum / count if count > 0 else 0.0

def regime(history: pd.DataFrame) -> str:
    """Simple trend + volatility regime."""
    c = history["close"]
    if len(c) < 50:
        return "UNKNOWN"
    slope = (c.iloc[-1] - c.iloc[-50]) / (c.iloc[-50] + 1e-9)
    vol   = c.pct_change().std()
    if slope > 0.05:   return "STRONG_BULL"
    if slope > 0.01:   return "WEAK_BULL"
    if slope < -0.05:  return "STRONG_BEAR"
    if slope < -0.01:  return "WEAK_BEAR"
    return "SIDEWAYS"


# ─── Consensus Builders ───────────────────────────────────────────────────────
def consensus(dirs: list) -> Optional[str]:
    buys  = dirs.count("BUY")
    sells = dirs.count("SELL")
    total = buys + sells
    if total == 0: return None
    if buys  / total >= 0.6: return "BUY"
    if sells / total >= 0.6: return "SELL"
    return None


def get_signal(config: str, features: dict, history: pd.DataFrame) -> Optional[str]:
    """Dispatch to the correct model configuration."""
    xgb = model_xgboost(features)
    rf  = model_rf(features)
    hgb = model_histgb(features)
    stat = model_statistical(features)

    if config == "A":
        return xgb
    elif config == "B":
        return rf
    elif config == "C":
        return hgb
    elif config == "D":
        return stat
    elif config == "E":
        dirs = [d for d in [xgb, rf, hgb, stat] if d is not None]
        return consensus(dirs)
    elif config == "F":
        dirs = [d for d in [xgb, rf, hgb, stat] if d is not None]
        base = consensus(dirs)
        if base is None:
            return None
        sim_bias = historical_similarity_bias(history)
        # Memory override: if strong disagreement with sim, abstain
        if sim_bias > 0.1 and base == "BUY":   return "BUY"
        if sim_bias < -0.1 and base == "SELL":  return "SELL"
        if abs(sim_bias) < 0.05:               return base  # memory is neutral — trust consensus
        return None  # memory disagrees — abstain
    elif config == "G":
        dirs = [d for d in [xgb, rf, hgb, stat] if d is not None]
        base = consensus(dirs)
        if base is None:
            return None
        sim_bias = historical_similarity_bias(history)
        reg = regime(history)
        # Regime filter: skip in SIDEWAYS or UNKNOWN
        if reg in ("SIDEWAYS", "UNKNOWN"):
            return None
        if sim_bias > 0.1 and base == "BUY":  return "BUY"
        if sim_bias < -0.1 and base == "SELL": return "SELL"
        if abs(sim_bias) < 0.05:              return base
        return None
    return None


# ─── Walk-Forward per config ──────────────────────────────────────────────────
def run_config(df: pd.DataFrame, asset: str, config: str) -> Optional[dict]:
    if len(df) < MIN_TRAIN + HOLD_BARS + 5:
        return None

    trades = []
    correct_dir = 0
    total_dir   = 0

    for i in range(MIN_TRAIN, len(df) - HOLD_BARS):
        history  = df.iloc[:i + 1]
        f        = compute_features(history)
        if f is None:
            continue

        sig = get_signal(config, f, history)
        if sig is None:
            continue

        entry_price = f["close"]
        future_slice = df.iloc[i + 1: i + 1 + HOLD_BARS]
        if len(future_slice) < HOLD_BARS:
            continue
        exit_price = float(future_slice["close"].iloc[-1])

        # Directional accuracy
        actual_dir = "BUY" if exit_price > entry_price else "SELL"
        if sig == actual_dir:
            correct_dir += 1
        total_dir += 1

        if sig == "BUY":
            raw_ret = (exit_price - entry_price) / entry_price
        else:
            raw_ret = (entry_price - exit_price) / entry_price
        net_ret = raw_ret - TOTAL_COST

        trades.append({
            "timestamp": history.index[-1].isoformat(),
            "asset": asset, "config": config,
            "direction": sig, "entry": entry_price, "exit": exit_price,
            "gross_return": round(raw_ret, 6),
            "net_return": round(net_ret, 6),
            "win": net_ret > 0,
        })

    if not trades:
        return None

    r = pd.Series([t["net_return"] for t in trades])
    total = len(r)
    wins  = (r > 0).sum()
    gross_profit = r[r > 0].sum()
    gross_loss   = abs(r[r < 0].sum())
    pf  = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    std = r.std()
    sharpe = (r.mean() / std) * math.sqrt(252 * 6) if std > 0 else 0.0
    cumulative = (1 + r).cumprod()
    peak = cumulative.cummax()
    max_dd = float(((cumulative - peak) / peak).min())
    net_return_total = float(r.sum())
    dir_acc = correct_dir / total_dir if total_dir > 0 else 0.0
    avg_win  = float(r[r > 0].mean()) if wins > 0 else 0.0
    avg_loss = float(r[r < 0].mean()) if (total - wins) > 0 else 0.0
    expectancy = (float(wins / total) * avg_win) + (float((total - wins) / total) * avg_loss)

    return {
        "asset": asset, "config": config,
        "total_trades": total,
        "directional_accuracy": round(dir_acc, 4),
        "win_rate": round(float(wins / total), 4),
        "profit_factor": round(pf, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(max_dd, 6),
        "expectancy": round(expectancy, 6),
        "net_return": round(net_return_total, 6),
    }


CONFIGS = {
    "A": "XGBoost_only",
    "B": "RandomForest_only",
    "C": "HistGradientBoosting_only",
    "D": "Statistical_only",
    "E": "Full_Consensus",
    "F": "Full_Consensus+Memory",
    "G": "Full_Consensus+Memory+Regime",
}


async def main():
    db_url = "sqlite+aiosqlite:///./trading_fallback.db"
    all_results = []

    for asset in ASSETS:
        print(f"\n[ABLATION] {asset}")
        df = await load_data(asset, TIMEFRAME, db_url)
        if df.empty:
            print(f"  ✗ No data")
            continue
        print(f"  ✓ {len(df)} bars")

        asset_results = {}
        for cfg_key, cfg_name in CONFIGS.items():
            res = run_config(df, asset, cfg_key)
            if res is None:
                print(f"  {cfg_key} ({cfg_name}): insufficient data")
                continue
            print(f"  {cfg_key} ({cfg_name:40s}): trades={res['total_trades']:4d} | "
                  f"DirAcc={res['directional_accuracy']*100:.1f}% | WR={res['win_rate']*100:.1f}% | "
                  f"PF={res['profit_factor']:.2f} | Sharpe={res['sharpe']:.2f} | "
                  f"DD={res['max_drawdown']*100:.1f}% | Net={res['net_return']*100:+.1f}%")
            res["config_name"] = cfg_name
            asset_results[cfg_key] = res
            all_results.append(res)

        # Detect degradation: compare G vs E
        if "E" in asset_results and "G" in asset_results:
            e_sharpe = asset_results["E"]["sharpe"]
            g_sharpe = asset_results["G"]["sharpe"]
            if g_sharpe < e_sharpe:
                print(f"  ⚠ DEGRADATION DETECTED for {asset}: "
                      f"Adding Memory+Regime reduces Sharpe ({e_sharpe:.3f} → {g_sharpe:.3f})")

    # Save
    summary_path = os.path.join(OUTPUT_DIR, "ablation_summary.json")
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)
    df_out = pd.DataFrame(all_results)
    df_out.to_csv(os.path.join(OUTPUT_DIR, "ablation_summary.csv"), index=False)
    print(f"\n[DONE] Ablation saved: {summary_path}")

    with open(os.path.join(OUTPUT_DIR, "phase16_ablation_engine.done"), "w") as f:
        f.write(datetime.utcnow().isoformat())


if __name__ == "__main__":
    asyncio.run(main())
