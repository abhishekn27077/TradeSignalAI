
import pandas as pd


class SupportResistanceDetector:
    """
    Identifies key support and resistance levels.
    """
    def __init__(self, window: int = 20):
        self.window = window
        
    def find_levels(self, data: pd.DataFrame) -> dict[str, list[float]]:
        """
        Finds horizontal support and resistance levels using rolling windows.
        """
        levels = {"support": [], "resistance": []}
        if len(data) < self.window:
            return levels
            
        # Simplistic pivot point detection
        data['swing_high'] = data['high'] == data['high'].rolling(window=self.window, center=True).max()
        data['swing_low'] = data['low'] == data['low'].rolling(window=self.window, center=True).min()
        
        levels["resistance"] = data[data['swing_high']]['high'].tolist()[-5:] # Last 5
        levels["support"] = data[data['swing_low']]['low'].tolist()[-5:]
        
        return levels
