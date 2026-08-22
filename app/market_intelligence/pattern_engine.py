import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
import logging

from app.database.manager import db_manager
from app.database.models.market import CandleModel

logger = logging.getLogger(__name__)


class MarketMemoryEngine:
    """
    Institutional Historical Pattern Engine (Market Memory).
    Uses KDTree / Cosine Similarity to find highly correlated past market contexts
    and empirical probabilities for future price action.
    """

    def __init__(self):
        self.models = {}  # Dict[str, NearestNeighbors] (key: symbol_timeframe)
        self.scalers = {} # Dict[str, StandardScaler]
        self.reference_data = {} # Dict[str, pd.DataFrame]

    async def build_memory(self, symbol: str, timeframe: str):
        """
        Loads all historical data from the DB for the given symbol and timeframe,
        normalizes the feature vectors, and fits a KD-Tree nearest neighbor model.
        """
        logger.info(f"Building Market Memory for {symbol} {timeframe}...")
        
        if db_manager._session_factory is None:
            logger.error("Database not configured.")
            return False

        async with db_manager._session_factory() as session:
            stmt = select(CandleModel).filter(
                CandleModel.symbol == symbol,
                CandleModel.timeframe == timeframe
            ).order_by(CandleModel.timestamp.asc())
            
            result = await session.execute(stmt)
            candles = result.scalars().all()
            
        if not candles or len(candles) < 500:
            logger.warning(f"Not enough data to build memory for {symbol} {timeframe} (count: {len(candles) if candles else 0})")
            return False

        records = []
        for c in candles:
            if not c.features_json:
                continue
            rec = c.features_json.copy()
            rec['timestamp'] = c.timestamp
            rec['close'] = c.close
            
            # Extract Future_Return_5 if it exists in features, else skip
            if 'Future_Return_5' not in rec or rec['Future_Return_5'] is None:
                continue
                
            records.append(rec)
            
        if len(records) < 500:
            logger.warning(f"Not enough complete feature records for {symbol} {timeframe}")
            return False
            
        df = pd.DataFrame(records)
        df.set_index('timestamp', inplace=True)
        
        # Select features to match on
        # We drop outcome variables and raw price
        exclude_cols = ['Future_Return_5', 'close']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        # Handle nan
        df.ffill(inplace=True)
        df.bfill(inplace=True)
        df.dropna(inplace=True)
        
        if len(df) < 500:
            return False

        X = df[feature_cols].values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Build KNN model using cosine distance to capture shape rather than magnitude
        knn = NearestNeighbors(n_neighbors=50, metric='cosine', algorithm='brute')
        knn.fit(X_scaled)
        
        key = f"{symbol}_{timeframe}"
        self.models[key] = knn
        self.scalers[key] = scaler
        
        # Store reference data so we can look up the future returns of the neighbors
        self.reference_data[key] = df
        
        logger.info(f"Successfully built memory for {symbol} {timeframe} with {len(df)} records.")
        return True

    def find_similar_patterns(self, symbol: str, timeframe: str, current_features: Dict[str, float], k: int = 50, prediction_timestamp: float = None) -> Dict[str, Any]:
        """
        Finds the k most similar historical states to the current features.
        Returns the empirical probability of a bullish vs bearish move.
        Filters out any patterns occurring after prediction_timestamp to prevent lookahead bias.
        """
        key = f"{symbol}_{timeframe}"
        
        if key not in self.models:
            return {"error": "Memory not built for this asset/timeframe."}
            
        knn = self.models[key]
        scaler = self.scalers[key]
        ref_df = self.reference_data[key]
        
        # Ensure we have the exact same columns used during training
        exclude_cols = ['Future_Return_5', 'close']
        feature_cols = [c for c in ref_df.columns if c not in exclude_cols]
        
        # Build array safely
        vec = []
        for col in feature_cols:
            vec.append(current_features.get(col, 0.0))
            
        X_current = np.array([vec])
        X_scaled = scaler.transform(X_current)
        
        distances, indices = knn.kneighbors(X_scaled, n_neighbors=min(k * 5, len(ref_df)))
        
        # Analyze outcomes, filtering out future data if prediction_timestamp is set
        outcomes = []
        valid_distances = []
        
        for i, idx in enumerate(indices[0]):
            row = ref_df.iloc[idx]
            # Ensure we don't look into the future
            if prediction_timestamp is not None:
                row_time = row.name.timestamp() if hasattr(row.name, 'timestamp') else row.name
                if row_time >= prediction_timestamp:
                    continue
                    
            outcomes.append(row['Future_Return_5'])
            valid_distances.append(distances[0][i])
            
            if len(outcomes) == k:
                break
                
        if not outcomes:
            return {"error": "No valid historical patterns found before the prediction timestamp."}
            
        outcomes = np.array(outcomes)
        actual_k = len(outcomes)
        
        bullish_count = np.sum(outcomes > 0)
        bearish_count = np.sum(outcomes < 0)
        
        avg_return = np.mean(outcomes)
        win_rate_long = bullish_count / actual_k
        win_rate_short = bearish_count / actual_k
        
        # Generate Narrative
        narrative = f"Found {actual_k} similar historical patterns based on current market structure and momentum. "
        if win_rate_long > 0.6:
            narrative += f"Historically, this setup resolved BULLISH {win_rate_long*100:.1f}% of the time with an avg move of {avg_return*100:.2f}%."
        elif win_rate_short > 0.6:
            narrative += f"Historically, this setup resolved BEARISH {win_rate_short*100:.1f}% of the time with an avg move of {avg_return*100:.2f}%."
        else:
            narrative += "Historically, this setup shows mixed/neutral resolution without a dominant edge."

        return {
            "k_neighbors": actual_k,
            "bullish_probability": float(win_rate_long),
            "bearish_probability": float(win_rate_short),
            "expected_return": float(avg_return),
            "memory_narrative": narrative,
            "closest_distance": float(valid_distances[0]) if valid_distances else 0.0
        }

# Global Instance
market_memory = MarketMemoryEngine()
