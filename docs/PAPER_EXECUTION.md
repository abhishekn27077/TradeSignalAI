# Paper Execution Safety Policy — TradeSignalAI-v3

## 1. Safety Mandate

TradeSignalAI-v3 is exclusively a **RESEARCH, WALK-FORWARD BACKTESTING, AND PROSPECTIVE PAPER-SIGNAL SYSTEM**.

**Real-money execution is permanently disabled.**

---

## 2. Hardlock Controls

1. **Global Configuration Default**:
   ```python
   REAL_MONEY_ENABLED: bool = False
   EXECUTION_MODE: str = "PAPER_ONLY"
   ```
2. **Order Routing Guard**:
   Any execution adapter attempting to route a real order raises `RealMoneyExecutionProhibitedError`.
3. **Broker Authentication Scope**:
   MT5 connections are configured solely for market-data copying (`copy_rates_from_pos`, `symbol_info_tick`). Order placement functions (`OrderSend`, `OrderSendAsync`) are disallowed and unlinked.
4. **UI Banner**:
   The terminal UI permanently renders the `PAPER ONLY` safety tag in the application header and signal detail views.

---

## 3. Paper Order Simulation Specifications

When a paper trade is journaled:
- **Fill Price**: Real tick `Ask` for Long entries; real tick `Bid` for Short entries.
- **Slippage Model**: Realistic execution delay modeling based on asset class volatility.
- **Spread Cost**: Explicitly accounted for in all Risk-Reward and R-Multiple calculations.
- **Outcome Resolution**: Resolved purely forward in time against subsequent real market bars (Zero lookahead bias).
