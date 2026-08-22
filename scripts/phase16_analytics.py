"""
PHASE 16 — EXPERIMENTS 4-13: Combined Analytics Script
Runs:
  4.  Confidence Calibration (Brier, ECE, calibration curve)
  5.  Random Baseline (Monte Carlo, 10k runs)
  6.  Self-Learning Validation (baseline vs learning-enabled)
  7.  Day-of-Week Analysis (H4 + D1)
  8.  Time-of-Day Analysis (H4)
  9.  Market Session Analysis
  10. Friday→Monday Gap Analysis
  11. Multi-Asset Summary (ranking table)
  12. Regime Analysis
  13. H4 Signal Quality Thresholds (validation set only)

All experiments use only past data at each prediction point.
"""
import asyncio
import json
import math
import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# ─── Cost Model ───────────────────────────────────────────────────────────────
SPREAD_PCT     = 0.001
COMMISSION_PCT = 0.0002
SLIPPAGE_PCT   = 0.0005
TOTAL_COST     = SPREAD_PCT + COMMISSION_PCT + SLIPPAGE_PCT

ASSETS    = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "SPX500"]
CRYPTO    = {"BTCUSD", "ETHUSD"}
FOREX     = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD"}
INDICES   = {"NAS100", "SPX500"}
GOLD      = {"XAUUSD"}
MIN_TRAIN = 500
HOLD_BARS = 5
IST_OFFSET = timedelta(hours=5, minutes=30)

OUTPUT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "validation_outputs"))
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# ─── DB ───────────────────────────────────────────────────────────────────────
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

# ─── Indicators ───────────────────────────────────────────────────────────────
def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def rsi_fn(s, n=14):
    d=s.diff(); g=d.clip(lower=0).ewm(span=n,adjust=False).mean(); l=(-d.clip(upper=0)).ewm(span=n,adjust=False).mean()
    return 100-100/(1+g/(l+1e-9))
def atr_fn(df, n=14):
    tr=pd.concat([df["high"]-df["low"],(df["high"]-df["close"].shift(1)).abs(),(df["low"]-df["close"].shift(1)).abs()],axis=1).max(axis=1)
    return tr.ewm(span=n,adjust=False).mean()

# ─── Core signal (same as ablation config E full consensus) ───────────────────
def ai_signal(history: pd.DataFrame) -> Optional[dict]:
    c = history["close"]
    if len(c) < 50: return None
    e10=float(ema(c,10).iloc[-1]); e20=float(ema(c,20).iloc[-1]); e50=float(ema(c,50).iloc[-1])
    macd=float(ema(c,12).iloc[-1]-ema(c,26).iloc[-1])
    macd_s=float(ema(ema(c,12)-ema(c,26),9).iloc[-1])
    r=float(rsi_fn(c).iloc[-1])
    atr_val=float(atr_fn(history).iloc[-1])
    price=float(c.iloc[-1])
    # votes
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
        direction="BUY"
        conf=55+min(25, (vb-3)*5) + min(10, abs(macd/price)*1000)
    elif vs>=3 and vs>vb:
        direction="SELL"
        conf=55+min(25, (vs-3)*5) + min(10, abs(macd/price)*1000)
    else:
        return None
    stop_d=atr_val*1.5; tgt_d=atr_val*2.5
    rr=tgt_d/stop_d if stop_d>0 else 0.0
    return {"direction": direction, "confidence": round(float(conf),1), "price": price,
            "rr": round(rr,2), "atr": atr_val}

def regime_fn(history: pd.DataFrame) -> str:
    c = history["close"]
    if len(c)<50: return "UNKNOWN"
    vol = c.pct_change().std()
    slope = (c.iloc[-1]-c.iloc[-50])/(c.iloc[-50]+1e-9)
    vol_level = "HIGH" if vol > c.pct_change().rolling(200).std().mean()*1.5 else ("LOW" if vol < c.pct_change().rolling(200).std().mean()*0.5 else "NORMAL")
    if slope>0.05:   trend="STRONG_BULL"
    elif slope>0.01: trend="WEAK_BULL"
    elif slope<-0.05:trend="STRONG_BEAR"
    elif slope<-0.01:trend="WEAK_BEAR"
    else:            trend="SIDEWAYS"
    return f"{trend}|{vol_level}"

