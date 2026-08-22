import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

from app.strategies.Technical.indicators import compute_atr


def compute_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0
) -> Tuple[pd.Series, pd.Series]:
    """
    Computes SuperTrend indicator (Trend Band & Direction).
    Direction: 1 for Bullish, -1 for Bearish.
    Operates strictly on confirmed closed candles (no lookahead / non-repainting).
    """
    hl2 = (df['high'] + df['low']) / 2.0
    atr = compute_atr(df, period=period)

    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)

    n = len(df)
    final_upper = np.zeros(n)
    final_lower = np.zeros(n)
    supertrend = np.zeros(n)
    direction = np.ones(n, dtype=int)  # 1: Bullish, -1: Bearish

    close = df['close'].values

    for i in range(1, n):
        # Final Upper Band
        if basic_upper.iloc[i] < final_upper[i - 1] or close[i - 1] > final_upper[i - 1]:
            final_upper[i] = basic_upper.iloc[i]
        else:
            final_upper[i] = final_upper[i - 1]

        # Final Lower Band
        if basic_lower.iloc[i] > final_lower[i - 1] or close[i - 1] < final_lower[i - 1]:
            final_lower[i] = basic_lower.iloc[i]
        else:
            final_lower[i] = final_lower[i - 1]

        # SuperTrend Value & Direction
        if direction[i - 1] == 1:
            if close[i] < final_lower[i]:
                direction[i] = -1
                supertrend[i] = final_upper[i]
            else:
                direction[i] = 1
                supertrend[i] = final_lower[i]
        else:
            if close[i] > final_upper[i]:
                direction[i] = 1
                supertrend[i] = final_lower[i]
            else:
                direction[i] = -1
                supertrend[i] = final_upper[i]

    return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)
