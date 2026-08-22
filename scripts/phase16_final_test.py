"""
PHASE 16 — EXPERIMENT 17: FINAL FROZEN OUT-OF-SAMPLE TEST
Model weights, parameters, thresholds, and historical memory are FROZEN.
Test period: most recent 3 months of data (NEVER touched in any prior experiment).
Run ONCE. No re-runs after seeing results.
This is the official final performance record.
"""
import asyncio
import json
import math
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

SPREAD_PCT     = 0.001
COMMISSION_PCT = 0.0002
SLIPPAGE_PCT   = 0.0005
TOTAL_COST     = SPREAD_PCT + COMMISSION_PCT + SLIPPAGE_PCT

# FINAL TEST PERIOD: last 90 calendar days (FROZEN — do not change)
FINAL_TEST_DAYS = 90
HOLD_BARS       = 5   # H4 → ~20 hours
MIN_TRAIN       = 500

ASSETS = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "SPX500"]

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation_outputs", "final_test"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sentinel: if this file already exists, refuse to re-run (integrity lock)
LOCK_FILE = os.path.join(OUTPUT_DIR, "FINAL_TEST_COMPLETED.lock")


async def load_data(symbol, tf, db_url):
    engine = create_async_engine(db_url, echo=False)
    q = text("SELECT timestamp,open,high,low,close,volume FROM historical_candles WHERE symbol=:s AND timeframe=:t ORDER BY timestamp ASC")
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
    d=s.diff(); g=d.clip(lower=0).ewm(span=n,adjust=False).mean(); l=(-d.clip(upper=0)).ewm(span=n,adjust=False).mean()
    return 100-100/(1+g/(l+1e-9))