def session_fn(ts: pd.Timestamp) -> str:
    h = ts.hour
    if 0 <= h < 8:    return "Asian"
    if 8 <= h < 12:   return "London"
    if 12 <= h < 16:  return "LondonNY_Overlap"
    if 16 <= h < 21:  return "NewYork"
    return "Asian"


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE ALL H4 PREDICTIONS (shared across experiments 4-13)
# ═══════════════════════════════════════════════════════════════════════════════
async def generate_h4_predictions(db_url: str) -> pd.DataFrame:
    """Generate all H4 predictions for all assets in one pass."""
    all_preds = []
    for asset in ASSETS:
        df = await load_data(asset, "4h", db_url)
        if df.empty: continue
        print(f"  Generating H4 predictions for {asset} ({len(df)} bars)...")
        for i in range(MIN_TRAIN, len(df)-HOLD_BARS):
            history = df.iloc[:i+1]
            sig = ai_signal(history)
            if sig is None: continue
            price = sig["price"]
            fut   = df.iloc[i+1: i+1+HOLD_BARS]
            if len(fut)<HOLD_BARS: continue
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
            ts  = history.index[-1]
            ist = ts + IST_OFFSET
            all_preds.append({
                "asset":     asset,
                "timestamp": ts,
                "ist":       ist,
                "weekday":   ts.weekday(),   # 0=Mon
                "hour_utc":  ts.hour,
                "hour_ist":  ist.hour,
                "session":   session_fn(ts),
                "direction": sig["direction"],
                "confidence":sig["confidence"],
                "entry":     price,
                "exit":      exit_p,
                "rr":        sig["rr"],
                "gross_return": round(raw,6),
                "net_return":   round(net,6),
                "mfe":          round(mfe,6),
                "mae":          round(mae,6),
                "win":          net>0,
                "win_int":      1 if net>0 else 0,
                "regime":       regime_fn(history),
            })
    return pd.DataFrame(all_preds)


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 4: CONFIDENCE CALIBRATION
# ═══════════════════════════════════════════════════════════════════════════════
def exp4_confidence_calibration(preds: pd.DataFrame) -> dict:
    print("\n[EXP 4] Confidence Calibration")
    buckets = [(50,55),(55,60),(60,65),(65,70),(70,75),(75,80),(80,85),(85,90),(90,101)]
    rows = []
    brier_sum = 0.0
    ece_sum   = 0.0
    n_total   = len(preds)

    for lo, hi in buckets:
        sub = preds[(preds["confidence"]>=lo) & (preds["confidence"]<hi)]
        n   = len(sub)
        if n == 0: continue
        pred_conf = sub["confidence"].mean() / 100.0
        act_wr    = sub["win_int"].mean()
        avg_ret   = sub["net_return"].mean()
        gp = sub[sub["net_return"]>0]["net_return"].sum()
        gl = abs(sub[sub["net_return"]<0]["net_return"].sum())
        pf = gp/gl if gl>0 else float("inf")
        brier_sum += n * (pred_conf - act_wr)**2
        ece_sum   += n * abs(pred_conf - act_wr)
        row = {"bucket": f"{lo}-{hi}", "count": n, "pred_conf_pct": round(pred_conf*100,2),
               "actual_win_rate_pct": round(act_wr*100,2),
               "avg_net_return_pct": round(avg_ret*100,4), "profit_factor": round(pf,3)}
        rows.append(row)
        print(f"  Conf {lo}-{hi:3d}% | n={n:5d} | Pred={pred_conf*100:.0f}% | Actual WR={act_wr*100:.1f}% | PF={pf:.2f}")

    brier_score = brier_sum / n_total if n_total > 0 else 0.0
    ece         = ece_sum / n_total if n_total > 0 else 0.0
    calibrated  = ece < 0.05

    print(f"  Brier Score: {brier_score:.4f}")
    print(f"  ECE:         {ece:.4f}")
    print(f"  CALIBRATED:  {'YES' if calibrated else 'NO — confidence is NOT a reliable probability estimate'}")

    os.makedirs(os.path.join(OUTPUT_ROOT,"calibration"), exist_ok=True)
    df_out = pd.DataFrame(rows)
    df_out.to_csv(os.path.join(OUTPUT_ROOT,"calibration","calibration_buckets.csv"), index=False)
    summary = {"brier_score": round(brier_score,6), "ece": round(ece,6), "calibrated": calibrated,
               "buckets": rows}
    with open(os.path.join(OUTPUT_ROOT,"calibration","calibration_summary.json"),"w") as f:
        json.dump(summary, f, indent=2)
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 5: RANDOM BASELINE (Monte Carlo)
# ═══════════════════════════════════════════════════════════════════════════════
def exp5_random_baseline(preds: pd.DataFrame, n_trials: int = 10000) -> dict:
    print(f"\n[EXP 5] Random Baseline ({n_trials:,} Monte Carlo trials)")
    os.makedirs(os.path.join(OUTPUT_ROOT,"random_baseline"), exist_ok=True)
    results = {}

    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset].copy()
        n   = len(sub)
        if n < 10: continue
        actual_net = float(sub["net_return"].sum())

        # Monte Carlo: randomly flip directions
        mc_returns = []
        for _ in range(n_trials):
            flips = np.random.choice([-1,1], size=n)  # randomly invert returns
            r = sub["gross_return"].values * flips - TOTAL_COST
            mc_returns.append(r.sum())
        mc_arr = np.array(mc_returns)
        mc_mean = float(mc_arr.mean())
        mc_std  = float(mc_arr.std())
        mc_sharpe = float(np.mean([r/(np.std(np.diff(np.cumsum(np.random.choice(sub["gross_return"].values*np.random.choice([-1,1],n)-TOTAL_COST, n))))+1e-9) for _ in range(100)]))
        ai_percentile = float((mc_arr < actual_net).mean() * 100)
        beats_random  = actual_net > mc_mean

        results[asset] = {"n_trades": n, "ai_net_return": round(actual_net,6),
                          "random_mean": round(mc_mean,6), "random_std": round(mc_std,6),
                          "ai_percentile_vs_random": round(ai_percentile,1),
                          "beats_random": beats_random}
        verdict = "✓ BEATS RANDOM" if beats_random else "✗ DOES NOT BEAT RANDOM"
        print(f"  {asset:8s}: AI={actual_net*100:+.1f}% | RandMean={mc_mean*100:+.1f}% | "
              f"AI@{ai_percentile:.0f}th pct | {verdict}")

    with open(os.path.join(OUTPUT_ROOT,"random_baseline","random_baseline_summary.json"),"w") as f:
        json.dump(results, f, indent=2)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 6: SELF-LEARNING VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
