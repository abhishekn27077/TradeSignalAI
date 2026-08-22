"""
app/intelligence/faiss_memory.py  — Phase 33
=============================================
FAISSMemoryEngine: real historical analog retrieval using FAISS vector search.
Phase 33 enhancements: complete trace output with explicit leak check.
"""
import numpy as np
import pandas as pd
import faiss
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.analytics.feature_engine import FeatureEngine
from app.market_data.service import market_service
from app.market_data.registry import asset_registry

logger = logging.getLogger(__name__)

# Status constants (zero-trust)
STATUS_VALID       = "VALID"
STATUS_UNAVAILABLE = "UNAVAILABLE"


class FAISSMemoryEngine:
    def __init__(self):
        self.indices: Dict[str, faiss.IndexFlatL2] = {}
        self.metadata: Dict[str, pd.DataFrame] = {}
        # We index only these features (must match FeatureEngine output)
        self.feature_cols = [
            'RSI_14', 'MACD', 'MACD_signal', 'ATR_14',
            'BB_high', 'BB_low', 'Momentum_10', 'ROC_10'
        ]

    async def build_index(self, symbol: str, timeframe: str = "H1", count: int = 1500):
        """
        Downloads real historical data, computes features, and indexes them.
        """
        logger.info(f"Building FAISS Index for {symbol} ({timeframe}) using {count} candles...")
        rates = await market_service.get_rates(symbol, timeframe, count=count)

        if not rates or len(rates) < 100:
            logger.error(f"Insufficient historical data to build FAISS index for {symbol}")
            return False

        df = pd.DataFrame(rates)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

        for drop_col in ('symbol', 'timeframe'):
            if drop_col in df.columns:
                df.drop(columns=[drop_col], inplace=True)

        df = FeatureEngine.add_all_features(df)
        df.dropna(inplace=True)

        if df.empty:
            logger.error(f"DataFrame empty after feature generation for {symbol}")
            return False

        missing = [col for col in self.feature_cols if col not in df.columns]
        if missing:
            logger.error(f"Missing feature columns: {missing}")
            return False

        feature_matrix = df[self.feature_cols].values.astype('float32')

        # Forward return: 5 periods ahead
        df['forward_return_5'] = df['close'].shift(-5) / df['close'] - 1
        df = df.iloc[:-5]
        feature_matrix = feature_matrix[:-5]

        # Standardize
        means = np.mean(feature_matrix, axis=0)
        stds = np.std(feature_matrix, axis=0) + 1e-8

        df_meta = df.copy()
        df_meta['faiss_mean'] = [means] * len(df)
        df_meta['faiss_std'] = [stds] * len(df)

        normalized_features = (feature_matrix - means) / stds

        dimension = normalized_features.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(normalized_features)

        key = f"{symbol}_{timeframe}"
        self.indices[key] = index
        self.metadata[key] = df_meta

        logger.info(f"FAISS index built for {key}: {index.ntotal} vectors indexed.")
        return True

    def get_historical_analogs(
        self,
        symbol: str,
        timeframe: str,
        current_df: pd.DataFrame,
        query_timestamp: pd.Timestamp,
    ) -> Dict[str, Any]:
        """
        Phase 33: Returns a complete, traceable FAISS result.
        Every historical timestamp is verified < query_timestamp (zero look-ahead).

        Returns
        -------
        dict with:
          status           : VALID | UNAVAILABLE
          samples          : int — number of valid analogs found
          nearest_timestamps    : list[str]
          distances             : list[float]
          similarities          : list[float]  (normalized 0–1)
          historical_directions : list[str]    (BULLISH | BEARISH)
          historical_outcomes   : list[float]  (forward return %)
          average_analog_return : float | UNAVAILABLE
          historical_direction  : str          (aggregate)
          leak_check            : bool         (True = no leakage)
          closest_match_date    : str | UNAVAILABLE
          similarity_score      : float | UNAVAILABLE
        """
        key = f"{symbol}_{timeframe}"
        _unavailable = {
            "status": STATUS_UNAVAILABLE,
            "reason": "INDEX_NOT_BUILT",
            "samples": 0,
            "nearest_timestamps": [],
            "distances": [],
            "similarities": [],
            "historical_directions": [],
            "historical_outcomes": [],
            "average_analog_return": "UNAVAILABLE",
            "historical_direction": "UNAVAILABLE",
            "leak_check": False,
            "closest_match_date": "UNAVAILABLE",
            "similarity_score": "UNAVAILABLE",
        }

        if key not in self.indices:
            return _unavailable

        index = self.indices[key]
        meta = self.metadata[key]

        if current_df.empty:
            return {**_unavailable, "reason": "EMPTY_CURRENT_DF"}

        current_df = current_df.copy()
        if 'timestamp' in current_df.columns:
            current_df['timestamp'] = pd.to_datetime(current_df['timestamp'])
            current_df.set_index('timestamp', inplace=True)

        if self.feature_cols[0] not in current_df.columns:
            current_df = FeatureEngine.add_all_features(current_df)

        latest = current_df.iloc[-1]

        try:
            query_vec = np.array(
                [latest[col] for col in self.feature_cols], dtype='float32'
            ).reshape(1, -1)
        except KeyError as e:
            return {**_unavailable, "reason": f"MISSING_FEATURE_COL_{e}"}

        # Normalize using same mean/std as training
        means = meta.iloc[0]['faiss_mean']
        stds = meta.iloc[0]['faiss_std']
        query_vec = (query_vec - means) / stds

        k = 10
        distances, I = index.search(query_vec, k)

        # Ensure query_timestamp is timezone-aware pandas Timestamp
        if isinstance(query_timestamp, datetime):
            query_ts_pd = pd.Timestamp(query_timestamp)
        else:
            query_ts_pd = pd.Timestamp(query_timestamp)
        if query_ts_pd.tzinfo is None:
            query_ts_pd = query_ts_pd.tz_localize("UTC")

        nearest_timestamps = []
        distances_list = []
        similarities_list = []
        historical_directions = []
        historical_outcomes = []
        leak_detected = False
        best_distance = float('inf')
        best_match_date = None

        for i in range(k):
            idx = I[0][i]
            if idx < 0 or idx >= len(meta):
                continue

            match_row = meta.iloc[idx]
            match_date = match_row.name

            # Phase 33 Zero-Trust: explicit leak check
            match_ts = pd.Timestamp(match_date)
            if match_ts.tzinfo is None:
                match_ts = match_ts.tz_localize("UTC")

            if match_ts >= query_ts_pd:
                leak_detected = True
                logger.error(
                    f"FAISS_LEAKAGE_DETECTED: match_date={match_ts.isoformat()} "
                    f">= query_timestamp={query_ts_pd.isoformat()}"
                )
                continue  # Skip this contaminated match

            dist = float(distances[0][i])
            sim = round(1.0 / (1.0 + dist), 4)

            fwd_ret = match_row.get('forward_return_5')
            if pd.isna(fwd_ret):
                continue

            fwd_ret = float(fwd_ret)
            direction = "BULLISH" if fwd_ret > 0 else "BEARISH"

            nearest_timestamps.append(match_ts.isoformat())
            distances_list.append(round(dist, 4))
            similarities_list.append(sim)
            historical_directions.append(direction)
            historical_outcomes.append(round(fwd_ret * 100, 4))

            if dist < best_distance:
                best_distance = dist
                best_match_date = match_ts

        if not historical_outcomes:
            return {
                **_unavailable,
                "reason": "NO_VALID_ANALOGS_AFTER_LEAKCHECK",
                "leak_check": not leak_detected,
            }

        avg_ret = float(np.mean(historical_outcomes))
        aggregate_direction = "BULLISH" if avg_ret > 0 else "BEARISH"

        return {
            "status": STATUS_VALID,
            "samples": len(nearest_timestamps),
            "nearest_timestamps": nearest_timestamps,
            "distances": distances_list,
            "similarities": similarities_list,
            "historical_directions": historical_directions,
            "historical_outcomes": historical_outcomes,
            "average_analog_return": round(avg_ret, 4),
            "historical_direction": aggregate_direction,
            "leak_check": not leak_detected,
            "closest_match_date": best_match_date.isoformat() if best_match_date else "UNAVAILABLE",
            "similarity_score": round(1.0 / (1.0 + best_distance), 4) if best_match_date else "UNAVAILABLE",
            # Legacy aliases for backward compatibility
            "historical_outcome": aggregate_direction,
        }


faiss_memory = FAISSMemoryEngine()
