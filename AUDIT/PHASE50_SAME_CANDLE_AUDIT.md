# PHASE 50.18 — SAME-CANDLE TP/SL AMBIGUITY & CONSERVATIVE RESOLUTION AUDIT

**Audit Scope:** Independent scan of all forward trade resolutions for cases where both Stop Loss and Take Profit levels fall within the High-Low range of the same candle.

---

## 1. Ambiguity Resolution Policy

$$\text{If } \text{Low} \le \text{SL} \text{ AND } \text{High} \ge \text{TP} \implies \mathbf{RESOLVE\_AS\_LOSS\; (SL\_FIRST)}$$

- **Invariant:** When intrabar tick-level ordering is unavailable, the execution engine enforces the **conservative worst-case invariant** (Stop Loss hit first).

---

## 2. Forward Sample Audit ($N_{\text{trades}}=42$)

- **Same-Candle Ambiguous Trades Identified:** **$2$** trades (both occurred during high-volatility 1H candles).
- **Resolution Applied:** Both 2 trades were resolved as **LOSSES** ($-1.0\text{ R}$ and $-0.95\text{ R}$).
- **Optimistic Resolution Sensitivity (Counterfactual TP first):**
  - If resolved optimistically (TP first): Profit Factor would be $1.94$, Win Rate $66.7\%$.
  - Reported Headline Performance ($1.78\text{ PF}$, $61.9\%\text{ Win Rate}$) uses the **conservative worst-case** resolution.

---

## 3. Verdict

Zero artificial inflation from same-candle ambiguity exists. Headline performance is strictly conservative.
- **Classification:** `CONSERVATIVE_RESOLUTION_VERIFIED`.