def exp6_self_learning(preds: pd.DataFrame) -> dict:
    """
    Split OOS predictions in half.
    Phase A: first half (baseline — no learning).
    Phase B: second half (simulate learning: re-weight signals based on Phase A outcomes).
    Compare metrics.
    """
    print("\n[EXP 6] Self-Learning Validation")
    os.makedirs(os.path.join(OUTPUT_ROOT,"self_learning"), exist_ok=True)
    results = {}

    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset].sort_values("timestamp").copy()
        n = len(sub)
        if n < 50: continue
        mid = n // 2
        phA = sub.iloc[:mid]
        phB = sub.iloc[mid:]

        def m(df):
            r = df["net_return"]
            if len(r)<2: return {}
            wins = (r>0).mean()
            std  = r.std()
            sharpe = (r.mean()/std)*math.sqrt(252*6) if std>0 else 0.0
            cum = (1+r).cumprod(); pk=cum.cummax()
            return {"n":len(r), "win_rate":round(wins,4), "net_return":round(float(r.sum()),6),
                    "sharpe":round(sharpe,4), "max_drawdown":round(float(((cum-pk)/pk).min()),6),
                    "expectancy":round(float(r.mean()),6)}

        # Simulate learning: use Phase A win rate to weight Phase B confidence threshold
        a_wr = phA["win_int"].mean()
        # if Phase A WR < 50%, "learning" raises the threshold — filter Phase B to conf > 62 instead of 55
        if a_wr < 0.50:
            phB_learned = phB[phB["confidence"] >= 62]
        else:
            phB_learned = phB  # no change needed

        mA  = m(phA)
        mB_base    = m(phB)           # second half without learning
        mB_learned = m(phB_learned)   # second half with learning

        # Directional accuracy
        def dir_acc(df):
            return round(float(df["win_int"].mean()),4) if len(df)>0 else 0.0

        results[asset] = {
            "phase_A_baseline": {**mA, "dir_acc": dir_acc(phA)},
            "phase_B_no_learning": {**mB_base, "dir_acc": dir_acc(phB)},
            "phase_B_with_learning": {**mB_learned, "dir_acc": dir_acc(phB_learned)},
        }

        sh_base    = mB_base.get("sharpe",0)
        sh_learned = mB_learned.get("sharpe",0)
        if sh_learned > sh_base:
            verdict = "SELF-LEARNING IMPROVES PERFORMANCE"
        elif sh_learned < sh_base:
            verdict = "SELF-LEARNING CURRENTLY DEGRADES OUT-OF-SAMPLE PERFORMANCE"
        else:
            verdict = "SELF-LEARNING HAS NO MEASURABLE EFFECT"
        results[asset]["verdict"] = verdict
        print(f"  {asset:8s}: PhaseA Sharpe={mA.get('sharpe',0):.3f} | "
              f"PhaseB-base={sh_base:.3f} | PhaseB-learned={sh_learned:.3f} | {verdict}")

    with open(os.path.join(OUTPUT_ROOT,"self_learning","self_learning_summary.json"),"w") as f:
        json.dump(results, f, indent=2)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 7: DAY-OF-WEEK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
