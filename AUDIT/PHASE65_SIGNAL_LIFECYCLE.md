# AUDIT: PHASE 65 SIGNAL LIFECYCLE & IMMUTABLE LEDGER
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 65 Certified  
**Mode:** DEMO / PAPER TRADING ONLY  

---

## 1. Lifecycle State Machine Transitions

$$\text{CANDIDATE} \longrightarrow \text{QUALIFIED} \longrightarrow \text{LIVE} \longrightarrow \text{RESOLVING} \longrightarrow \begin{cases}
\text{WON} & (\text{High} \ge \text{TP}) \\
\text{LOST} & (\text{Low} \le \text{SL}) \\
\text{AMBIGUOUS} & (\text{Simultaneous TP \& SL}) \\
\text{TIME\_EXIT} & (\text{Expiry Reached})
\end{cases}$$

- **Immutability:** Once generated at $T_0$, entry price, stop loss, take profit, and generation timestamp cannot be modified.
- **Deduplication:** Hashing on `(asset, timeframe, candle_timestamp)` ensures idempotency and suppresses sub-minute signal spam.
- **Indexes Added:** SQLite indexes on `asset`, `timeframe`, `status`, `outcome`, `generated_at`, `quality_grade` for sub-millisecond query latency.
