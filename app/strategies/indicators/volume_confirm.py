from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class VolumeConfirmationEngine:
    """
    Checks for volume spikes to confirm breakouts, BOS, or Order Block formation.
    """
    def __init__(self, volume_ma_period=20, surge_multiplier=1.5):
        self.ma_period = volume_ma_period
        self.multiplier = surge_multiplier

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if 'volume' not in df.columns or len(df) < self.ma_period:
            return {"volume_surge": False, "volume_ratio": 1.0}
            
        vol = df['volume']
        vol_ma = vol.rolling(window=self.ma_period).mean()
        
        current_vol = vol.iloc[-1]
        current_ma = vol_ma.iloc[-1]
        
        if current_ma == 0:
            return {"volume_surge": False, "volume_ratio": 1.0}
            
        ratio = current_vol / current_ma
        
        return {
            "volume_surge": ratio >= self.multiplier,
            "volume_ratio": ratio,
            "average_volume": current_ma
        }

volume_engine = VolumeConfirmationEngine()
