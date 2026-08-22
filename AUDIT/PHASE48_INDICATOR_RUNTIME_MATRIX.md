# PHASE 48.6 — INDICATOR RUNTIME EXECUTION MATRIX

**Audit Scope:** Verification of code execution paths from raw calculation to `CanonicalDecisionEngine.evaluate_market()`.

---

## 1. Indicator Execution & Influence Matrix

| Indicator Name | Module Location | Implemented? | Used by Engine? | Affects Direction? | Affects Risk / Sizing? | Affects Gating / Filter? | Runtime Classification |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **EMA 20** | `app/indicators/trend.py` | YES | YES | YES | NO | NO | `CORE_SIGNAL_FEATURE` |
| **EMA 50** | `app/indicators/trend.py` | YES | YES | YES | NO | NO | `CORE_SIGNAL_FEATURE` |
| **EMA 200** | `app/indicators/trend.py` | YES | YES | YES | NO | NO | `CORE_SIGNAL_FEATURE` |
| **SuperTrend (10, 3.0)** | `app/indicators/trend.py` | YES | YES | YES | Trailing SL | NO | `CORE_SIGNAL_FEATURE` |
| **RSI (14)** | `app/indicators/momentum.py` | YES | YES | YES | NO | YES | `CORE_SIGNAL_FEATURE` |
| **MACD (12, 26, 9)** | `app/indicators/momentum.py` | YES | YES | YES | NO | NO | `CORE_SIGNAL_FEATURE` |
| **ATR (14)** | `app/indicators/volatility.py`| YES | YES | NO | YES (SL/TP Distances)| YES (Min Volatility) | `RISK_FEATURE` |
| **ADX (14)** | `app/strategies/indicators/trend.py`| YES | YES | NO | NO | YES (Chop Filter $<20$) | `REGIME_FEATURE` |
| **BOS (Break of Structure)**| `app/strategies/SmartMoney/`| YES | YES | YES | Entry Anchor | YES | `CORE_SIGNAL_FEATURE` |
| **CHoCH (Change of Char)**| `app/strategies/SmartMoney/`| YES | YES | YES | Entry Anchor | YES | `CORE_SIGNAL_FEATURE` |
| **Order Blocks** | `app/strategies/SmartMoney/`| YES | YES | YES | Entry / SL Level | YES | `CORE_SIGNAL_FEATURE` |
| **FVG (Fair Value Gaps)** | `app/strategies/SmartMoney/`| YES | YES | YES | TP Target | YES | `CORE_SIGNAL_FEATURE` |
| **Liquidity Sweeps** | `app/strategies/SmartMoney/`| YES | YES | YES | Entry Anchor | YES | `CORE_SIGNAL_FEATURE` |
| **SMA (50, 200)** | `app/indicators/trend.py` | YES | YES | YES | NO | NO | `SUPPORTING_FEATURE` |
| **VWAP** | `app/indicators/volume.py` | YES | YES | YES | NO | NO | `SUPPORTING_FEATURE` |
| **Bollinger Bands** | `app/indicators/volatility.py`| YES | YES | YES | Dynamic Band SL | NO | `SUPPORTING_FEATURE` |

---

## 2. Invariant Rule Enforcement

- Zero phantom indicators exist in the core pipeline; every indicator tagged as `CORE_SIGNAL_FEATURE` or `RISK_FEATURE` has a verified execution path into `CanonicalTradingSignal`.
