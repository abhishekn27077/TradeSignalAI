import pandas as pd
import numpy as np
from typing import Tuple

from app.strategies.Technical.indicators import compute_atr


def compute_ut_bot(
    df: pd.DataFrame,
    key_value: float = 1.0,
    atr_period: int = 10
) -> Tuple[pd.Series, pd.Series]:
    """
    Computes UT Bot ATR Trailing Stop and Direction.
    key_value: Sensitivity parameter.
    Returns (trailing_stop_series, position_series) where position is 1 (Long) or -1 (Short).
    """
    atr = compute_atr(df, period=atr_period)
    n_loss = key_value * atr
    close = df['close'].values

    n = len(df)
    trailing_stop = np.zeros(n)
    pos = np.ones(n, dtype=int)

    for i in range(1, n):
        prev_stop = trailing_stop[i - 1]
        curr_loss = n_loss.iloc[i]

        if close[i] > prev_stop:
            curr_stop = max(prev_stop, close[i] - curr_loss)
            pos[i] = 1
        else:
            curr_stop = min(prev_stop, close[i] + curr_loss)
            pos[i] = -1

        # Trend flip checks
        if close[i] > prev_stop and close[i - 1] <= prev_stop:
            curr_stop = close[i] - curr_loss
            pos[i] = 1
        elif close[i] < prev_stop and close[i - 1] >= prev_stop:
            curr_stop = close[i] + curr_loss
            pos[i] = -1

        trailing_stop[i] = curr_stop

    return pd.Series(trailing_stop, index=df.index), pd.Series(pos, index=df.index)
