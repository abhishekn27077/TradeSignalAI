from app.logs.logger import get_logger
from app.strategies.indicators.base import BaseIndicator

logger = get_logger(__name__)


import numpy as np
import pandas as pd


class RSI(BaseIndicator):
    def __init__(self, period: int = 14):
        super().__init__(name="RSI", params={"period": period})
        if period < 1:
            logger.warning(f"Invalid RSI period: {period}, using default 14")
            period = 14
        self.period = period

    def initialize(self):
        self.is_initialized = True

    def reset(self):
        self.is_initialized = False

    def validate(self) -> bool:
        return self.period > 0

    def calculate(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            return pd.Series(dtype=float)
        
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Avoid division by zero
        rsi = rsi.fillna(100).where(avg_loss != 0, 100)
        # Restore leading NaNs
        rsi.iloc[:self.period] = np.nan
        
        return rsi

    def update(self, new_data: pd.DataFrame):
        pass