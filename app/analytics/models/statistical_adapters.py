import os
import pickle
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from app.analytics.feature_engine import FeatureEngine
from app.logs.logger import get_logger

logger = get_logger(__name__)

class StatisticalAdapter:
    """
    Adapter to interface TradeSignalAI-v3 market data with statistical baseline models
    (XGBoost, Random Forest, HistGradientBoosting).

    Supported states:
    - UNTRAINED : Instantiated without weights file. Predict returns 0.0 and does not dilute consensus.
    - LOADED    : Pre-trained serialized weights successfully loaded from disk.
    - TRAINED   : Model successfully fitted on candle feature data in-session.
    - FAILED    : Failed to deserialize or train.
    - DISABLED  : Explicitly disabled.
    """
    def __init__(self, model_name: str = "xgboost"):
        self.model_name = model_name.lower()
        self.model_path = os.path.join(os.path.dirname(__file__), f"stat_{self.model_name}.pkl")
        self.model = None
        self.state = "UNTRAINED"
        self._load_or_initialize()

    def _load_or_initialize(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.state = "LOADED"
                logger.info(f"Loaded pre-trained Statistical ({self.model_name}) weights.")
            except Exception as e:
                logger.error(f"Failed to load weights for {self.model_name}: {e}")
                self.state = "FAILED"
                self._initialize_new_model()
        else:
            self._initialize_new_model()

    def _initialize_new_model(self):
        self.state = "UNTRAINED"
        logger.debug(f"Statistical ({self.model_name}) model initialized in UNTRAINED state (no weights found).")
        if self.model_name == "xgboost":
            self.model = xgb.XGBRegressor(
                n_estimators=200, learning_rate=0.05, max_depth=6,
                subsample=0.8, colsample_bytree=0.8, random_state=42
            )
        elif self.model_name == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=10, min_samples_split=5, random_state=42
            )
        elif self.model_name == "hist_gb":
            self.model = HistGradientBoostingRegressor(
                learning_rate=0.05, max_iter=200, max_depth=6, random_state=42
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_name}")

    def format_market_data(self, ohlcv_data: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(ohlcv_data)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
        rename_map = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}
        df.rename(columns=rename_map, inplace=True)
        
        df = FeatureEngine.add_all_features(df)
        return df

    def train(self, df: pd.DataFrame):
        if 'Future_Return_5' not in df.columns:
            raise ValueError("Target variable 'Future_Return_5' not found in features.")
            
        train_df = df.dropna(subset=['Future_Return_5'])
        X = train_df.drop(columns=['Future_Return_5', 'close'], errors='ignore')
        y = train_df['Future_Return_5']
        
        logger.info(f"Training Statistical ({self.model_name}) on {len(X)} samples...")
        self.model.fit(X, y)
        self.state = "TRAINED"
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Statistical ({self.model_name}) weights saved successfully.")

    def predict(self, df: pd.DataFrame) -> float:
        """
        Generates a scalar prediction for the expected return.
        If the model is UNTRAINED or FAILED, safely returns 0.0 without raising.
        """
        if df.empty or self.state not in ("LOADED", "TRAINED"):
            return 0.0
            
        predict_df = df.drop(columns=['Future_Return_5', 'close'], errors='ignore')
        latest_features = predict_df.iloc[[-1]]
        
        try:
            expected_return = self.model.predict(latest_features)[0]
        except Exception:
            logger.debug(f"Statistical ({self.model_name}) model is not fitted yet. Returning 0.0.")
            expected_return = 0.0
            
        return float(expected_return)

    def get_feature_importances(self, df: pd.DataFrame) -> dict:
        try:
            if hasattr(self.model, 'feature_importances_'):
                importance = self.model.feature_importances_
            else:
                return {} # HistGB doesn't support easy feature importances without permutation
            features = df.drop(columns=['Future_Return_5', 'close'], errors='ignore').columns
            return dict(zip(features, importance))
        except Exception:
            return {}
