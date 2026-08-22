"""
PHASE 16 — EXPERIMENT 3: HISTORICAL MEMORY ABLATION
Tests three configurations on identical timestamps and costs:
  A: AI (consensus) WITHOUT FAISS historical memory
  B: Historical similarity (FAISS-style cosine) ONLY — no ML
  C: Full AI + Historical Memory
Answers: Does historical similarity actually improve prediction?
"""
import asyncio
import json
import math
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

SPREAD_PCT     = 0.001
COMMISSION_PCT = 0.0002
SLIPPAGE_PCT   = 0.0005
TOTAL_COST     = SPREAD_PCT + COMMISSION_PCT + SLIPPAGE_PCT

ASSETS    = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
TIMEFRAME = "4h"
MIN_TRAIN = 500
HOLD_BARS = 5

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation_outputs", "memory_ablation"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def load_data(symbol, tf, db_url):
    engine = create_async_engine(db_url, echo=False)
    q = text("SELECT timestamp, open, high, low, close, volume FROM historical_candles WHERE symbol=:s AND timeframe=:t ORDER BY timestamp ASC")
    async with engine.connect() as c:
        rows = (await c.execute(q, {"s": symbol, "t": tf})).fetchall()
    await engine.dispose()
    if not rows: return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["timestamp","open","high","low","close","volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df[~df.index.duplicated(keep="last")].sort_index()


def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def rsi_fn(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(span=n, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(span=n, adjust=False).mean()
    return 100 - 100/(1 + g/(l+1e-9))


def ai_consensus_no_memory(history: pd.DataFrame):
    """Pure ML consensus — no similarity lookup at all."""
    c = history["close"]
    if len(c) < 50: return None
    e10 = float(ema(c,10).iloc[-1]); e20 = float(ema(c,20).iloc[-1]); e50 = float(ema(c,50).iloc[-1])
    macd = float(ema(c,12).iloc[-1] - ema(c,26).iloc[-1])
    macd_s = float(ema(ema(c,12)-ema(c,26),9).iloc[-1])
    r = float(rsi_fn(c).iloc[-1])
    votes_buy = 0
    # XGBoost proxy
    if e10>e20>e50 and macd>macd_s and r<70: votes_buy+=1
    # RF proxy
    if e10>e50: votes_buy+=1
    if macd>0:  votes_buy+=1
    if r<55:    votes_buy+=1
    # HistGB proxy
    score = (1 if e20>e50 else -1) + (0.5 if macd>macd_s else -0.5) + (0.3 if r<50 else -0.3)
    if score > 0.8: votes_buy+=1
    total = 5
    if votes_buy >= 3: return "BUY"
    if votes_buy <= 2: return "SELL"
    return None


def faiss_similarity_only(history: pd.DataFrame):
    """Historical similarity ONLY — no ML model at all."""
    c = history["close"].values
    feat_len = 20
    if len(c) < feat_len*3: return None, 0.0
    def vec(s, e):
        r = np.diff(c[s:e]) / (c[s:e][:-1]+1e-9)
        n = np.linalg.norm(r)
        return r/n if n>0 else r
    curr = vec(len(c)-feat_len, len(c))
    bull, bear, count = 0, 0, 0
    for j in range(feat_len, len(c)-feat_len-5, 3):
        sim = float(np.dot(curr, vec(j-feat_len, j)))
        if sim > 0.92:
            fut = (c[j+5]-c[j])/(c[j]+1e-9)
            if fut > 0: bull += 1
            else:       bear += 1
            count += 1
    if count == 0: return None, 0.0
    bull_pct = bull/count
    if bull_pct > 0.6: return "BUY",  round(bull_pct, 4)
    if bull_pct < 0.4: return "SELL", round(1-bull_pct, 4)
    return None, 0.5


def ai_plus_memory(history: pd.DataFrame):
    """Full AI + historical memory with agreement gate."""
    base = ai_consensus_no_memory(history)
    mem_dir, mem_conf = faiss_similarity_only(history)
    if base is None: return None
    if mem_dir is None: return base    # memory neutral → trust AI
    if mem_dir == base: return base    # agreement
    return None                         # disagreement → abstain


def metrics(trade_list):
    if not trade_list: return {"total_trades": 0}
    r = pd.Series([t["net_return"] for t in trade_list])
    total = len(r)
    wins  = (r>0).sum()
    gp    = r[r>0].sum(); gl = abs(r[r<0].sum())
    pf    = gp/gl if gl>0 else float("inf")
    std   = r.std()
    sharpe = (r.mean()/std)*math.sqrt(252*6) if std>0 else 0.0
    cum = (1+r).cumprod(); peak = cum.cummax()
    max_dd = float(((cum-peak)/peak).min())
    avg_w = float(r[r>0].mean()) if wins>0 else 0.0
    avg_l = float(r[r<0].mean()) if (total-wins)>0 else 0.0
    wr = float(wins/total)
    return {
        "total_trades": total,
        "directional_accuracy": round(float(sum(t["win_raw_dir"] for t in trade_list)/total),4),
        "win_rate": round(wr,4),
        "profit_factor": round(pf,4),
        "sharpe": round(sharpe,4),
        "max_drawdown": round(max_dd,6),
        "expectancy": round(wr*avg_w + (1-wr)*avg_l, 6),
        "net_return": round(float(r.sum()),6),
    }


def run_asset(df, asset):
    res = {"A": [], "B": [], "C": []}

    for i in range(MIN_TRAIN, len(df)-HOLD_BARS):
        history = df.iloc[:i+1]
        price   = float(history["close"].iloc[-1])
        fut     = df.iloc[i+1: i+1+HOLD_BARS]
        if len(fut) < HOLD_BARS: continue
        exit_p  = float(fut["close"].iloc[-1])

        def make_trade(direction):
            if direction == "BUY":
                raw = (exit_p - price)/price
            else:
                raw = (price - exit_p)/price
            net = raw - TOTAL_COST
            actual_dir = "BUY" if exit_p > price else "SELL"
            return {"net_return": round(net,6), "win": net>0,
                    "win_raw_dir": 1 if direction==actual_dir else 0}

        # A: AI no memory
        d = ai_consensus_no_memory(history)
        if d: res["A"].append(make_trade(d))

        # B: Memory only
        d, _ = faiss_similarity_only(history)
        if d: res["B"].append(make_trade(d))

        # C: AI + memory
        d = ai_plus_memory(history)
        if d: res["C"].append(make_trade(d))

    return {
        "asset": asset,
        "A_AI_no_memory":    metrics(res["A"]),
        "B_memory_only":     metrics(res["B"]),
        "C_AI_plus_memory":  metrics(res["C"]),
    }


async def main():
    db_url = "sqlite+aiosqlite:///./trading_fallback.db"
    all_results = []

    for asset in ASSETS:
        print(f"\n[MEMORY ABLATION] {asset}")
        df = await load_data(asset, TIMEFRAME, db_url)
        if df.empty:
            print("  ✗ No data"); continue
        print(f"  ✓ {len(df)} bars")
        r = run_asset(df, asset)
        all_results.append(r)

        for cfg, m in [("A (AI no memory)", r["A_AI_no_memory"]),
                       ("B (Memory only) ", r["B_memory_only"]),
                       ("C (AI+Memory)   ", r["C_AI_plus_memory"])]:
            if m.get("total_trades",0) == 0:
                print(f"  {cfg}: no trades")
                continue
            print(f"  {cfg}: trades={m['total_trades']:4d} | "
                  f"DirAcc={m['directional_accuracy']*100:.1f}% | "
                  f"WR={m['win_rate']*100:.1f}% | "
                  f"PF={m['profit_factor']:.2f} | "
                  f"Sharpe={m['sharpe']:.2f} | "
                  f"DD={m['max_drawdown']*100:.1f}% | "
                  f"Net={m['net_return']*100:+.1f}%")

        # Verdict
        a_sh = r["A_AI_no_memory"].get("sharpe",0)
        c_sh = r["C_AI_plus_memory"].get("sharpe",0)
        if c_sh > a_sh:
            print(f"  ✓ MEMORY HELPS {asset}: Sharpe {a_sh:.3f} → {c_sh:.3f}")
        else:
            print(f"  ✗ MEMORY DOES NOT HELP {asset}: Sharpe {a_sh:.3f} → {c_sh:.3f}")
            print(f"    VERDICT: HISTORICAL MEMORY IS DESCRIPTIVE, NOT PREDICTIVE for {asset}")

    out_path = os.path.join(OUTPUT_DIR, "memory_ablation_summary.json")
    with open(out_path, "w") as f: json.dump(all_results, f, indent=2)
    df_out = pd.DataFrame([
        {"asset": r["asset"], "config": cfg, **m}
        for r in all_results
        for cfg, m in [("A_no_memory", r["A_AI_no_memory"]),
                       ("B_memory_only", r["B_memory_only"]),
                       ("C_ai_plus_memory", r["C_AI_plus_memory"])]
    ])
    df_out.to_csv(os.path.join(OUTPUT_DIR, "memory_ablation_summary.csv"), index=False)
    print(f"\n[DONE] Memory ablation saved: {out_path}")
    with open(os.path.join(OUTPUT_DIR, "phase16_memory_ablation.done"), "w") as f:
        f.write(datetime.utcnow().isoformat())

if __name__ == "__main__":
    asyncio.run(main())
