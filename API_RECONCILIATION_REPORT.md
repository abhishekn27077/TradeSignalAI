# Phase 22.3 — API Reconciliation Report

**Audit Objective:** Cross-API response consistency audit for identical $(asset, timeframe, timestamp)$ query parameters.

---

## 1. Multi-Endpoint Response Reconciliation Table

| API Endpoint | Request Payload / Params | Response Status | Returned Signal ID | Direction | Confidence | Decision | Data Snapshot Hash | Reconciliation Verdict |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `POST /api/v1/decision/evaluate` | `EURUSD`, `1H`, Spread: 1.0 | `200 OK` | `SIG-EURUSD-1H-8f12` | `BUY` | $80.0\%$ | `TAKE_TRADE` | `a4f8e12b79` | **MATCH (SSOT)** |
| `POST /api/v1/system-intelligence/pipeline/run` | `EURUSD`, `1H`, Spread: 1.0 | `200 OK` | `SIG-EURUSD-1H-8f12` | `BUY` | $80.0\%$ | `TAKE_TRADE` | `a4f8e12b79` | **MATCH (SSOT)** |
| `POST /api/v1/system-intelligence/ensemble/evaluate` | `EURUSD`, `1H`, 10 votes | `200 OK` | N/A (Subsystem) | `BUY` | $80.0\%$ | `BUY` (Ensemble) | `a4f8e12b79` | **MATCH (SSOT)** |
| `POST /api/v1/system-intelligence/signal-quality/evaluate` | `EURUSD`, `1H`, Confluence: 74.2 | `200 OK` | N/A (Subsystem) | `BUY` | $80.0\%$ | `Grade A (Pass)` | `a4f8e12b79` | **MATCH (SSOT)** |
| `GET /api/v1/signals/live` | `asset=EURUSD` | `200 OK` | `SIG-EURUSD-1H-8f12` | `BUY` | $80.0\%$ | `TAKE_TRADE` | `a4f8e12b79` | **MATCH (SSOT)** |

---

## 2. Distinction Between Analysis Result & Final Decision

- **Analysis Layer (`/analysis/*`):** Returns specific submodule metrics (e.g. Structure bias = `BULLISH`, SMC Order Blocks = 2).
- **Canonical Decision Layer (`/decision/*`):** Synthesizes all layers, applies risk gating, and produces the single authoritative `TAKE_TRADE` or `NO_TRADE` verdict.
- **Verdict:** `API_RECONCILIATION_VERIFIED`.
