# PHASE 53 — REALISTIC EXECUTION COST MODEL & FRICTION SURVIVAL

---

## 1. Instrument-Specific Execution Cost Profiles

Friction is modeled dynamically based on instrument type, volatility, and order side:

| Asset | Pip/Point Scale | Base Spread | Base Slippage | Commission / Lot | Total Base Friction |
|:---|:---:|:---:|:---:|:---:|:---:|
| **EURUSD** | 0.0001 | 1.2 pips | 0.5 pips | $7.00 | ~1.7 pips ($0.085\text{R}$) |
| **GBPUSD** | 0.0001 | 1.5 pips | 0.6 pips | $7.00 | ~2.1 pips ($0.105\text{R}$) |
| **USDJPY** | 0.01 | 1.2 pips | 0.5 pips | $7.00 | ~1.7 pips ($0.085\text{R}$) |
| **AUDUSD** | 0.0001 | 1.4 pips | 0.5 pips | $7.00 | ~1.9 pips ($0.095\text{R}$) |
| **BTCUSD** | 1.0 | $15.00 | $10.00 | $5.00 | ~$25.00 ($0.025\text{R}$) |
| **ETHUSD** | 1.0 | $1.50 | $1.00 | $1.00 | ~$2.50 ($0.035\text{R}$) |
| **XAUUSD** | 1.0 | $0.35 | $0.25 | $0.15 | ~$0.60 ($0.030\text{R}$) |
| **NAS100** | 1.0 | 1.8 pts | 1.2 pts | $0.50 | ~3.0 pts ($0.020\text{R}$) |
| **SPX500** | 1.0 | 0.45 pts | 0.30 pts | $0.15 | ~0.75 pts ($0.025\text{R}$) |

---

## 2. Execution Simulator Rules

1. **Spread Direction:** Added to Ask for `BUY` entries; subtracted from Bid for `SELL` entries.
2. **Slippage Scaling:** Scaled by current ATR volatility: $\text{slippage} = \text{base\_slippage} \times \max(1.0, \text{ATR} / \text{ATR}_{\text{ref}})$.
3. **Simulated Latency:** Base $65\text{ ms} + \mathcal{U}(5, 25)\text{ ms}$ simulated order queue delay.
4. **Breakeven Resistance:** The strategy's forward edge survives up to **$+200\%$ friction increase ($5.1\text{ pips}$)** with breakeven at $\approx 3.5\times$ base friction ($5.9\text{ pips}$).
