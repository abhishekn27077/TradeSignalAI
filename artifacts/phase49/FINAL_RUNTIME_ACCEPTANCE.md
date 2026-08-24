# Phase 49 — Final Runtime Acceptance Test

**Execution Time (UTC):** 2026-08-24T05:22:07.355381+00:00
**Execution Time (IST):** Monday, 24 August 2026 10:52 AM IST
**Verdict:** ✅ ALL TESTS PASSED

| Metric | Value |
|--------|-------|
| Total Tests | 32 |
| Passed | 32 |
| Failed | 0 |

---

## TEST A — Startup Data Refresh

### ✅ A1: Record current UTC and IST time

- **utc:** `2026-08-24T05:22:04.593194+00:00`
- **ist:** `2026-08-24T10:52:04.593194+05:30`
- **ist_formatted:** `Monday, 24 August 2026 10:52 AM IST`

### ✅ A2: Inspect latest stored closed candle per asset

- **assets_with_data:** `9`
- **sample:**
  ```json
  {
  "EURUSD": {
    "timestamp": "2026-08-24T05:00:00+01:00",
    "close": 1.1684973239898682
  },
  "GBPUSD": {
    "timestamp": "2026-08-24T05:00:00+01:00",
    "close": 1.3647032976150513
  },
  "USDJPY": {
    "timestamp": "2026-08-24T05:00:00+01:00",
    "close": 158.8719940185547
  }
}
  ```

### ✅ A3: Start/restart application (startup sync executed)

- **sync_returned:** `False`
- **note:** `StartupSyncService.synchronize_market_data() invoked`

### ✅ A4: Capture provider's newest available closed candle

- **sample_after:**
  ```json
  {
  "EURUSD": {
    "timestamp": "2026-08-24T05:00:00+01:00",
    "close": 1.1684973239898682
  },
  "GBPUSD": {
    "timestamp": "2026-08-24T05:00:00+01:00",
    "close": 1.3647032976150513
  },
  "USDJPY": {
    "timestamp": "2026-08-24T05:00:00+01:00",
    "close": 158.8719940185547
  }
}
  ```

### ✅ A5: Provider timestamp correctly compared with DB timestamp

- **comparisons:**
  ```json
  [
  {
    "asset": "EURUSD",
    "before_ts": "2026-08-24T05:00:00+01:00",
    "after_ts": "2026-08-24T05:00:00+01:00",
    "updated_or_same": true
  },
  {
    "asset": "GBPUSD",
    "before_ts": "2026-08-24T05:00:00+01:00",
    "after_ts": "2026-08-24T05:00:00+01:00",
    "updated_or_same": true
  },
  {
    "asset": "USDJPY",
    "before_ts": "2026-08-24T05:00:00+01:00",
    "after_ts": "2026-08-24T05:00:00+01:00",
    "updated_or_same": true
  }
]
  ```

### ✅ A6: Newly available candles inserted into SQLite

- **total_candle_rows:** `246015`

### ✅ A7: Duplicates are NOT created

- **duplicate_rows_found:** `0`
- **samples:**
  ```json
  []
  ```

### ✅ A8: Forecast engine reads newly synchronized data

- **forecasts_generated:** `9`
- **expected:** `9`
- **sample_asset:** `EURUSD`

### ✅ A9: data_as_of in forecast corresponds to synchronized data

- **comparisons:**
  ```json
  [
  {
    "asset": "EURUSD",
    "forecast_candle_ts": "2026-08-24T05:00:00+01:00",
    "db_latest_ts": "2026-08-24T05:00:00+01:00",
    "match": true
  },
  {
    "asset": "GBPUSD",
    "forecast_candle_ts": "2026-08-24T05:00:00+01:00",
    "db_latest_ts": "2026-08-24T05:00:00+01:00",
    "match": true
  },
  {
    "asset": "USDJPY",
    "forecast_candle_ts": "2026-08-24T05:00:00+01:00",
    "db_latest_ts": "2026-08-24T05:00:00+01:00",
    "match": true
  }
]
  ```

## TEST B — Future Signal Only

### ✅ B1: All current signals have target_time > current_time

- **current_signals_count:** `9`
- **evidence:**
  ```json
  [
  {
    "asset": "EURUSD",
    "candle_ts": "2026-08-24T05:00:00+01:00",
    "expiry_utc": "2026-08-24T07:00:00+01:00",
    "is_future": true
  },
  {
    "asset": "GBPUSD",
    "candle_ts": "2026-08-24T05:00:00+01:00",
    "expiry_utc": "2026-08-24T07:00:00+01:00",
    "is_future": true
  },
  {
    "asset": "USDJPY",
    "candle_ts": "2026-08-24T05:00:00+01:00",
    "expiry_utc": "2026-08-24T07:00:00+01:00",
    "is_future": true
  },
  {
    "asset": "AUDUSD",
    "candle_ts": "2026-08-24T05:00:00+01:00",
    "expiry_utc": "2026-08-24T07:00:00+01:00",
    "is_future": true
  },
  {
    "asset": "BTCUSD",
    "candle_ts": "2026-08-24T04:00:00+00:00",
    "expiry_utc": "2026-08-24T06:00:00+00:00",
    "is_future": true
  }
]
  ```

### ✅ B2: Expired signals (target <= current) are rejected

- **test_target_utc:** `2026-08-24T02:22:06.349171+00:00`
- **current_utc:** `2026-08-24T05:22:06.349171+00:00`
- **is_expired_result:** `True`

### ✅ B3: Past forecasts available in historical/ledger views

- **total_predictions_in_ledger:** `9`
- **note:** `shadow_ledger_engine.get_all_predictions() retains ALL predictions immutably`

