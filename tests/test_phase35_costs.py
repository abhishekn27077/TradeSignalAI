import pytest
from app.execution.evidence_ledger import evidence_ledger

def test_cost_deduction():
    signal_mock = {
        "signal_id": "sig-123",
        "trace_id": "trace-456",
        "asset": "BTCUSD",
        "timeframe": "H4",
        "created_at": "2026-08-14T10:00:00Z",
        "direction": "BUY",
        "confidence": 85.0,
        "entry_price": 60000.0,
        "stop_loss": 59000.0,
        "take_profit_1": 62000.0,
        "ablation_mode": "MODE_B"
    }
    
    outcome_mock = {
        "exit_price": 62000.0,
        "exit_time": "2026-08-15T10:00:00Z",
        "outcome": "TAKE_PROFIT",
        "gross_pnl": 2000.0,
        "spread_cost": 50.0,
        "slippage_cost": 25.0,
        "fees_cost": 10.0,
        "net_pnl": 1915.0, # 2000 - 50 - 25 - 10
        "r_multiple": 1.91
    }
    
    record = evidence_ledger.build_phase29_compatible_record(signal_mock, outcome_mock)
    
    assert record["gross_pnl"] == 2000.0
    assert record["spread_cost"] == 50.0
    assert record["slippage_cost"] == 25.0
    assert record["fees_cost"] == 10.0
    assert record["net_pnl"] == 1915.0
    assert record["R"] == 1.91
    assert record["ablation_mode"] == "MODE_B"
