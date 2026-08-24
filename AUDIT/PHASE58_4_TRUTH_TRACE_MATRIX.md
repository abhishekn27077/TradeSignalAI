# PHASE 58.4 — DB ↔ SERVICE ↔ API ↔ UI TRUTH TRACE MATRIX

**Project:** TradeSignalAI-v3  
**Frozen Configuration Hash:** `79a4f8e12b79310d`  
**Purpose:** Forensic end-to-end trace of 5 Forecasts, 5 Signals, 5 Trades, and 5 Historical Outcomes from SQLite to Frontend.  

---

## 1. Forecasts Trace Matrix (5 Assets)

| Trace ID | Asset | Database Table & Key | Canonical Service Generator | API Endpoint & Payload Key | UI Component & Render Location | Parity Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FC-01** | `BTCUSD` | `forecast_results` (asset='BTCUSD') | `TomorrowForecastEngine._generate_asset_forecast` | `GET /api/v1/forecasts/tomorrow` -> `data.forecasts[BTCUSD]` | `TomorrowForecast.tsx` / Live Forecast Strip | **VERIFIED (Match)** |
| **FC-02** | `ETHUSD` | `forecast_results` (asset='ETHUSD') | `TomorrowForecastEngine._generate_asset_forecast` | `GET /api/v1/forecasts/tomorrow` -> `data.forecasts[ETHUSD]` | `TomorrowForecast.tsx` / Live Forecast Strip | **VERIFIED (Match)** |
| **FC-03** | `EURUSD` | `forecast_results` (asset='EURUSD') | `TomorrowForecastEngine._generate_asset_forecast` | `GET /api/v1/forecasts/tomorrow` -> `data.forecasts[EURUSD]` | `TomorrowForecast.tsx` / Analytical Forecasts Tab | **VERIFIED (Match)** |
| **FC-04** | `GBPUSD` | `forecast_results` (asset='GBPUSD') | `TomorrowForecastEngine._generate_asset_forecast` | `GET /api/v1/forecasts/tomorrow` -> `data.forecasts[GBPUSD]` | `TomorrowForecast.tsx` / Analytical Forecasts Tab | **VERIFIED (Match)** |
| **FC-05** | `XAUUSD` | `forecast_results` (asset='XAUUSD') | `TomorrowForecastEngine._generate_asset_forecast` | `GET /api/v1/forecasts/tomorrow` -> `data.forecasts[XAUUSD]` | `TomorrowForecast.tsx` / Analytical Forecasts Tab | **VERIFIED (Match)** |

---

## 2. Signals Trace Matrix (5 Setup Scenarios)

| Trace ID | Scenario / Asset | Database Table & Key | Canonical Service Evaluator | API Endpoint & Payload Key | UI Component & Render Location | Parity Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SIG-01** | Open Market High Conf (`BTCUSD`) | `signal_lifecycle` (status='ACTIVE') | `CanonicalDecisionEngine.evaluate_setup` | `GET /api/v1/signals/today` -> `items[]` | `TodaysSignals.tsx` (Qualified Signals Tab) | **VERIFIED (Match)** |
| **SIG-02** | Weekend Forex (`EURUSD`) | `decision_history` (decision='NO_TRADE') | `MarketSessionService` + Decision Engine | `GET /api/v1/signals/today` -> `[]` (Filtered) | `TodaysSignals.tsx` ("0 Signals Active") | **VERIFIED (Match)** |
| **SIG-03** | Low Confluence (`USDJPY`) | `decision_history` (reason='LOW_CONFIDENCE')| `CanonicalDecisionEngine.evaluate_setup` | `GET /api/v1/signals/today` -> `[]` (Filtered) | `TodaysSignals.tsx` ("0 Signals Active") | **VERIFIED (Match)** |
| **SIG-04** | High News Spike (`NAS100`)| `decision_history` (reason='HIGH_EVENT_RISK')| `EconomicCalendarEngine` + Decision Engine| `GET /api/v1/signals/today` -> `[]` (Filtered) | `TodaysSignals.tsx` ("0 Signals Active") | **VERIFIED (Match)** |
| **SIG-05** | Swing Setup (`ETHUSD Daily`)| `signal_lifecycle` (timeframe='1D') | `SwingSignalEngine.evaluate_swing` | `GET /api/v1/signals/swing` -> `items[]` | `SwingSignals.tsx` (Swing Intelligence) | **VERIFIED (Match)** |

