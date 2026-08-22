import pytest
import pandas as pd
from app.analytics.ablation_tracker import ablation_tracker

def test_confidence_calibration():
    # Synthetic data spanning confidence bins
    data = {
        "ablation_mode": ["MODE_A"] * 6,
        "net_pnl": [10.0, -10.0, 10.0, 10.0, -10.0, 10.0],
        "R": [1.0, -1.0, 1.0, 1.0, -1.0, 1.0],
        "confidence": [55, 59, 65, 75, 85, 95], # Bins: <60, <60, 60-70, 70-80, 80-90, 90+
        "generated_at": ["2026-08-14T10:00:00Z"] * 6
    }
    df = pd.DataFrame(data)
    
    metrics = ablation_tracker._compute_metrics(df)
    
    calib = metrics["MODE_A"]["confidence_calibration"]
    
    assert calib["<60"]["trades"] == 2
    assert calib["<60"]["win_rate"] == 50.0
    
    assert calib["60-70"]["trades"] == 1
    assert calib["60-70"]["win_rate"] == 100.0
    
    assert calib["70-80"]["trades"] == 1
    assert calib["70-80"]["win_rate"] == 100.0
    
    assert calib["80-90"]["trades"] == 1
    assert calib["80-90"]["win_rate"] == 0.0
    
    assert calib["90+"]["trades"] == 1
    assert calib["90+"]["win_rate"] == 100.0
