import os
import pandas as pd
import numpy as np
import torch
from app.analytics.models.kronos.kronos import Kronos, KronosTokenizer, KronosPredictor
from app.logs.logger import get_logger

logger = get_logger(__name__)

class KronosAdapter:
    """
    Genuine adapter to interface TradeSignalAI-v3 market data with the Kronos Foundation Model.
    """
    def __init__(self, model_name: str = "NeoQuasar/Kronos-mini", tokenizer_name: str = "NeoQuasar/Kronos-Tokenizer-base", device: str = "cpu"):
        self.device = device
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        self.tokenizer = None
        self.model = None
        self.predictor = None
        
        self._initialize_model()

    def _initialize_model(self):
        logger.info(f"Initializing genuine Kronos model: {self.model_name} on {self.device}")
        
        try:
            # First attempt: load from local cache without blocking network
            try:
                self.tokenizer = KronosTokenizer.from_pretrained(self.tokenizer_name, local_files_only=True)
                self.model = Kronos.from_pretrained(self.model_name, local_files_only=True)
                self.predictor = KronosPredictor(self.model, self.tokenizer, device=self.device)
                logger.info("Successfully loaded PyTorch Kronos model from local cache.")
                return
            except Exception:
                pass

            # Second attempt: load from HuggingFace Hub
            logger.info(f"Downloading/Loading tokenizer weights from HuggingFace Hub: {self.tokenizer_name}")
            self.tokenizer = KronosTokenizer.from_pretrained(self.tokenizer_name)
            
            logger.info(f"Downloading/Loading model weights from HuggingFace Hub: {self.model_name}")
            self.model = Kronos.from_pretrained(self.model_name)
            
            self.predictor = KronosPredictor(self.model, self.tokenizer, device=self.device)
            logger.info("Successfully loaded PyTorch Kronos model.")
        except Exception as e:
            logger.warning(f"Kronos model initialization deferred (offline): {e}")
            # Keep as None, predictions will fallback to baseline statistical models

    def format_market_data(self, ohlcv_data) -> pd.DataFrame:
        """
        Kronos requires raw OHLCV sequential data.
        Returns a DataFrame with columns: open, high, low, close, volume
        """
        if isinstance(ohlcv_data, pd.DataFrame):
            df = ohlcv_data.copy()
        else:
            df = pd.DataFrame(ohlcv_data)
            
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
        # Ensure correct column names
        rename_map = {c: c.lower() for c in df.columns}
        df.rename(columns=rename_map, inplace=True)
        
        # Verify required columns
        for col in ['open', 'high', 'low', 'close']:
            if col not in df.columns:
                raise ValueError(f"Missing required price column: {col}")
                
        if 'volume' not in df.columns:
            df['volume'] = 0.0
            
        return df

    def train(self, df: pd.DataFrame):
        """
        Pretrained Foundation Model - fine-tuning is disabled for zero-shot testing.
        """
        logger.warning(f"Kronos is a pre-trained foundation model. Skipping online training.")
        pass

    def predict(self, df: pd.DataFrame, pred_len: int = 1) -> float:
        """
        Generates a scalar prediction for the expected return.
        """
        if df.empty or self.predictor is None:
            return 0.0

        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                df = self.format_market_data(df)

            x_timestamp = df.index

            # Create future timestamps
            freq = pd.Timedelta(minutes=5)  # Default fallback
            if len(df.index) >= 2 and isinstance(df.index, pd.DatetimeIndex):
                diff = df.index[-1] - df.index[-2]
                if diff > pd.Timedelta(0):
                    freq = diff

            y_timestamp = pd.date_range(start=df.index[-1] + freq, periods=pred_len, freq=freq)

            # Deterministic seeding for zero-trust reproducibility across identical candle snapshots
            try:
                import hashlib
                import torch
                import numpy as np
                seed_bytes = df[['open', 'high', 'low', 'close']].values.tobytes()
                seed_int = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
                torch.manual_seed(seed_int)
                np.random.seed(seed_int % (2**32 - 1))
            except Exception:
                pass

            # Predict
            pred_df = self.predictor.predict(
                df=df,
                x_timestamp=x_timestamp,
                y_timestamp=y_timestamp,
                pred_len=pred_len,
                verbose=False
            )
            
            # Calculate expected return over the prediction window. 
            current_close = df['close'].iloc[-1]
            predicted_close = pred_df['close'].iloc[-1]
            
            expected_return = (predicted_close - current_close) / current_close
            return float(expected_return)
            
        except Exception as e:
            logger.error(f"Prediction failed in KronosAdapter: {e}")
            return 0.0

    def get_feature_importances(self, df: pd.DataFrame) -> dict:
        """ Foundation models don't expose simple feature importances. """
        return {}