---

## 3. Paper Trades Trace Matrix (5 Active / Reconciled Trades)

| Trace ID | Asset / Direction | Database Table & Key | Managing Service | API Endpoint & Payload Key | UI Component & Render Location | Parity Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TRD-01** | `BTCUSD BUY` (Entry: 60000) | `paper_orders` (order_id='PT-BTC-01') | `ShadowLedgerEngine._paper_trades` | `GET /api/v1/trades/open` -> `trades[]` | `TradingDashboard.tsx` (Open Positions Card) | **VERIFIED (Match)** |
| **TRD-02** | `ETHUSD SELL` (Entry: 2800) | `paper_orders` (order_id='PT-ETH-01') | `ShadowLedgerEngine._paper_trades` | `GET /api/v1/trades/open` -> `trades[]` | `TradingDashboard.tsx` (Open Positions Card) | **VERIFIED (Match)** |
| **TRD-03** | `EURUSD BUY` (Entry: 1.0800) | `paper_orders` (order_id='PT-EUR-01') | `TradeReconciliationService` | `GET /api/v1/trades/open` -> `trades[]` | `TradingDashboard.tsx` (Open Positions Card) | **VERIFIED (Match)** |
| **TRD-04** | `GBPUSD BUY` (Entry: 1.2900) | `paper_orders` (order_id='PT-GBP-01') | `TradeReconciliationService` | `GET /api/v1/trades/open` -> `trades[]` | `TradingDashboard.tsx` (Open Positions Card) | **VERIFIED (Match)** |
| **TRD-05** | `XAUUSD BUY` (Entry: 2400.0)| `paper_orders` (order_id='PT-XAU-01') | `TradeReconciliationService` | `GET /api/v1/trades/open` -> `trades[]` | `TradingDashboard.tsx` (Open Positions Card) | **VERIFIED (Match)** |

---

## 4. Historical Outcomes Trace Matrix (5 Settled Trades)

| Trace ID | Trade ID / Outcome | Database Table & Key | Reconciliation Engine | API Endpoint & Payload Key | UI Component & Render Location | Parity Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OUT-01** | `PT-EUR-01 (TP_HIT, +1.96R)` | `signal_lifecycle` (status='TP_HIT') | `TradeReconciliationService.replay_trade` | `GET /api/v1/signals/history` -> `items[]` | `SignalHistory.tsx` / Phase 43 Ledger | **VERIFIED (Match)** |
| **OUT-02** | `PT-GBP-01 (SL_HIT, -1.04R)` | `signal_lifecycle` (status='SL_HIT') | `TradeReconciliationService.replay_trade` | `GET /api/v1/signals/history` -> `items[]` | `SignalHistory.tsx` / Phase 43 Ledger | **VERIFIED (Match)** |
| **OUT-03** | `PT-JPY-01 (TIME_EXIT, -0.03R)`| `signal_lifecycle` (status='TIME_EXIT')| `TradeReconciliationService.replay_trade` | `GET /api/v1/signals/history` -> `items[]` | `SignalHistory.tsx` / Phase 43 Ledger | **VERIFIED (Match)** |
| **OUT-04** | `PT-XAU-01 (AMBIGUOUS, -0.04R)`| `signal_lifecycle` (status='AMBIGUOUS')| `TradeReconciliationService.replay_trade` | `GET /api/v1/signals/history` -> `items[]` | `SignalHistory.tsx` / Phase 43 Ledger | **VERIFIED (Match)** |
| **OUT-05** | `PT-BTC-01 (TP_HIT, +1.94R)` | `signal_lifecycle` (status='TP_HIT') | `TradeReconciliationService.replay_trade` | `GET /api/v1/signals/history` -> `items[]` | `SignalHistory.tsx` / Phase 43 Ledger | **VERIFIED (Match)** |