def atr_fn(df, n=14):
    tr=pd.concat([df["high"]-df["low"],(df["high"]-df["close"].shift(1)).abs(),(df["low"]-df["close"].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(span=n,adjust=False).mean()

# ─── FROZEN SIGNAL FUNCTION (identical to ablation config E) ─────────────────
def frozen_signal(history: pd.DataFrame):
    """
    FROZEN parameters — these cannot change after the final test starts.
    Confidence threshold: 58 (chosen on validation set in Exp 13).
    """
    c = history["close"]
    if len(c) < 50: return None
    e10=float(ema(c,10).iloc[-1]); e20=float(ema(c,20).iloc[-1]); e50=float(ema(c,50).iloc[-1])
    macd=float(ema(c,12).iloc[-1]-ema(c,26).iloc[-1])
    macd_s=float(ema(ema(c,12)-ema(c,26),9).iloc[-1])
    r=float(rsi_fn(c).iloc[-1])
    atr_val=float(atr_fn(history).iloc[-1])
    price=float(c.iloc[-1])
    vb=0
    if e10>e20>e50 and macd>macd_s and r<70: vb+=2
    if e10>e50: vb+=1
    if macd>0:  vb+=1
    if r<55:    vb+=1
    vs=0
    if e10<e20<e50 and macd<macd_s and r>30: vs+=2
    if e10<e50: vs+=1
    if macd<0:  vs+=1
    if r>45:    vs+=1
    if vb>=3 and vb>vs:
        direction="BUY"; conf=55+min(25,(vb-3)*5)+min(10,abs(macd/price)*1000)
    elif vs>=3 and vs>vb:
        direction="SELL"; conf=55+min(25,(vs-3)*5)+min(10,abs(macd/price)*1000)
    else: return None
    # FROZEN confidence threshold from validation set optimisation
    if conf < 58: return None
    stop_d=atr_val*1.5; tgt_d=atr_val*2.5
    return {"direction":direction, "confidence":round(float(conf),1),
            "price":price, "stop":price-stop_d if direction=="BUY" else price+stop_d,
            "target":price+tgt_d if direction=="BUY" else price-tgt_d,
            "rr":round(tgt_d/stop_d if stop_d>0 else 0,2)}


def compute_metrics(trades_df: pd.DataFrame, annualisation: float = 252*6) -> dict:
    r = trades_df["net_return"]
    if len(r) < 2: return {"total_trades": len(r), "note": "insufficient trades"}
    wins=(r>0).sum(); n=len(r)
    gp=r[r>0].sum(); gl=abs(r[r<0].sum()); pf=gp/gl if gl>0 else float("inf")
    std=r.std(); sharpe=(r.mean()/std)*math.sqrt(annualisation) if std>0 else 0.0
    downside=r[r<0].std(); sortino=(r.mean()/downside)*math.sqrt(annualisation) if downside>0 else 0.0
    cum=(1+r).cumprod(); pk=cum.cummax(); dd_series=(cum-pk)/pk
    max_dd=float(dd_series.min())
    net_total=float(r.sum())
    calmar=net_total/abs(max_dd) if max_dd<0 else float("inf")
    avg_w=float(r[r>0].mean()) if wins>0 else 0.0
    avg_l=float(r[r<0].mean()) if (n-wins)>0 else 0.0
    wr=float(wins/n)
    # Max consecutive losses
    streak=cur=0
    for v in r:
        cur = cur+1 if v<0 else 0
        streak=max(streak,cur)
    return {"total_trades":n, "win_rate":round(wr,4), "profit_factor":round(pf,4),
            "expectancy":round(wr*avg_w+(1-wr)*avg_l,6),
            "net_return":round(net_total,6), "sharpe":round(sharpe,4),
            "sortino":round(sortino,4), "calmar":round(calmar,4),
            "max_drawdown":round(max_dd,6), "avg_win":round(avg_w,6),
            "avg_loss":round(avg_l,6), "max_consecutive_losses":streak,
            "avg_mfe":round(float(trades_df["mfe"].mean()),6),
            "avg_mae":round(float(trades_df["mae"].mean()),6)}


async def main():
    print("="*60)
    print("PHASE 16 — EXP 17: FINAL FROZEN OUT-OF-SAMPLE TEST")
    print("="*60)

    # Integrity lock: refuse re-runs
    if os.path.exists(LOCK_FILE):
        print(f"\n[LOCKED] Final test has already been run. Results are immutable.")
        print(f"  Lock file: {LOCK_FILE}")
        print("  To intentionally re-run, delete the lock file manually.")
        return

    db_url = "sqlite+aiosqlite:///./trading_fallback.db"
    all_results = []
    all_trades  = []

    for asset in ASSETS:
        df = await load_data(asset, "4h", db_url)
        if df.empty:
            print(f"  {asset}: no data — skipping")
            continue

        # Split: training history = everything before final 90 days
        cutoff = df.index[-1] - timedelta(days=FINAL_TEST_DAYS)
        train  = df[df.index <= cutoff]
        test   = df[df.index > cutoff]

        if len(train) < MIN_TRAIN or len(test) < HOLD_BARS + 5:
            print(f"  {asset}: insufficient split (train={len(train)}, test={len(test)}) — skipping")
            continue

        print(f"\n  {asset}: train={len(train)} bars, test={len(test)} bars "
              f"({test.index[0].date()} → {test.index[-1].date()})")

        trades = []
        # Buy & Hold baseline on test set
        bh_start = float(test["close"].iloc[0])
        bh_end   = float(test["close"].iloc[-1])
        bh_return = (bh_end - bh_start) / bh_start

        for i in range(len(test) - HOLD_BARS):
            # History = all training data + test data up to and including current bar
            history = pd.concat([train, test.iloc[:i+1]])
            sig = frozen_signal(history)
            if sig is None: continue

            price  = sig["price"]
            fut    = test.iloc[i+1: i+1+HOLD_BARS]
            if len(fut) < HOLD_BARS: continue
            exit_p = float(fut["close"].iloc[-1])

            if sig["direction"]=="BUY":
                raw=(exit_p-price)/price
                mfe=(fut["high"].max()-price)/price
                mae=(fut["low"].min()-price)/price
            else:
                raw=(price-exit_p)/price
                mfe=(price-fut["low"].min())/price
                mae=(price-fut["high"].max())/price
            net = raw - TOTAL_COST

            trade = {"asset":asset,"timestamp":test.index[i].isoformat(),
                     "direction":sig["direction"],"confidence":sig["confidence"],
                     "entry":price,"exit":exit_p,"stop":sig["stop"],"target":sig["target"],
                     "rr":sig["rr"],"gross_return":round(raw,6),"net_return":round(net,6),
                     "mfe":round(mfe,6),"mae":round(mae,6),"win":net>0}
            trades.append(trade)
            all_trades.append(trade)

        if not trades:
            print(f"    No trades generated")
            continue

        tdf = pd.DataFrame(trades)
        m = compute_metrics(tdf)
        m["asset"]          = asset
        m["test_start"]     = test.index[0].date().isoformat()
        m["test_end"]       = test.index[-1].date().isoformat()
        m["buy_hold_return"]= round(bh_return,6)
        m["beats_bh"]       = m["net_return"] > bh_return
        all_results.append(m)

        print(f"    trades={m['total_trades']} | WR={m['win_rate']*100:.1f}% | "
              f"PF={m['profit_factor']:.2f} | Sharpe={m['sharpe']:.2f} | "
              f"DD={m['max_drawdown']*100:.1f}% | Net={m['net_return']*100:+.1f}% | "
              f"B&H={bh_return*100:+.1f}%")

    # ── Aggregate final summary ────────────────────────────────────────────────
    if all_trades:
        all_df = pd.DataFrame(all_trades)
        agg = compute_metrics(all_df)
        agg["note"] = "AGGREGATE ACROSS ALL ASSETS"
    else:
        agg = {"note": "NO TRADES GENERATED"}

    print(f"\n  AGGREGATE: trades={agg.get('total_trades','?')} | "
          f"WR={agg.get('win_rate',0)*100:.1f}% | "
          f"Sharpe={agg.get('sharpe',0):.2f} | "
          f"Net={agg.get('net_return',0)*100:+.1f}%")

    # Determine readiness — default NO
    any_passes = any(
        r.get("sharpe", 0) > 0.5 and
        r.get("profit_factor", 0) > 1.1 and
        r.get("win_rate", 0) > 0.50
        for r in all_results
    )
    agg_sharpe = agg.get("sharpe", 0)
    ready_for_paper = agg_sharpe > 0.3 and agg.get("profit_factor",0) > 1.05
    ready_for_real  = False  # ALWAYS FALSE by default (Zero-Trust Rule)

    final_verdict = {
        "generated_at":       datetime.utcnow().isoformat(),
        "test_period_days":   FINAL_TEST_DAYS,
        "assets_tested":      len(all_results),
        "aggregate_metrics":  agg,
        "per_asset_metrics":  all_results,
        "ready_for_paper_trading": ready_for_paper,
        "ready_for_real_money":    ready_for_real,
        "real_money_verdict": "NO — requires additional validation and live paper trading first.",
        "notes": [
            "Model parameters FROZEN before this test.",
            "Thresholds NOT optimized on this test period.",
            "Historical memory FROZEN (no updates during test).",
            "This test was run ONCE and results are immutable.",
        ]
    }

    # Save
    pd.DataFrame(all_trades).to_csv(os.path.join(OUTPUT_DIR,"final_test_trades.csv"), index=False)
    with open(os.path.join(OUTPUT_DIR,"final_test_verdict.json"),"w") as f:
        json.dump(final_verdict, f, indent=2)

    print(f"\n  READY FOR PAPER TRADING: {'YES' if ready_for_paper else 'NO'}")
    print(f"  READY FOR REAL MONEY:    NO (Zero-Trust Default)")
    print(f"\n[DONE] Final test results saved to {OUTPUT_DIR}")

    # Write integrity lock
    with open(LOCK_FILE, "w") as f:
        f.write(f"Final test completed at {datetime.utcnow().isoformat()}\n")
        f.write("DO NOT DELETE unless intentionally re-running the final test.\n")

    with open(os.path.join(OUTPUT_DIR,"phase16_final_test.done"),"w") as f:
        f.write(datetime.utcnow().isoformat())


if __name__ == "__main__":
    asyncio.run(main())
