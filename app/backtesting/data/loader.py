from datetime import datetime

import pandas as pd


class HistoricalDataLoader:
    """Loads and formats historical data for the simulation engine."""
    
    @staticmethod
    def load_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Stub. In production, this pulls from the Database or MarketData layer.
        For now, returns a dummy dataframe.
        """
        # Create dummy daily data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        df = pd.DataFrame({
            'open': [100.0 + i for i in range(len(dates))],
            'high': [105.0 + i for i in range(len(dates))],
            'low': [95.0 + i for i in range(len(dates))],
            'close': [102.0 + i for i in range(len(dates))],
            'volume': [1000] * len(dates)
        }, index=dates)
        return df
