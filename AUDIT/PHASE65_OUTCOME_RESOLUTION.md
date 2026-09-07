# AUDIT: PHASE 65 AUTOMATIC OUTCOME RESOLUTION & FRICTION ACCOUNTING
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 65 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. Automatic Background Lifecycle Resolver

The automatic resolver (`app/analytics/lifecycle_resolver_engine.py`) scans unresolved signals and evaluates subsequent market candles where $\text{timestamp} > T_0$:
- **Take Profit (TP):** High $\ge$ TP (for BUY) or Low $\le$ TP (for SELL) $\to$ **WON**
- **Stop Loss (SL):** Low $\le$ SL (for BUY) or High $\ge$ SL (for SELL) $\to$ **LOST**
- **Ambiguous:** Simultaneous hit in single candle $\to$ **AMBIGUOUS** (conservative loss assumption)
- **Time Exit:** Expiry reached $\to$ **TIME_EXIT** at candle close

---

## 2. Realistic Friction Accounting

All realized returns deduct:
- **Spread:** 1.0 pip ($0.00010$)
- **Slippage:** 0.5 pip ($0.00005$)
- **Broker Fees:** 0.5 pip ($0.00005$)
$$\text{Realized Net } R = \frac{\text{Gross PnL} - \text{Total Friction}}{\text{Initial Risk}}$$
