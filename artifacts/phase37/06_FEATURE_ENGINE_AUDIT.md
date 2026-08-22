# 06 — Feature Engine Audit & Mathematical Feature Matrix
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Feature Engine Architecture
`FeatureEngine` (`app/analytics/feature_engine.py`) enriches raw OHLCV market candles into a 50+ dimension technical, institutional, and cyclical feature matrix without lookahead bias.

### Technical & Institutional Indicators
1. **Momentum:** RSI (14), MACD (12, 26, 9), Stochastic (%K, %D), CCI (20), Rate of Change (ROC-10), Momentum (10).
2. **Trend:** EMA (20, 50, 200), SMA (20, 50), ADX (14), Directional Indicators (DI+, DI-).
3. **Volatility:** Average True Range (ATR-14), Bollinger Bands (20, 2.0 std), 20-period Rolling Volatility.
4. **Volume & Liquidity:** On-Balance Volume (OBV), VWAP, Money Flow Index (MFI-14), Chaikin Money Flow (CMF-20), Liquidity Proxy.
5. **Smart Money Concepts (SMC):** Bullish/Bearish Fair Value Gaps (FVG), Bullish/Bearish Order Blocks (OB), Rolling 20 min/max Support & Resistance, 3-bar Swing Fractals, Liquidity Sweeps, Change of Character (CHOCH), Break of Structure (BOS).
6. **Temporal & Session:** Asian, London, and New York session indicators.

---

## 2. Invariant & Repair Verification
- **Defect Identified & Resolved:** In Phase 36/37, `EMA_200` caused all rows to be dropped via `dropna()` when retrieving datasets $<200$ bars.
- **Fix Applied:** Implemented dynamic window clamping (`min(len(df), 50)` when bars $<200$) and dual-pass filling (`ffill() -> bfill() -> fillna(0.0)`).
- **Result:** $100\%$ bar retention across arbitrary timeframe query lengths (e.g. 50, 100, 500 bars).
- Status: **PASSED & VERIFIED**.
