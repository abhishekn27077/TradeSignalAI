# 05 — Asset Registry Audit & Multi-Class Coverage
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Monitored Multi-Asset Universe
TradeSignalAI-v3 monitors 9 tier-1 global instruments across 4 major financial asset classes:

| Asset Class | Symbol | Decimals | Tick Size | Minimum R:R Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **Crypto** | `BTCUSD` | 2 | 0.01 | $\ge 1.50$ |
| **Crypto** | `ETHUSD` | 2 | 0.01 | $\ge 1.50$ |
| **Forex** | `EURUSD` | 5 | 0.00001 | $\ge 1.50$ |
| **Forex** | `USDJPY` | 3 | 0.001 | $\ge 1.50$ |
| **Forex** | `GBPUSD` | 5 | 0.00001 | $\ge 1.50$ |
| **Forex** | `AUDUSD` | 5 | 0.00001 | $\ge 1.50$ |
| **Commodities** | `XAUUSD` | 2 | 0.01 | $\ge 1.50$ |
| **Indices** | `NAS100` | 2 | 0.01 | $\ge 1.50$ |
| **Indices** | `SPX500` | 2 | 0.01 | $\ge 1.50$ |

---

## 2. Registry Health & Configuration
- All 9 assets have dedicated historical cache stores in SQLite database.
- Precision formatters correctly map currency decimals (5 decimals for EUR/USD, 3 for USD/JPY, 2 for BTC/Gold).
- Status: **PASSED & SYNCHRONIZED**.
