# TradeSignalAI-v3 — User Guide

Welcome to the TradeSignalAI-v3 User Guide. This document provides step-by-step instructions for operating the platform.

---

## 1. Dashboard Overview

The web dashboard provides live visibility into system operations:
- **Trading View / Terminal**: View real-time charts, candlestick data, and active indicators.
- **AI Command Center**: Monitor individual AI Agent opinions, confidence scores, and final Consensus decisions.
- **Portfolio & Risk View**: Track open positions, current drawdown, daily PnL, margin utilization, and risk scoring.
- **System Health & Logs**: Real-time status of Database, Redis, OmniRoute, MT5 Broker, and Failsafes.

---

## 2. Operating Modes & Switching

TradeSignalAI-v3 supports two execution modes:

### DEMO Mode (Default)
In `DEMO` mode, orders are routed to your broker's demo server or simulated internally. 
```env
EXECUTION_MODE=DEMO
```

### LIVE Mode
In `LIVE` mode, real capital is deployed. Ensure you have verified strategy performance in DEMO mode first.
```env
EXECUTION_MODE=LIVE
```

> [!WARNING]
> Always verify that your risk parameters (`MAX_DAILY_LOSS_PCT`, `MAX_DRAWDOWN_PCT`) are correctly set in `.env` before running in LIVE mode.

---

## 3. Failsafes & Emergency Controls

- **Emergency Kill Switch**: Can be toggled manually via the Dashboard or API (`POST /api/v1/failsafe/killswitch`). Activating the kill switch immediately blocks all new order entries.
- **Daily Loss Shutdown**: If the net account loss for the day exceeds `MAX_DAILY_LOSS_PCT` (default 3.0%), the system automatically locks out trading until the next trading day.
- **Drawdown Protection**: Reaching `MAX_DRAWDOWN_PCT` triggers an automated kill switch activation.
