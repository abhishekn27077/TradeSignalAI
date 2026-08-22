from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class MultiTimeframeResolver:
    TF_MAP = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}

    def resolve(self, symbol: str, target_tf: str, data: dict[str, Any] | None = None) -> list[dict[str, Any]] | None:
        if data is None:
            logger.warning(f"No data provided to resolve {target_tf} for {symbol}")
            return None
        target_data = data.get(target_tf)
        if target_data is not None:
            return target_data
        available = list(data.keys())
        found = None
        for tf in available:
            if self._can_resolve(tf, target_tf):
                found = tf
                break
        if found is None:
            logger.warning(f"Cannot resolve {target_tf} data for {symbol}")
            return None
        try:
            source_bars = data[found]
            if not source_bars:
                return []
            ratio = self.TF_MAP.get(target_tf, 60) // self.TF_MAP.get(found, 1)
            if ratio <= 1:
                return source_bars
            aggregated = []
            for i in range(0, len(source_bars), ratio):
                chunk = source_bars[i : i + ratio]
                if not chunk:
                    continue
                agg = {
                    "time": chunk[0].get("time", 0),
                    "open": chunk[0].get("open", 0),
                    "high": max(c.get("high", 0) for c in chunk),
                    "low": min(c.get("low", 0) for c in chunk),
                    "close": chunk[-1].get("close", 0),
                }
                aggregated.append(agg)
            return aggregated
        except Exception as e:
            logger.warning(f"Resampling failed for {symbol}: {e}")
            return data.get(found)

    def _can_resolve(self, source_tf: str, target_tf: str) -> bool:
        src = self.TF_MAP.get(source_tf)
        tgt = self.TF_MAP.get(target_tf)
        if src is None or tgt is None:
            return False
        return tgt > src and tgt % src == 0


mtf_resolver = MultiTimeframeResolver()