DAY_NAMES = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}

def exp7_dayofweek(preds: pd.DataFrame) -> dict:
    print("\n[EXP 7] Day-of-Week Analysis")
    os.makedirs(os.path.join(OUTPUT_ROOT,"dayofweek"), exist_ok=True)
    results = {}
    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset]
        asset_rows = []
        for day in range(7):
            d = sub[sub["weekday"]==day]
            n = len(d)
            if n < 5: continue
            buy_pct  = float((d["direction"]=="BUY").mean()*100)
            sell_pct = float((d["direction"]=="SELL").mean()*100)
            wr       = float(d["win_int"].mean()*100)
            avg_ret  = float(d["net_return"].mean()*100)
            avg_move = float(d["gross_return"].abs().mean()*100)
            asset_rows.append({"asset":asset,"day":DAY_NAMES[day],"n":n,
                                "buy_pct":round(buy_pct,1),"sell_pct":round(sell_pct,1),
                                "win_rate_pct":round(wr,1),"avg_return_pct":round(avg_ret,4),
                                "avg_move_pct":round(avg_move,4)})
        results[asset] = asset_rows
    df_out = pd.DataFrame([row for rows in results.values() for row in rows])
    df_out.to_csv(os.path.join(OUTPUT_ROOT,"dayofweek","dayofweek_analysis.csv"), index=False)
    print(f"  Saved {len(df_out)} rows")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 8: TIME-OF-DAY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def exp8_timeofday(preds: pd.DataFrame) -> dict:
    print("\n[EXP 8] Time-of-Day Analysis (H4 IST)")
    os.makedirs(os.path.join(OUTPUT_ROOT,"timeofday"), exist_ok=True)
    # H4 windows in IST: 00, 04, 08, 12, 16, 20
    windows = [0, 4, 8, 12, 16, 20]
    results = {}
    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset]
        rows = []
        for h in windows:
            d = sub[sub["hour_ist"]==h]
            n = len(d)
            if n < 3:
                rows.append({"asset":asset,"ist_hour":h,"n":n,"note":"INSUFFICIENT SAMPLE"})
                continue
            rows.append({"asset":asset,"ist_hour":h,"n":n,
                         "buy_pct":round(float((d["direction"]=="BUY").mean()*100),1),
                         "sell_pct":round(float((d["direction"]=="SELL").mean()*100),1),
                         "win_rate_pct":round(float(d["win_int"].mean()*100),1),
                         "avg_move_pct":round(float(d["gross_return"].abs().mean()*100),4),
                         "avg_hold_bars":HOLD_BARS})
        results[asset] = rows
    df_out = pd.DataFrame([r for rows in results.values() for r in rows])
    df_out.to_csv(os.path.join(OUTPUT_ROOT,"timeofday","timeofday_analysis.csv"), index=False)
    print(f"  Saved {len(df_out)} rows")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 9: MARKET SESSION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def exp9_sessions(preds: pd.DataFrame) -> dict:
    print("\n[EXP 9] Market Session Analysis")
    os.makedirs(os.path.join(OUTPUT_ROOT,"sessions"), exist_ok=True)
    rows = []
    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset]
        for sess in ["Asian","London","LondonNY_Overlap","NewYork"]:
            d = sub[sub["session"]==sess]
            n = len(d)
            if n < 5: continue
            r_series = d["net_return"]
            gp=r_series[r_series>0].sum(); gl=abs(r_series[r_series<0].sum())
            pf=gp/gl if gl>0 else float("inf")
            std=r_series.std()
            sharpe=(r_series.mean()/std)*math.sqrt(252*6) if std>0 else 0.0
            cum=(1+r_series).cumprod(); pk=cum.cummax()
            dd=float(((cum-pk)/pk).min())
            rows.append({"asset":asset,"session":sess,"n":n,
                         "win_rate_pct":round(float(d["win_int"].mean()*100),1),
                         "net_return_pct":round(float(r_series.sum()*100),4),
                         "profit_factor":round(pf,3),
                         "sharpe":round(sharpe,4),
                         "avg_move_pct":round(float(d["gross_return"].abs().mean()*100),4),
                         "max_drawdown_pct":round(dd*100,4)})
            print(f"  {asset:8s} | {sess:20s} | n={n:4d} | WR={d['win_int'].mean()*100:.1f}% | PF={pf:.2f} | Sharpe={sharpe:.2f}")
    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_ROOT,"sessions","session_analysis.csv"), index=False)
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 10: FRIDAY → MONDAY GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
async def exp10_weekend_gaps(db_url: str) -> dict:
    print("\n[EXP 10] Friday→Monday Gap Analysis")
    os.makedirs(os.path.join(OUTPUT_ROOT,"weekend_gaps"), exist_ok=True)
    results = {}
    TF_MAP = {"BTCUSD":"1d","ETHUSD":"1d","EURUSD":"1d","GBPUSD":"1d",
              "USDJPY":"1d","AUDUSD":"1d","XAUUSD":"1d","SPX500":"1d"}
    for asset, tf in TF_MAP.items():
        df = await load_data(asset, tf, db_url)
        if df.empty: continue
        gaps = []
        for i in range(1, len(df)):
            ts_prev = df.index[i-1]; ts_curr = df.index[i]
            # Friday close → Monday open
            if ts_prev.weekday() == 4 and ts_curr.weekday() == 0:
                fri_close = float(df["close"].iloc[i-1])
                mon_open  = float(df["open"].iloc[i])
                mon_close = float(df["close"].iloc[i])
                gap_size  = (mon_open - fri_close) / fri_close
                gap_dir   = "UP" if gap_size > 0 else "DOWN"
                mon_move  = (mon_close - mon_open) / mon_open
                # gap fill: did price touch fri_close during Monday?
                mon_low   = float(df["low"].iloc[i]); mon_high = float(df["high"].iloc[i])
                if gap_size > 0:
                    filled = mon_low <= fri_close
                else:
                    filled = mon_high >= fri_close
                gaps.append({"friday_ist": (ts_prev+IST_OFFSET).isoformat(),
                             "monday_ist": (ts_curr+IST_OFFSET).isoformat(),
                             "friday_close": fri_close, "monday_open": mon_open,
                             "gap_pct": round(gap_size*100,4), "gap_dir": gap_dir,
                             "gap_filled": filled,
                             "monday_move_pct": round(mon_move*100,4),
                             "continuous": asset in CRYPTO})
        if not gaps: continue
        gdf = pd.DataFrame(gaps)
        n = len(gdf)
        results[asset] = {
            "asset": asset, "is_continuous": asset in CRYPTO, "n_weeks": n,
            "gap_up_pct":   round(float((gdf["gap_dir"]=="UP").mean()*100),1),
            "gap_down_pct": round(float((gdf["gap_dir"]=="DOWN").mean()*100),1),
            "gap_fill_pct": round(float(gdf["gap_filled"].mean()*100),1),
            "avg_gap_pct":  round(float(gdf["gap_pct"].mean()),4),
            "median_gap_pct": round(float(gdf["gap_pct"].median()),4),
            "avg_monday_move_pct": round(float(gdf["monday_move_pct"].mean()),4),
            "monday_bullish_pct": round(float((gdf["monday_move_pct"]>0).mean()*100),1),
        }
        print(f"  {asset:8s}: n={n} | GapUp={results[asset]['gap_up_pct']}% | "
              f"Fill={results[asset]['gap_fill_pct']}% | MonBull={results[asset]['monday_bullish_pct']}%")
        gdf.to_csv(os.path.join(OUTPUT_ROOT,"weekend_gaps",f"{asset}_gaps.csv"), index=False)
    with open(os.path.join(OUTPUT_ROOT,"weekend_gaps","weekend_gap_summary.json"),"w") as f:
        json.dump(results, f, indent=2)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 12: REGIME ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def exp12_regime(preds: pd.DataFrame) -> dict:
    print("\n[EXP 12] Regime Analysis")
    os.makedirs(os.path.join(OUTPUT_ROOT,"regime"), exist_ok=True)
    rows = []
    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset]
        for reg in sub["regime"].unique():
            d = sub[sub["regime"]==reg]
            n = len(d)
            if n < 5: continue
            r = d["net_return"]
            gp=r[r>0].sum(); gl=abs(r[r<0].sum()); pf=gp/gl if gl>0 else float("inf")
            std=r.std(); sharpe=(r.mean()/std)*math.sqrt(252*6) if std>0 else 0.0
            cum=(1+r).cumprod(); pk=cum.cummax(); dd=float(((cum-pk)/pk).min())
            rows.append({"asset":asset,"regime":reg,"n":n,
                         "win_rate_pct":round(float(d["win_int"].mean()*100),1),
                         "profit_factor":round(pf,3), "sharpe":round(sharpe,4),
                         "net_return_pct":round(float(r.sum()*100),4),
                         "max_drawdown_pct":round(dd*100,4)})
    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_ROOT,"regime","regime_analysis.csv"), index=False)
    print(f"  Saved {len(rows)} regime rows")
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 13: SIGNAL QUALITY THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════
def exp13_signal_quality(preds: pd.DataFrame) -> dict:
    """
    Tests combinations of confidence thresholds and RR ratios on validation set only.
    Final test set is UNTOUCHED (assumed to be last 20% of data).
    """
    print("\n[EXP 13] Signal Quality Thresholds (validation set only)")
    os.makedirs(os.path.join(OUTPUT_ROOT,"signal_quality"), exist_ok=True)
    # Use only first 80% of timestamps as validation set
    if preds.empty: return {}
    cutoff = preds["timestamp"].quantile(0.8)
    val = preds[preds["timestamp"] <= cutoff].copy()
    results = []
    for conf_thresh in [55, 58, 60, 62, 65]:
        for rr_thresh in [1.0, 1.5, 2.0]:
            sub = val[(val["confidence"]>=conf_thresh) & (val["rr"]>=rr_thresh)]
            n = len(sub)
            if n < 10: continue
            r = sub["net_return"]
            gp=r[r>0].sum(); gl=abs(r[r<0].sum()); pf=gp/gl if gl>0 else float("inf")
            std=r.std(); sharpe=(r.mean()/std)*math.sqrt(252*6) if std>0 else 0.0
            wr=float(sub["win_int"].mean())
            results.append({"conf_thresh":conf_thresh,"rr_thresh":rr_thresh,"n":n,
                            "win_rate_pct":round(wr*100,1),"profit_factor":round(pf,3),
                            "sharpe":round(sharpe,4),"net_return_pct":round(float(r.sum()*100),4)})
            print(f"  conf≥{conf_thresh} RR≥{rr_thresh:.1f}: n={n:5d} | WR={wr*100:.1f}% | PF={pf:.2f} | Sharpe={sharpe:.2f}")
    df_out = pd.DataFrame(results)
    df_out.to_csv(os.path.join(OUTPUT_ROOT,"signal_quality","signal_quality_thresholds.csv"), index=False)
    best = df_out.loc[df_out["sharpe"].idxmax()].to_dict() if len(df_out) > 0 else {}
    print(f"  Best threshold (validation): {best}")
    return {"results": results, "best_on_validation": best}


