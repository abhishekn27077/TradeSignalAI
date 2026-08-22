import asyncio
import httpx
from datetime import datetime, timezone
import json

async def run_validation():
    print("============================================================")
    print("PHASE 30 DATA INTELLIGENCE VALIDATION")
    print("============================================================")
    
    # In a real environment, we'd boot up the FastAPI server via TestClient
    # For script validation, we import the routers directly and mock the requests.
    # To keep it lightweight and zero-trust, we'll validate the functions mathematically.
    
    from app.core.timing import CandleClock, ISTConverter
    from app.forecast_engine.next_signal import NextSignalEngine
    from app.intelligence.time_pattern import HistoricalTimePatternEngine
    
    # 1. Validate IST Converter
    now_utc = datetime(2026, 8, 19, 14, 0, 0, tzinfo=timezone.utc)
    now_ist = ISTConverter.to_ist_string(now_utc)
    print(f"UTC: {now_utc.isoformat()} -> IST: {now_ist}")
    assert "19:30:00 IST" in now_ist, "IST conversion failed"
    
    # 2. Validate CandleClock H4
    status_h4 = CandleClock.get_candle_status("H4", reference_time=now_utc)
    print(f"H4 Candle Status: {json.dumps(status_h4, indent=2)}")
    assert status_h4["timeframe"] == "H4", "Timeframe mismatch"
    assert status_h4["current_candle_open_utc"] == "2026-08-19T12:00:00+00:00", "H4 open failed"
    assert status_h4["current_candle_close_utc"] == "2026-08-19T16:00:00+00:00", "H4 close failed"
    
    # 3. Validate NextSignalEngine
    next_sig = NextSignalEngine.get_next_opportunity("BTCUSD", "H4")
    print(f"Next Signal Engine: {json.dumps(next_sig, indent=2)}")
    assert next_sig["asset"] == "BTCUSD"
    assert next_sig["status"] == "WAITING FOR CANDLE CLOSE"
    
    # 4. Validate Historical Time Pattern (Zero-Trust Unavailable check)
    pattern = HistoricalTimePatternEngine.analyze("EURUSD", current_time=now_utc, timeframe="H4")
    print(f"Historical Pattern: {json.dumps(pattern, indent=2)}")
    assert pattern["bullish_rate"] == "UNAVAILABLE", "Zero-trust rule violated: fake data returned"
    assert pattern["status"] == "INSUFFICIENT HISTORICAL SAMPLE"
    
    print("============================================================")
    print("VALIDATION PASSED: CORE TIMING AND INTELLIGENCE ENGINES ARE ZERO-TRUST COMPLIANT.")
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(run_validation())
