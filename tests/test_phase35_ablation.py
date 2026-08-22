import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.analytics.ablation_tracker import ablation_tracker

def test_ablation_metrics_computation():
    # Create synthetic outcomes_df
    data = {
        "ablation_mode": ["MODE_A", "MODE_A", "MODE_B", "MODE_C", "MODE_C"],
        "net_pnl": [10.5, -5.2, 15.0, -10.0, -5.0],
        "R": [1.5, -1.0, 2.0, -1.0, -0.5],
        "confidence": [65, 85, 75, 55, 95],
        "generated_at": [
            "2026-08-14T10:00:00Z", # Friday
            "2026-08-14T14:00:00Z", # Friday
            "2026-08-17T10:00:00Z", # Monday
            "2026-08-17T14:00:00Z", # Monday
            "2026-08-18T10:00:00Z"  # Tuesday
        ]
    }
    df = pd.DataFrame(data)
    
    metrics = ablation_tracker._compute_metrics(df)
    
    assert "MODE_A" in metrics
    assert "MODE_B" in metrics
    assert "MODE_C" in metrics
    
    # MODE A Check
    assert metrics["MODE_A"]["trades"] == 2
    assert metrics["MODE_A"]["wins"] == 1
    assert metrics["MODE_A"]["losses"] == 1
    assert metrics["MODE_A"]["win_rate"] == 50.0
    
    # Calibration check for MODE_A
    calib = metrics["MODE_A"]["confidence_calibration"]
    assert calib["60-70"]["trades"] == 1 # 65
    assert calib["60-70"]["win_rate"] == 100.0 # It won (10.5)
    
    assert calib["80-90"]["trades"] == 1 # 85
    assert calib["80-90"]["win_rate"] == 0.0 # It lost (-5.2)
    
    # Friday Monday check for MODE_A
    fm_stats = metrics["MODE_A"]["friday_monday_study"]
    assert fm_stats["friday"]["trades"] == 2
    assert fm_stats["monday"]["trades"] == 0
