# Phase 72 — Model Drift & Automated Degradation Report
**Current System Drift Status**: **DEGRADED** | **Risk Multiplier**: 0.5x
**Recommended Action**: `REDUCE_RISK_50_PCT`

## 1. Directional & Feature Skew Monitor

- **Signals Audited**: 84
- **BUY Count**: 70 (83.3%)
- **SELL Count**: 12
- **NO_TRADE Count**: 0
- **Directional Skew Deviation**: 33.3%

## 2. Performance Degradation Monitor

- **Resolved Sample**: 65
- **Rolling Win Rate**: 81.5%

## 3. Automated Safety Invariants
- If rolling win rate drops below 45% -> System transitions to `DEGRADED` (0.5x risk)
- If rolling win rate drops below 30% or skew exceeds 80% -> System transitions to `CRITICAL` (Hard NO_TRADE lockout)