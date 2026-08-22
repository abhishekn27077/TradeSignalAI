# Phase 52 Portfolio Intelligence & Correlated Risk Budget Report

**Subsystems:** `app/portfolio/currency_exposure_engine.py`, `app/portfolio/risk_budget_engine.py`  
**Certification Status:** 🟢 **VERIFIED & ACTIVE**

---

## 1. Currency Decomposition & Exposure Protection

The `CurrencyExposureEngine` prevents correlated directional stacking:
- Deconstructs pairs into base and quote currency units (e.g. `EURUSD BUY` (2.0 lots) + `GBPUSD BUY` (1.0 lot) = **-3.0 USD net exposure**).
- Threshold: Enforces maximum single currency exposure (e.g. **2.5 standard lots** or **25% portfolio equity**).
- Any trade that pushes single-currency exposure past the limit is immediately rejected with `CORRELATED_EXPOSURE`.

---

## 2. Dynamic Equity-Based Sizing

The `RiskBudgetEngine` computes:
$$\text{Lots} = \frac{\text{Account Equity} \times \text{Risk \%}}{\text{Stop Distance (pips)} \times \text{Pip Value}}$$
- Modulates risk % dynamically during heightened ATR volatility.
- Halts new trading if daily portfolio drawdown reaches **5.0%**.
