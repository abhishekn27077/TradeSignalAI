# Phase 23.1 — Experiment Configuration Freeze & Fingerprint Report

**Experiment ID:** `EXP-PHASE23-STATISTICAL-VALIDATION-V1`  
**Freeze Timestamp (UTC):** `2026-08-22T20:07:50Z`  
**Git Baseline Commit:** `d1b7b8f`  
**Git Tag:** `phase-22-certified`  
**Authoritative Config Hash:** `CONFIG_HASH = 79a4f8e12b79310d`

---

## 1. Frozen System Configuration Parameters

| Parameter Category | Configuration Parameter | Frozen Value | Invariant Rule |
|:---|:---|:---:|:---|
| **Strategy & Models** | Strategy Version | `52.0.0-PROD` | Locked |
| | Model Consensus Version | `52.0.0-ENSEMBLE` | Locked |
| | Supermajority Consensus Threshold | $60.0\%$ | Locked |
| | Cluster Collinearity Dampening Factor | $\frac{1}{\sqrt{K}}$ | Locked |
| **Risk Gating** | Minimum Reward-to-Risk Ratio | $1.50$ (Target $2.00$) | Locked |
| | Maximum Daily Drawdown Halt | $5.0\%$ | Fail-Closed |
| | Max Single Currency Net Exposure | $3.0$ Lots | Fail-Closed |
| | Maximum Base Spread Filter | $3.0$ Pips | Fail-Closed |
| | Economic Event Release Blackout | $\pm 30$ Minutes | Fail-Closed |
| **Universe & Execution** | Core Asset Universe | 9 Assets (BTC, ETH, EUR, GBP, JPY, AUD, XAU, NAS, SPX) | Locked |
| | Primary Timeframe | `1H` (with 4H & 1D MTF Alignment) | Locked |
| | Execution Mode | `VIRTUAL_PAPER_SHADOW` | Locked |
| | Real-Money Execution | `STRICTLY_DISABLED` | **Permanent Invariant** |

---

## 2. Immutable Hash Verification

Every downstream decision, trade evaluation, and statistical ledger entry must record `CONFIG_HASH = 79a4f8e12b79310d`. Any modification to parameters requires terminating this experiment and initiating a distinct versioned trial.
