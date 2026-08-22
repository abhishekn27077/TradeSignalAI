import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple


class CorrelationEngine:
    """
    Computes rolling cross-asset returns correlation.
    """

    def compute_correlation(self, df_a: pd.DataFrame, df_b: pd.DataFrame, window: int = 20) -> float:
        if df_a is None or df_b is None or len(df_a) < window or len(df_b) < window:
            return 0.0

        try:
            ret_a = df_a['close'].pct_change().dropna().tail(window)
            ret_b = df_b['close'].pct_change().dropna().tail(window)

            min_len = min(len(ret_a), len(ret_b))
            if min_len < 5:
                return 0.0

            corr = np.corrcoef(ret_a.tail(min_len), ret_b.tail(min_len))[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0
        except Exception:
            return 0.0
