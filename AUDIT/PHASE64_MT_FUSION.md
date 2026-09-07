# AUDIT: PHASE 64 MULTI-TIMEFRAME FUSION & SIGNAL STRENGTH DECOMPOSITION
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 64 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. 0–100 Signal Strength Decomposition

Signal strength is calculated across 10 transparent empirical dimensions:

$$\begin{aligned}
\text{Overall Strength} &= 0.15 \cdot \text{Trend} + 0.15 \cdot \text{Momentum} + 0.15 \cdot \text{Structure} \\
&+ 0.10 \cdot \text{Liquidity} + 0.05 \cdot \text{Volatility} + 0.05 \cdot \text{Volume} \\
&+ 0.10 \cdot \text{Forecast Models} + 0.10 \cdot \text{Historical Analogue} \\
&+ 0.10 \cdot \text{MTF Alignment} + 0.05 \cdot \text{Expected Net R}
\end{aligned}$$

---

## 2. Multi-Timeframe Concordance

Short-term signals (5m, 15m) inspect higher-timeframe context (1H, 4H, 1D).
- **HTF Alignment Score:** Ratio of aligned timeframes across the hierarchy ($0.0 \dots 1.0$).
- **MTF Conflict Score:** Ratio of conflicting timeframes ($0.0 \dots 1.0$).
- Hard gate: If MTF conflict $> 0.40$, the setup is rejected with `MTF_CONFLICT_DETECTED`.