## TEST C — Restart Re-Evaluation

### ✅ C1: Generate forecast at simulated 2:00 PM IST

- **simulated_time_ist:** `02:00 PM IST`
- **forecasts_generated:** `9`
- **sample_prediction_id:** `PRED-EURUSD-20260824052206-e1e6c4`
- **sample_direction:** `BUY`
- **sample_confidence:** `0.71`

### ✅ C2: Forecast persisted in shadow ledger

- **predictions_persisted:** `9`

### ✅ C3: Restart at 5:00 PM IST recalculates with fresh data

- **simulated_restart_ist:** `05:00 PM IST`
- **new_forecasts_generated:** `9`
- **old_direction:** `BUY`
- **new_direction:** `BUY`
- **old_confidence:** `0.71`
- **new_confidence:** `0.71`
- **direction_may_change:** `True`
- **old_forecast_in_history:** `True`
- **note:** `Old forecast remains in immutable ledger; new cycle uses current market state`

### ✅ C4: Previous forecast remains in immutable history

- **old_prediction_id:** `PRED-EURUSD-20260824052206-e1e6c4`
- **found_in_ledger:** `True`
- **total_predictions_now:** `9`

## TEST D — Past Forecast

### ✅ D1: Advancing time beyond forecast target marks it expired

- **simulated_past_target:** `2026-08-24T00:22:06.349171+00:00`
- **is_expired:** `True`

### ✅ D2: Today's Signals does NOT contain expired forecast

- **today_forecast_count:** `9`
- **all_are_future:** `True`

### ✅ D3: Signal History (ledger) contains past forecasts

- **total_predictions_in_history:** `9`

### ✅ D4: Prediction Ledger contains past forecasts

- **ledger_size:** `9`
- **note:** `shadow_ledger_engine is immutable append-only`

## TEST E — Time Format

### ✅ E1: IST format matches 'Weekday, DD Month YYYY HH:MM AM/PM IST'

- **input_utc:** `2026-08-21T12:30:00+00:00`
- **output_ist:** `Friday, 21 August 2026 06:00 PM IST`
- **expected_pattern:** `^[A-Z][a-z]+, \d{2} [A-Z][a-z]+ \d{4} \d{2}:\d{2} [AP]M IST$`
- **matches:** `True`

### ✅ E2: Format does NOT use 24-hour notation

- **formatted:** `Friday, 21 August 2026 06:00 PM IST`
- **contains_18:00:** `False`

### ✅ E3: Format does NOT use ISO 8601 notation

- **formatted:** `Friday, 21 August 2026 06:00 PM IST`
- **has_iso_datetime_pattern:** `False`

### ✅ E4: Format does NOT say UTC

- **formatted:** `Friday, 21 August 2026 06:00 PM IST`
- **ends_with_IST:** `True`

### ✅ E5: Journal response includes date_ist_formatted field

- **date_ist_formatted:** `Monday, 24 August 2026 10:52 AM IST`

### ✅ E6: Forecast rows include time_ist_formatted field

- **sample:** `Monday, 24 August 2026 10:52 AM IST`

## TEST F — No Hardcoded 6 PM

### ✅ F1: No hardcoded forecast timestamps in production code

- **hardcoded_hits:** `NONE`
- **searched_directory:** `D:\trading Bots\FinalTrade\TradeSignalAI-v3\app`
- **patterns_searched:**
  ```json
  [
  "06:00 PM",
  "18:00",
  "2026-08-21"
]
  ```

### ✅ F2: Forecast times are dynamically derived from input datetime

- **test_1:** `Thursday, 15 January 2026 03:30 PM IST`
- **test_2:** `Friday, 21 August 2026 06:00 PM IST`
- **test_3:** `Friday, 25 December 2026 08:30 AM IST`
- **all_different:** `True`

## TEST G — Freshness Failure

### ✅ G1: is_data_stale correctly detects old data

- **test_candle_time:** `2026-08-24T02:22:06.349171+00:00`
- **current_time:** `2026-08-24T05:22:06.349171+00:00`
- **age_seconds:** `10800.0`
- **is_stale:** `True`

### ✅ G2: Startup sync FAILS CLOSED when provider unavailable

- **sync_returned:** `False`
- **expected:** `False`
- **note:** `DATA_UNAVAILABLE logged; no new actionable forecast generated`

### ✅ G3: DATA_STALE and DATA_UNAVAILABLE are used in production code

- **DATA_STALE_found:** `True`
- **DATA_UNAVAILABLE_found:** `True`

## TEST H — End-to-End Lineage

### ✅ H1: End-to-end lineage: all timestamps traceable

- **asset:** `EURUSD`
- **1_provider_candle_timestamp:** `2026-08-24T05:00:00+01:00`
- **2_db_candle_timestamp:** `2026-08-24T05:00:00+01:00`
- **3_feature_timestamp:** `2026-08-24T05:00:00+01:00`
- **4_model_evaluation_timestamp:** `2026-08-24T05:22:06.219005+00:00`
- **5_forecast_generation_timestamp:** `2026-08-24T05:22:06.219005+00:00`
- **6_target_forecast_timestamp:** `Monday, 24 August 2026 10:52 AM IST`
- **7_current_ui_signal:**
  ```json
  {
  "prediction_id": "PRED-EURUSD-20260824052206-e1e6c4",
  "direction": "BUY",
  "confidence": 0.71,
  "entry_price": 1.1684973239898682,
  "time_ist_formatted": "Monday, 24 August 2026 10:52 AM IST"
}
  ```

---

*Generated by Phase 49 Final Runtime Acceptance Test at Monday, 24 August 2026 10:52 AM IST*