# ═══════════════════════════════════════════════════════════════════════════════
# EXP 11: MULTI-ASSET SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
def exp11_multiasset_summary(preds: pd.DataFrame) -> dict:
    print("\n[EXP 11] Multi-Asset Comparison")
    os.makedirs(os.path.join(OUTPUT_ROOT,"multiasset"), exist_ok=True)
    rows = []
    for asset in preds["asset"].unique():
        sub = preds[preds["asset"]==asset]
        r = sub["net_return"]
        n = len(r)
        if n < 10: continue
        gp=r[r>0].sum(); gl=abs(r[r<0].sum()); pf=gp/gl if gl>0 else float("inf")
        std=r.std(); sharpe=(r.mean()/std)*math.sqrt(252*6) if std>0 else 0.0
        cum=(1+r).cumprod(); pk=cum.cummax(); dd=float(((cum-pk)/pk).min())
        wr=float(sub["win_int"].mean())
        avg_w=float(r[r>0].mean()) if (r>0).any() else 0.0
        avg_l=float(r[r<0].mean()) if (r<0).any() else 0.0
        exp=wr*avg_w+(1-wr)*avg_l
        rows.append({"asset":asset,"n_trades":n,"win_rate_pct":round(wr*100,1),
                     "profit_factor":round(pf,3),"sharpe":round(sharpe,4),
                     "max_drawdown_pct":round(dd*100,4),"expectancy":round(exp,6),
                     "net_return_pct":round(float(r.sum()*100),4)})
    df_out = pd.DataFrame(rows).sort_values("sharpe", ascending=False)
    df_out.to_csv(os.path.join(OUTPUT_ROOT,"multiasset","multiasset_summary.csv"), index=False)
    print(df_out.to_string(index=False))
    best  = df_out.iloc[0]["asset"] if len(df_out)>0 else "N/A"
    worst = df_out.iloc[-1]["asset"] if len(df_out)>0 else "N/A"
    print(f"\n  BEST ASSET (Sharpe):   {best}")
    print(f"  WORST ASSET (Sharpe):  {worst}")
    return {"ranking": rows, "best": best, "worst": worst}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
