# PHASE 47.1 — FROZEN CONFIGURATION & IMMUTABLE BENCHMARK STATE

**Freeze Date (UTC):** `2026-08-22T21:25:50Z`  
**Git Baseline Commit:** `ae93614`  
**Git Tag:** `phase-46-certified`  
**Authoritative Config Hash:** `CONFIG_HASH = 79a4f8e12b79310d`  
**Real-Money Execution Status:** `STRICTLY_DISABLED`

---

## 1. Frozen Trading Engine Parameters

| Parameter Layer | Configuration Parameter | Locked Value | Invariant Enforcement |
|:---|:---|:---:|:---|
| **Strategy Suite** | Strategy Version | `52.0.0-PROD` | Locked |
| | Supermajority Consensus Threshold | $60.0\%$ | Locked |
| | Cluster Collinearity Dampener | $\frac{1}{\sqrt{K}}$ | Locked |
| **Indicator Suite** | Registry Version | `46.0.0-PROD` | Locked in `indicator_registry.json` |
| | EMA Periods | $20, 50, 200$ | Locked |
| | RSI Period & Smoothing | $14$ (Wilder's Smoothing) | Locked |
| | ATR Period | $14$ | Locked |
| | ADX Period & Regime Gate | $14$ ($ADX \ge 20.0$ for trend) | Locked |
| **Risk Gating** | Minimum Reward-to-Risk Ratio | $1:1.50$ (Target $1:2.00$) | Locked |
| | Daily Drawdown Circuit Breaker | $5.0\%$ | Fail-Closed |
| | Max Currency Net Exposure | $3.0$ Lots | Fail-Closed |
| | Max Base Spread Filter | $3.0$ Pips | Fail-Closed |
| | Economic Event Blackout Window | $\pm 30$ Minutes | Fail-Closed |
| **Universe & Execution**| Supported Core Assets | 9 Assets (BTC, ETH, EUR, GBP, JPY, AUD, XAU, NAS, SPX) | Locked |
| | Primary Execution Timeframe | 1H (with 4H & 1D Confirmation) | Locked |
| | Execution Simulator Mode | `VIRTUAL_PAPER_SHADOW` | Locked |

---

## 2. Invariance Rule

All parameters, weights, and logic remain strictly frozen. Forward evaluation measures genuine persistence without post-hoc curve fitting.
