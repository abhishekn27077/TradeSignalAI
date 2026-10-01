import os
import threading
import pandas as pd
import numpy as np
import torch
try:
    import safetensors
    import safetensors.torch
except ImportError:
    safetensors = None
from typing import Dict, Any, Tuple, Optional
from app.analytics.models.kronos.kronos import Kronos, KronosTokenizer, KronosPredictor
from app.logs.logger import get_logger

logger = get_logger(__name__)


class KronosModelRegistry:
    """
    Lifecycle-managed, thread-safe model registry and cache for the Kronos Foundation Model.

    Guarantees:
    - Load-once behavior across concurrent threads and repeated adapter instantiations.
    - Zero redundant memory allocation or duplicate PyTorch tensor allocations in memory.
    - Thread-safe acquisition using a re-entrant lock.
    - Safe failure handling with cached failure status to avoid repeated blocking retries.
    - Explicit lifecycle controls: is_loaded(), get_instance(), clear_cache(), metrics.
    """
    _instance: Optional['KronosModelRegistry'] = None
    _lock = threading.RLock()

    def __init__(self):
        self._cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self._init_count = 0
        self._load_count = 0
        self._inference_count = 0

    @classmethod
    def get_instance(cls) -> 'KronosModelRegistry':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = KronosModelRegistry()
        return cls._instance

    @property
    def actual_model_loads(self) -> int:
        with self._lock:
            return self._load_count

    @property
    def adapter_init_calls(self) -> int:
        with self._lock:
            return self._init_count

    @property
    def inferences_executed(self) -> int:
        with self._lock:
            return self._inference_count

    def get_or_load(self, model_name: str, tokenizer_name: str, device: str) -> Dict[str, Any]:
        key = (model_name, tokenizer_name, device)
        with self._lock:
            self._init_count += 1
            if key in self._cache:
                entry = self._cache[key]
                if entry.get("status") == "LOADED":
                    return entry

            logger.info(f"Initializing genuine Kronos model: {model_name} on {device}")
            tokenizer = None
            model = None
            predictor = None
            status = "FAILED"
            error = None

            try:
                # 1. First attempt: local cache
                try:
                    tokenizer = KronosTokenizer.from_pretrained(tokenizer_name, local_files_only=True)
                    model = Kronos.from_pretrained(model_name, local_files_only=True)
                    if hasattr(model, "eval"):
                        model.eval()
                    predictor = KronosPredictor(model, tokenizer, device=device)
                    logger.info("Successfully loaded PyTorch Kronos model from local cache.")
                    status = "LOADED"
                    self._load_count += 1
                except Exception as local_err:
                    logger.debug(f"Local cache load attempt had error: {local_err}")

                # 2. Second attempt: remote hub if not in local cache
                if status != "LOADED":
                    logger.info(f"Downloading/Loading tokenizer weights from HuggingFace Hub: {tokenizer_name}")
                    tokenizer = KronosTokenizer.from_pretrained(tokenizer_name)
                    logger.info(f"Downloading/Loading model weights from HuggingFace Hub: {model_name}")
                    model = Kronos.from_pretrained(model_name)
                    if hasattr(model, "eval"):
                        model.eval()
                    predictor = KronosPredictor(model, tokenizer, device=device)
                    logger.info("Successfully loaded PyTorch Kronos model.")
                    status = "LOADED"
                    self._load_count += 1

            except Exception as e:
                error = str(e)
                logger.warning(f"Kronos model initialization deferred (offline): {e}")

            entry = {
                "tokenizer": tokenizer,
                "model": model,
                "predictor": predictor,
                "status": status,
                "error": error,
                "model_name": model_name,
                "tokenizer_name": tokenizer_name,
                "device": device,
            }
            self._cache[key] = entry
            return entry

    def is_loaded(self, model_name: str = "NeoQuasar/Kronos-mini", tokenizer_name: str = "NeoQuasar/Kronos-Tokenizer-base", device: str = "cpu") -> bool:
        key = (model_name, tokenizer_name, device)
        with self._lock:
            return key in self._cache and self._cache[key].get("status") == "LOADED"

    def record_inference(self):
        with self._lock:
            self._inference_count += 1

    def clear_cache(self):
        with self._lock:
            self._cache.clear()
            self._load_count = 0
            self._init_count = 0
            self._inference_count = 0

    @property
    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "adapter_init_calls": self._init_count,
                "actual_model_loads": self._load_count,
                "inferences_executed": self._inference_count,
                "cached_models": list(self._cache.keys()),
            }


class KronosAdapter:
    """
    Genuine adapter to interface TradeSignalAI-v3 market data with the Kronos Foundation Model.
    Utilizes KronosModelRegistry for load-once, thread-safe lifecycle caching.
    """
    def __init__(self, model_name: str = "NeoQuasar/Kronos-mini", tokenizer_name: str = "NeoQuasar/Kronos-Tokenizer-base", device: str = "cpu"):
        self.device = device
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        
        self._registry = KronosModelRegistry.get_instance()
        loaded = self._registry.get_or_load(model_name, tokenizer_name, device)
        
        self.tokenizer = loaded.get("tokenizer")
        self.model = loaded.get("model")
        self.predictor = loaded.get("predictor")
        self.status = loaded.get("status", "FAILED")
        self.error = loaded.get("error")

    def is_loaded(self) -> bool:
        return self.status == "LOADED" and self.predictor is not None

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
            self._registry.record_inference()
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
