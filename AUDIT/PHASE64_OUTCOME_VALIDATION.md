# AUDIT: PHASE 64 OUTCOME VALIDATION & FRICTION ACCOUNTING
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 64 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. Post-T0 Chronological Outcome Resolution

Signal outcomes are resolved by chronologically evaluating candles where $\text{timestamp} > T_0$ and $\le \text{expiry\_time}$:

1. **BUY Signals:**
   - $\text{High} \ge \text{TP} \longrightarrow \text{WON}$
   - $\text{Low} \le \text{SL} \longrightarrow \text{LOST}$
2. **SELL Signals:**
   - $\text{Low} \le \text{TP} \longrightarrow \text{WON}$
   - $\text{High} \ge \text{SL} \longrightarrow \text{LOST}$
3. **Simultaneous TP & SL in Same Candle:**
   - Evaluated as $\text{AMBIGUOUS}$ with conservative loss assumption (never assuming favorable intrabar ordering).
4. **Neither Hit Before Expiry:**
   - Resolved as $\text{TIME\_EXIT}$ at the closing price of the expiry candle.

---

## 2. Friction-Adjusted Realized R Calculation

For every resolved signal, transaction costs are explicitly deducted:
$$\text{Total Friction} = \text{Spread Cost} + \text{Slippage Cost} + \text{Broker Fees}$$
$$\text{Net Realized PnL} = \text{Gross PnL} - \text{Total Friction}$$
$$\text{Realized } R = \frac{\text{Net Realized PnL}}{\text{Initial Risk Distance}}$$
