
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
            
        # Non-lookahead pivot point detection: confirmed with half_w lag
        half_w = max(1, self.window // 2)
        roll_max = data['high'].rolling(window=self.window).max()
        data['swing_high'] = (data['high'].shift(half_w) == roll_max)

        roll_min = data['low'].rolling(window=self.window).min()
        data['swing_low'] = (data['low'].shift(half_w) == roll_min)

        levels["resistance"] = data[data['swing_high']]['high'].tolist()[-5:] # Last 5
        levels["support"] = data[data['swing_low']]['low'].tolist()[-5:]
        
        return levels
