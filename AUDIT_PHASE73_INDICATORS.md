# Phase 73 — Technical Indicators Mathematical Parity Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **MATHEMATICAL DISCREPANCY & DOCUMENTATION MISREPRESENTATION**

---

## 1. Executive Summary

A rigorous mathematical audit comparing the indicator formulas implemented in `app/strategies/indicators/` and `app/core/canonical_signal_service.py` against standard reference formulas (TradingView Pine Script `ta.rsi`, `ta.atr`) was executed on real BTCUSD historical candles from `tradesignal.db`.

### Key Finding
`INDICATOR_PARITY_REPORT.md` claimed:
> *RSI: TradingView `ta.rsi(close, 14)` vs Backend: Wilder's exponential smoothing ... VERIFIED PARITY: None*

**This claim is FALSE.** The backend implementation uses simple rolling arithmetic mean (Cutler's RSI), NOT Wilder's exponential moving average. On real BTCUSD candles, the discrepancy between the system's RSI and TradingView's Wilder RSI reaches up to **12.14 points** (e.g. System: 38.13 vs TradingView: 50.27).

---

## 2. Mathematical Parity Verification Results

### 2.1 RSI (Relative Strength Index)
- **Implemented Code (`app/strategies/indicators/momentum.py:36-40`):**
  ```python
  avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
  avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()
  rs = avg_gain / avg_loss
  rsi = 100 - (100 / (1 + rs))
  ```
- **TradingView Pine Script Standard (`ta.rsi(close, 14)`):**
  Uses Wilder's smoothing (RMA):
  $$\text{gain}_t = \frac{1}{N}\text{gain}_t + \frac{N-1}{N}\text{gain}_{t-1} = \text{ewm}(\alpha = 1/N, \text{adjust}=\text{False})$$
- **Forensic Execution on Real 1H BTCUSD Candles:**

| Timestamp | Close Price | System Implemented (SMA) | Cutler Reference (SMA) | TradingView Reference (Wilder RMA) | Discrepancy ($\Delta$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `2024-08-15 20:00:00` | $56,386.16 | **32.75** | 32.75 | **23.06** | **9.69** |
| `2024-08-15 21:00:00` | $57,567.29 | **45.77** | 45.77 | **40.67** | **5.09** |
| `2024-08-15 22:00:00` | $57,642.15 | **44.27** | 44.27 | **41.59** | **2.69** |
| `2024-08-16 02:00:00` | $58,204.99 | **45.18** | 45.18 | **49.75** | **4.57** |
| `2024-08-16 03:00:00` | $57,882.05 | **37.50** | 37.50 | **46.16** | **8.65** |
| `2024-08-16 04:00:00` | $58,306.22 | **41.34** | 41.34 | **51.15** | **9.81** |
| `2024-08-16 05:00:00` | $58,232.38 | **38.13** | 38.13 | **50.27** | **12.14** |

**Trading Consequence:** At `2024-08-16 05:00:00`, the system indicates oversold/bearish momentum at 38.13, whereas TradingView indicates neutral/bullish momentum at 50.27.

---

### 2.2 ATR (Average True Range)
- **Implemented Code (`app/strategies/indicators/volatility.py:27-28`):**
  ```python
  tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
  atr = tr.rolling(window=self.period).mean()
  ```
- **Standard (`ta.atr(14)`):**
  Uses Wilder's smoothing RMA (`tr.ewm(alpha=1/14, adjust=False).mean()`).
- **Discrepancy:** Simple rolling average causes sudden step-dropouts after 14 bars when a high-volatility spike drops out of the rolling window, causing trailing stops and dynamic SL/TP levels to jump erratically.

---

### 2.3 MACD (Moving Average Convergence Divergence)
- **Implemented Code (`app/core/canonical_signal_service.py:196-200`):**
  ```python
  ema12 = close.ewm(span=12, adjust=False).mean()
  ema26 = close.ewm(span=26, adjust=False).mean()
  macd_line = ema12 - ema26
  signal_line = macd_line.ewm(span=9, adjust=False).mean()
  ```
- **Parity Assessment:** **VERIFIED PARITY.** Standard exponential moving average with spans 12, 26, 9 matches standard TradingView MACD formula exactly.

---

### 2.4 Fake Indicators in `TradingViewAdapter`
- **Location:** `app/market_intelligence/tradingview_adapter.py:251-269`
- **Code:**
  ```python
  if ind_id == "rsi_wilder":
      features["rsi_14"] = 58.2
  elif ind_id == "atr_volatility_regime":
      features["atr_normalized"] = 0.0045
  elif ind_id == "smc_bos_choch":
      features["market_structure"] = "BULLISH_BOS"
  ```
- **Finding:** In `tradingview_adapter.py`, indicators are **hardcoded static constants** accompanied by false claims of `"STRICTLY_NON_REPAINTING"` and `"ZERO_LOOKAHEAD_VERIFIED"`.

---

## 3. Remediation Required
1. In `app/strategies/indicators/momentum.py` and `canonical_signal_service.py`, replace `rolling(window).mean()` with `ewm(alpha=1/period, adjust=False).mean()` to achieve genuine mathematical parity with Wilder's RSI.
2. In `app/strategies/indicators/volatility.py`, replace `tr.rolling().mean()` with Wilder's RMA.
3. Remove static indicator injection in `tradingview_adapter.py`.
