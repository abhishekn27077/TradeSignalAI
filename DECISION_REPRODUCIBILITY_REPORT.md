# Phase 22.6 — Decision Reproducibility & Determinism Report

**Audit Objective:** Multi-pass deterministic evaluation verifying zero stochastic drift across identical market snapshots.

---

## 1. Multi-Pass Determinism Test Results

- **Test Snapshot:** `EURUSD` 1H (80 historical closed candles).
- **Number of Consecutive Passes:** 50 iterations.

| Parameter Evaluated | Pass #1 | Pass #10 | Pass #25 | Pass #50 | Invariant Result |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Decision** | `TAKE_TRADE` | `TAKE_TRADE` | `TAKE_TRADE` | `TAKE_TRADE` | **100% Identical** |
| **Direction** | `BUY` | `BUY` | `BUY` | `BUY` | **100% Identical** |
| **Ensemble Confidence** | `0.800` | `0.800` | `0.800` | `0.800` | **100% Identical** |
| **Confluence Score** | `74.20` | `74.20` | `74.20` | `74.20` | **100% Identical** |
| **Allocated Lots** | `0.50` | `0.50` | `0.50` | `0.50` | **100% Identical** |
| **Entry Price** | `1.08532` | `1.08532` | `1.08532` | `1.08532` | **100% Identical** |
| **Stop Loss** | `1.08332` | `1.08332` | `1.08332` | `1.08332` | **100% Identical** |
| **Take Profit** | `1.08932` | `1.08932` | `1.08932` | `1.08932` | **100% Identical** |
| **Config Hash** | `79a4f8e12b79310d` | `79a4f8e12b79310d` | `79a4f8e12b79310d` | `79a4f8e12b79310d` | **100% Identical** |

---

## 2. Model Determinism Settings

- All deep learning and similarity search components (Kronos, FAISS, Quant Core) execute with fixed random seeds (`SEED = 42`) and deterministic floating-point operations.
- **Verdict:** `DECISION_REPRODUCIBILITY_VERIFIED`.
