import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from app.pipeline.quant_pipeline_orchestrator import QuantPipelineOrchestrator


def generate_sample_candles(count: int = 100, trend: str = "BULLISH"):
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=count)
    dates = [base_time + timedelta(hours=i) for i in range(count)]

    base_price = 1.1000
    records = []
    for i in range(count):
        drift = (i * 0.0003) if trend == "BULLISH" else (-i * 0.0003)
        open_p = base_price + drift + np.random.normal(0, 0.0002)
        close_p = open_p + (0.0004 if trend == "BULLISH" else -0.0004)
        high_p = max(open_p, close_p) + 0.0003
        low_p = min(open_p, close_p) - 0.0003
        records.append({
            "timestamp": dates[i],
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": 1000.0 + (i * 10),
        })
    return pd.DataFrame(records)


def test_master_quant_pipeline_end_to_end_execution():
    orchestrator = QuantPipelineOrchestrator()
    df_primary = generate_sample_candles(count=80, trend="BULLISH")
    df_secondary = df_primary.copy()

    result = orchestrator.execute_pipeline(
        asset="EURUSD",
        df_primary=df_primary,
        df_secondary=df_secondary,
        current_spread_pips=1.0,
        is_event_risk=False,
    )

    assert result.trace_id.startswith("trace-")
    assert len(result.stages) >= 9
    assert result.stages[0].stage_name == "1. LIVE MARKET DATA"
    assert result.stages[1].stage_name == "2. DATA QUALITY"
    assert result.stages[1].status == "PASS"


def test_master_quant_pipeline_fail_closed_on_corrupted_data():
    orchestrator = QuantPipelineOrchestrator()
    df_primary = generate_sample_candles(count=50)
    # Corrupt a candle: Low > High
    df_primary.loc[10, "low"] = 2.0000

    result = orchestrator.execute_pipeline(
        asset="EURUSD",
        df_primary=df_primary,
    )

    assert result.status == "DATA_GATED"
    assert "DATA_QUALITY" in result.no_trade_reason
    assert result.stages[1].status == "HALTED"


def test_master_quant_pipeline_no_trade_on_event_risk():
    orchestrator = QuantPipelineOrchestrator()
    df_primary = generate_sample_candles(count=60, trend="BULLISH")

    result = orchestrator.execute_pipeline(
        asset="EURUSD",
        df_primary=df_primary,
        is_event_risk=True,  # Macro news release active
    )

    assert result.status == "NO_TRADE"
    quality_stage = [s for s in result.stages if "SIGNAL QUALITY" in s.stage_name][0]
    assert "EVENT_RISK" in quality_stage.details.get("rejection_reasons", []) or result.no_trade_reason == "EVENT_RISK"
