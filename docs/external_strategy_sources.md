# External Strategy Research & License Compliance Matrix

**Document Version:** 1.0.0  
**Compliance Standard:** Institutional Non-Infringement & Clean-Room Native Implementation  
**Policy:** TradingView and Pine Script indicators are **RESEARCH INPUT ONLY**. No proprietary or invite-only source code is copied or redistributed. All algorithmic concepts are implemented independently and natively in Python within TradeSignalAI-v3.

---

## 1. External Strategy Sources & License Analysis

| Source # | Indicator / Strategy Title | Author | Source URL | Open-Source / License | Reuse Permitted? | Attribution Required? | Concepts Extracted | Code Reused? | Implementation Method | Operational Notes |
|:---|:---|:---|:---|:---|:---:|:---:|:---|:---:|:---|:---|
| **1** | Smart Money Concepts (SMC) | LuxAlgo | [TradingView Script](https://in.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/) | Proprietary / TV Public Script (No direct reuse license) | No (Concept Only) | Yes (Conceptual citation) | Swing High/Low detection, Bullish/Bearish BOS, Bullish/Bearish CHoCH, Order Block creation & mitigation lifecycle, Equal Highs/Lows (EQH/EQL), Fair Value Gaps (FVG) | **NO** | Native Python Clean-Room Engine (`app/Strategies/Structure/`, `app/Strategies/SmartMoney/`) | Independent mathematical formulation using confirmed bar closures only. Zero lookahead. |
| **2** | Market Structure Break & Order Block | Joy_Bangla / Community | [TradingView Script](https://www.tradingview.com/script/DkE7UniD/) | TV Public Domain | No (Concept Only) | Yes | Market Structure Break (MSB), Breaker Blocks, Mitigation Blocks, Zig-Zag swing validation | **NO** | Native Python Clean-Room Engine (`app/Strategies/SmartMoney/OrderBlocks/`) | Formulated with strict lifecycle states: `CREATED`, `ACTIVE`, `TOUCHED`, `PARTIALLY_MITIGATED`, `FULLY_MITIGATED`, `INVALIDATED`. |
| **3** | ICT Killzones + Pivots | TFO / yusin99 | [GitHub / TV](https://github.com/yusin99/Tradingview-Indicator---Pivots-and-Killzones) | MIT License | Yes (MIT) | Yes | Asian Session, London Open Killzone, NY AM Killzone, NY PM Killzone, Daily/Weekly/Monthly Pivots & Prior High/Low reference levels | **NO** | Native Python using existing `MarketClockService` (`app/Strategies/Session/`) | Integrated seamlessly with existing `MarketClockService` for canonical UTC/IST conversion. Never hardcodes fixed hours. |
| **4** | SMC + SMT Divergence + Sweep | Community / TV | [TradingView Script](https://in.tradingview.com/script/RkQQOeI2/) | TV Public Script | No (Concept Only) | Yes | Smart Money Technique (SMT) divergence across correlated pairs (e.g. EURUSD vs DXY, BTC vs ETH), Liquidity Sweeps with structural confirmation | **NO** | Native Python Clean-Room Engine (`app/Strategies/Correlation/`, `app/Strategies/SmartMoney/Liquidity/`) | SMT Divergence serves as supporting confluence evidence only; cannot create isolated trades. |
| **5** | SuperTrend | KivancOzbilgic / Olivier Seban | [TradingView Script](https://www.tradingview.com/script/P5Gu6F8k/) | Public / Standard Algorithmic Indicator | Yes (Standard Algorithm) | Yes | ATR-based adaptive trailing band, trend direction flip detection, dynamic volatility multiplier | **NO** | Native Vectorized NumPy/Pandas in Python (`app/Strategies/Technical/`) | Returns structured evidence object: `value`, `direction`, `strength`, `state`. Non-repainting. |
| **6** | UT Bot Alerts | QuantNomad / Yo_Crypto_Mama | [TradingView Script](https://www.tradingview.com/script/n8ss8BID-UT-Bot-Alerts/) | TV Public Script | No (Concept Only) | Yes | ATR trailing stop calculation, key value sensitivity smoothing, momentum crossover filters | **NO** | Native Python Clean-Room Engine (`app/Strategies/Technical/ut_bot.py`) | Vectorized deterministic output on confirmed closed candles. |
| **7** | MACD + SMA 200 Strategy | ChartArt | [TradingView Script](https://www.tradingview.com/script/yMCa3XZD-MACD-SMA-200-Strategy-by-ChartArt/) | TV Public Script | No (Concept Only) | Yes | Multi-horizon trend filtering (SMA 200 regime filter) combined with MACD histogram momentum confirmation | **NO** | Native Python Clean-Room Engine (`app/Strategies/Technical/macd_sma.py`) | Strictly utilized as trend-momentum evidence component within Strategy Router & Confluence Engine. |

---

## 2. Clean-Room Architectural Principles

1. **Deterministic Input:** Calculations operate strictly on historical closed candles ($C_{t \le T}$) available at decision timestamp $T$.
2. **Zero Lookahead:** No future candle highs, lows, volumes, or close prices leak into feature vectors, swing detection, or block formations.
3. **Fail-Closed Integration:** If a correlated asset (e.g., DXY for EURUSD SMT) or event calendar data is missing, the engine reports `CORRELATION_DATA_UNAVAILABLE` or `EVENT_DATA_UNAVAILABLE` rather than guessing or fabricating values.
4. **Timezone Authority:** All internal timestamps are stored and computed as timezone-aware UTC, formatted to IST via `MarketClockService`.