async def main():
    db_url = "sqlite+aiosqlite:///./trading_fallback.db"
    print("="*70)
    print("PHASE 16 — ANALYTICS EXPERIMENTS 4-13")
    print("="*70)

    # Generate shared prediction set
    print("\n[SETUP] Generating H4 predictions for all assets...")
    preds = await generate_h4_predictions(db_url)
    if preds.empty:
        print("ERROR: No predictions generated. Check DB has H4 data.")
        return
    print(f"  Total predictions: {len(preds):,} across {preds['asset'].nunique()} assets")
    preds.to_csv(os.path.join(OUTPUT_ROOT, "all_h4_predictions.csv"), index=False)

    # Run all experiments
    cal_result  = exp4_confidence_calibration(preds)
    rnd_result  = exp5_random_baseline(preds)
    sl_result   = exp6_self_learning(preds)
    dow_result  = exp7_dayofweek(preds)
    tod_result  = exp8_timeofday(preds)
    sess_result = exp9_sessions(preds)
    gap_result  = await exp10_weekend_gaps(db_url)
    multi_result= exp11_multiasset_summary(preds)
    reg_result  = exp12_regime(preds)
    sq_result   = exp13_signal_quality(preds)

    # Master summary
    master = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_predictions": len(preds),
        "assets": list(preds["asset"].unique()),
        "exp4_calibration": cal_result,
        "exp5_random_baseline": rnd_result,
        "exp6_self_learning": sl_result,
        "exp11_multiasset": multi_result,
        "exp12_regime_rows": len(reg_result),
        "exp13_best_threshold": sq_result.get("best_on_validation",{}),
    }
    with open(os.path.join(OUTPUT_ROOT,"analytics_master_summary.json"),"w") as f:
        json.dump(master, f, indent=2)
    print(f"\n[DONE] All analytics experiments complete. Outputs in: {OUTPUT_ROOT}")

    for exp in ["exp4","exp5","exp6","exp7","exp8","exp9","exp10","exp11","exp12","exp13"]:
        with open(os.path.join(OUTPUT_ROOT, f"phase16_{exp}.done"),"w") as f:
            f.write(datetime.utcnow().isoformat())

if __name__ == "__main__":
    asyncio.run(main())
