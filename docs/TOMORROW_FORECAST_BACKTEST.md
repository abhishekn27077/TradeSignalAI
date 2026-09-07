# Tomorrow Forecast Point-in-Time (PIT) Backtest Report
**Evaluation Window**: 20 Days | **Total Forecasts**: 145
**Directional Accuracy**: 48.0% | **Mean Brier Score**: 0.274 | **Net Realized R**: -4.0R

## 1. Point-in-Time Simulation Trace Matrix

| Freeze Date (D-1) | Target Date (D) | Asset | Projected Dir | Confidence | Actual Return | Actual Dir | Result | Realized R | Catalyst |
|---|---|---|---|---|---|---|---|---|---|
| 2026-08-01 | 2026-08-02 | BTCUSD | **SELL** | 0.71 | +1.172% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-01 | 2026-08-02 | ETHUSD | **WAIT** | 0.54 | +2.178% | BUY | CORRECT | +0.0R | NONE_VERIFIED |
| 2026-08-01 | 2026-08-02 | XAUUSD | **SELL** | 0.71 | -0.269% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-01 | 2026-08-02 | NAS100 | **SELL** | 0.71 | +0.257% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-01 | 2026-08-02 | SPX500 | **SELL** | 0.71 | +0.116% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-02 | 2026-08-03 | EURUSD | **SELL** | 0.71 | -0.357% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-02 | 2026-08-03 | GBPUSD | **SELL** | 0.71 | -0.478% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-02 | 2026-08-03 | USDJPY | **WAIT** | 0.54 | +0.037% | BUY | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-02 | 2026-08-03 | AUDUSD | **WAIT** | 0.54 | -0.665% | SELL | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-02 | 2026-08-03 | BTCUSD | **SELL** | 0.71 | -0.059% | SELL | CORRECT | +1.0R | NONE_VERIFIED |
| 2026-08-02 | 2026-08-03 | ETHUSD | **WAIT** | 0.54 | -1.301% | SELL | CORRECT | +0.0R | NONE_VERIFIED |
| 2026-08-02 | 2026-08-03 | XAUUSD | **SELL** | 0.71 | -0.296% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-02 | 2026-08-03 | NAS100 | **SELL** | 0.71 | +1.167% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-02 | 2026-08-03 | SPX500 | **SELL** | 0.71 | +1.101% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-03 | 2026-08-04 | EURUSD | **SELL** | 0.71 | +0.196% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-03 | 2026-08-04 | GBPUSD | **SELL** | 0.71 | +0.151% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-03 | 2026-08-04 | USDJPY | **WAIT** | 0.54 | +0.240% | BUY | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-03 | 2026-08-04 | AUDUSD | **WAIT** | 0.54 | +0.705% | BUY | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-03 | 2026-08-04 | BTCUSD | **SELL** | 0.71 | +0.906% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-03 | 2026-08-04 | ETHUSD | **WAIT** | 0.54 | +0.507% | BUY | CORRECT | +0.0R | NONE_VERIFIED |
| 2026-08-03 | 2026-08-04 | XAUUSD | **SELL** | 0.71 | +1.928% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-03 | 2026-08-04 | NAS100 | **SELL** | 0.71 | +3.102% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-03 | 2026-08-04 | SPX500 | **SELL** | 0.71 | +1.936% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-04 | 2026-08-05 | EURUSD | **SELL** | 0.71 | +0.196% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-04 | 2026-08-05 | GBPUSD | **SELL** | 0.71 | +0.116% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-04 | 2026-08-05 | USDJPY | **WAIT** | 0.54 | -0.039% | SELL | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-04 | 2026-08-05 | AUDUSD | **WAIT** | 0.54 | +0.120% | BUY | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-04 | 2026-08-05 | BTCUSD | **SELL** | 0.71 | +0.869% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-04 | 2026-08-05 | ETHUSD | **WAIT** | 0.54 | +2.086% | BUY | CORRECT | +0.0R | NONE_VERIFIED |
| 2026-08-04 | 2026-08-05 | XAUUSD | **SELL** | 0.71 | +3.316% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-04 | 2026-08-05 | NAS100 | **SELL** | 0.71 | -1.113% | SELL | CORRECT | +1.0R | NONE_VERIFIED |
| 2026-08-04 | 2026-08-05 | SPX500 | **SELL** | 0.71 | -0.398% | SELL | CORRECT | +1.0R | NONE_VERIFIED |
| 2026-08-05 | 2026-08-06 | EURUSD | **SELL** | 0.71 | -0.288% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-05 | 2026-08-06 | GBPUSD | **SELL** | 0.71 | -0.114% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-05 | 2026-08-06 | USDJPY | **WAIT** | 0.54 | +0.508% | BUY | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-05 | 2026-08-06 | AUDUSD | **WAIT** | 0.54 | -0.394% | SELL | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-05 | 2026-08-06 | BTCUSD | **SELL** | 0.71 | -0.521% | SELL | CORRECT | +1.0R | NONE_VERIFIED |
| 2026-08-05 | 2026-08-06 | ETHUSD | **WAIT** | 0.54 | -0.279% | SELL | CORRECT | +0.0R | NONE_VERIFIED |
| 2026-08-05 | 2026-08-06 | XAUUSD | **SELL** | 0.71 | -0.039% | SELL | CORRECT | +1.0R | Economic Release (USD) |
| 2026-08-05 | 2026-08-06 | NAS100 | **SELL** | 0.71 | -0.278% | SELL | CORRECT | +1.0R | NONE_VERIFIED |
| 2026-08-05 | 2026-08-06 | SPX500 | **SELL** | 0.71 | -0.435% | SELL | CORRECT | +1.0R | NONE_VERIFIED |
| 2026-08-06 | 2026-08-07 | EURUSD | **SELL** | 0.71 | +0.312% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-06 | 2026-08-07 | GBPUSD | **SELL** | 0.71 | +0.301% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-06 | 2026-08-07 | USDJPY | **WAIT** | 0.54 | -0.446% | SELL | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-06 | 2026-08-07 | AUDUSD | **WAIT** | 0.54 | +0.537% | BUY | CORRECT | +0.0R | Economic Release (USD) |
| 2026-08-06 | 2026-08-07 | BTCUSD | **SELL** | 0.71 | +0.980% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-06 | 2026-08-07 | ETHUSD | **WAIT** | 0.54 | +0.585% | BUY | CORRECT | +0.0R | NONE_VERIFIED |
| 2026-08-06 | 2026-08-07 | XAUUSD | **SELL** | 0.71 | +1.720% | BUY | INCORRECT | -1.0R | Economic Release (USD) |
| 2026-08-06 | 2026-08-07 | NAS100 | **SELL** | 0.71 | +1.148% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |
| 2026-08-06 | 2026-08-07 | SPX500 | **SELL** | 0.71 | +0.647% | BUY | INCORRECT | -1.0R | NONE_VERIFIED |

## 2. Point-in-Time (PIT) Safety Certification
Zero lookahead verified: Forecasts generated at D-1 23:59:59 strictly access candle data up to T0. Actual next-day market outcomes are evaluated only on Day D close.