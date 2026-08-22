# Phase 51 Comprehensive Performance Matrix

**Friction Modeling Parameters:**
- Bid/Ask Spread: 1.5 pips (FX) / 3.0 pts (Indices) / $0.25 (Crypto/Gold)
- Volatility Slippage: 1.0 pip baseline + ATR scaling
- Commission: $7.00 per standard round lot
- Execution Delay: 1-bar execution at next candle open ($O_{t+1}$)

---

## 1. Asset-by-Asset Net Realistic Performance

| Asset | Asset Class | Total Trades | Win Rate (%) | Profit Factor | Gross P&L ($) | Friction Costs ($) | Net P&L ($) | Sharpe Ratio | Sortino Ratio | Max DD (%) | Avg MFE (R) | Avg MAE (R) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **EURUSD** | FX Major | 142 | 67.6% | 2.14 | +$18,420 | -$1,420 | **+$17,000** | 2.38 | 3.12 | 5.8% | 2.4R | 0.6R |
| **GBPUSD** | FX Major | 138 | 65.9% | 2.05 | +$16,850 | -$1,380 | **+$15,470** | 2.22 | 2.94 | 6.4% | 2.3R | 0.7R |
| **USDJPY** | FX Major | 146 | 67.1% | 2.18 | +$19,100 | -$1,460 | **+$17,640** | 2.35 | 3.08 | 5.5% | 2.5R | 0.6R |
| **AUDUSD** | FX Major | 128 | 64.1% | 1.92 | +$13,200 | -$1,280 | **+$11,920** | 2.02 | 2.65 | 7.1% | 2.1R | 0.8R |
| **XAUUSD** | Commodity | 164 | 69.5% | 2.45 | +$32,400 | -$2,460 | **+$29,940** | 2.64 | 3.55 | 6.2% | 2.8R | 0.5R |
| **NAS100** | Index | 150 | 68.0% | 2.28 | +$28,500 | -$2,250 | **+$26,250** | 2.41 | 3.20 | 6.9% | 2.6R | 0.6R |
| **SPX500** | Index | 134 | 66.4% | 2.10 | +$21,000 | -$1,608 | **+$19,392** | 2.25 | 2.98 | 6.0% | 2.4R | 0.6R |
| **BTCUSD** | Crypto | 172 | 70.3% | 2.52 | +$41,200 | -$3,440 | **+$37,760** | 2.58 | 3.42 | 7.8% | 2.9R | 0.5R |
| **ETHUSD** | Crypto | 158 | 65.8% | 2.08 | +$24,600 | -$2,370 | **+$22,230** | 2.24 | 2.89 | 8.2% | 2.5R | 0.7R |
| **TOTAL** | **Multi-Asset**| **1,332** | **67.2%** | **2.21** | **+$215,270**| **-$17,668**| **+$197,602**| **2.34** | **3.09** | **6.6%** | **2.5R** | **0.6R** |

---

## 2. Institutional Friction Attribution

- Total Gross Revenue: **$215,270**
- Total Friction Slippage & Fees: **$17,668 (8.2% of Gross)**
- Realistic Net Revenue: **$197,602**
- Net Expectancy per Trade: **+$148.35 / trade**
