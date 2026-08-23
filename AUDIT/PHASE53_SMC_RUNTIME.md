# PHASE 53 — SMART MONEY CONCEPTS (SMC) RUNTIME & CAUSALITY AUDIT

---

## 1. SMC Structural Components

Stage 5 of the Quant Pipeline evaluates 5 structural features:

| SMC Feature | Detection Logic | Closed Bars Lookback | Forward Lookahead Risk |
|:---|:---|:---:|:---:|
| **Break of Structure (BOS)** | Candle close breaks preceding confirmed swing high/low | $N \ge 20$ closed bars | **Zero (Closed Bars Only)** |
| **Change of Character (CHoCH)** | Candle close breaks counter-trend swing high/low | $N \ge 20$ closed bars | **Zero (Closed Bars Only)** |
| **Order Block (OB)** | Last opposing candle before aggressive displacement | $N \ge 10$ closed bars | **Zero (Closed Bars Only)** |
| **Fair Value Gap (FVG)** | 3-bar price imbalance (Bar 1 High < Bar 3 Low) | 3 closed bars | **Zero (Closed Bars Only)** |
| **Liquidity Sweep** | Price pierces swing level but closes back inside range | $N \ge 15$ closed bars | **Zero (Closed Bars Only)** |

---

## 2. Non-Repainting Invariant

1. **Closed Bar Enforcement:** Swing highs and lows are identified strictly using closed candles with a minimum 2-bar right confirmation (`[t-2, t-1, t, t+1, t+2]` evaluated strictly at `t+2` close).
2. **Zero Unclosed Candle Access:** Features cannot reference the unclosed live bar (`candle_index = -1` close price is unknown until bar close).
3. **Attribution:** $+0.37\text{ PF}$ joint contribution with documented $0.20\text{ PF}$ multi-collinear feature overlap.
