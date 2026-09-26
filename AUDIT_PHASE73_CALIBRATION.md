# Phase 73 — Confidence Calibration & Brier Score Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **CALIBRATION CLAIMS ARE STATICALLY FABRICATED**

---

## 1. Executive Summary

Documentation throughout the project claims that TradeSignalAI-v3 exhibits state-of-the-art probability calibration:
- *Brier Score < 0.188*
- *Expected Calibration Error (ECE) < 0.04*
- *8-bucket reliability curves demonstrating monotonicity*

A forensic code audit reveals that these calibration metrics and reliability buckets are **not calculated from prospective out-of-sample prediction outcomes**. Instead, they are returned directly from **static, hardcoded dictionaries** inside the analytics reporting engines.

---

## 2. Forensic Code Evidence

### 2.1 Hardcoded Scorecards in `prediction_reality_engine.py`
- **Location:** `app/analytics/prediction_reality_engine.py:43-62`
- **Code:**
  ```python
  asset_scores = {
      "EURUSD": {"score": 81.0, "directional_accuracy_pct": 72.5, "brier_score": 0.185, ...},
      "GBPUSD": {"score": 76.5, "directional_accuracy_pct": 68.8, "brier_score": 0.204, ...},
      "BTCUSD": {"score": 82.4, "directional_accuracy_pct": 75.0, "brier_score": 0.172, ...},
      ...
  }
  model_scores = {
      "Quant Baseline": {"accuracy_pct": 52.4, "brier_score": 0.245, "status": "ACTIVE"},
      "Kronos Foundation": {"accuracy_pct": 58.6, "brier_score": 0.212, "status": "ACTIVE"},
      "Full Consensus Ensemble": {"accuracy_pct": 66.8, "brier_score": 0.175, "status": "ACTIVE"},
  }
  ```
- **Finding:** Every call to `get_scorecards()` returns these exact fixed floats regardless of database state or recent performance.

### 2.2 Hardcoded Benchmarks in `research_benchmark_engine.py`
- **Location:** `app/analytics/research_benchmark_engine.py:55-80`
- **Code:**
  ```python
  champion = BenchmarkModelResult(
      model_name="Canonical TradeSignalAI-v3",
      brier_score=0.174,
      win_rate_pct=66.8, ...
  )
  ema_baseline = BenchmarkModelResult(
      model_name="Simple EMA 9/21 Cross",
      brier_score=0.245,
      win_rate_pct=51.2, ...
  )
  ```
- **Finding:** Brier scores are defined as constructor arguments in hardcoded objects.

### 2.3 Simulated Perturbation in `data_window_engine.py`
- **Location:** `app/analytics/data_window_engine.py:251`
- **Code:**
  ```python
  "brier_score": round(brier_score + np.random.uniform(-0.01, 0.01), 4)
  ```
- **Finding:** Adds random jitter (`np.random.uniform(-0.01, 0.01)`) to simulate dynamic calibration variations across windows!

---

## 3. Real Calibration Implementation (`tomorrow_pit_backtest_engine.py`)

A genuine mathematical formula for Brier score exists in `app/forecast/tomorrow_pit_backtest_engine.py:116`:
```python
# Brier score calculation: (p - y)^2 where y=1 if correct, 0 if incorrect
brier_sum += (p - y) ** 2
```
However, this engine is only executed during historical backtesting scripts, not on the live runtime dashboard or API reporting routes.

---

## 4. Verdict
**FAIL / FABRICATED EVIDENCE.** Confidence values do not correspond to empirically validated probabilities on out-of-sample data. The Brier score claims in documentation are static artifacts.
