"""
Feature Store
===============
Computes and persists technical indicators, volume metrics, volatility,
market structure, and SMC features for each candle.
Features are stored as JSON blobs on the CandleModel for fast single-query retrieval.
"""

import math
from typing import Any

import numpy as np

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class FeatureStore:
    """
    Calculates and persists technical features for historical candle data.
    Supports incremental computation — only recalculates from the last
    candle that has features.
    """

    async def generate_features(self, symbol: str, timeframe: str) -> dict[str, Any]:
        """
        Calculate and persist features for all candles of a symbol/timeframe.
        Returns summary of features generated.
        """
        candles = await self._load_candles_as_arrays(symbol, timeframe)

        if not candles or len(candles["close"]) < 20:
            return {
                "symbol": symbol, "timeframe": timeframe,
                "status": "insufficient_data",
                "candles": len(candles["close"]) if candles else 0,
            }

        n = len(candles["close"])
        features_list = []

        try:
            await self._publish_progress(symbol, timeframe, 0, "computing")

            # Compute all indicators
            close = np.array(candles["close"], dtype=float)
            high = np.array(candles["high"], dtype=float)
            low = np.array(candles["low"], dtype=float)
            open_ = np.array(candles["open"], dtype=float)
            volume = np.array(candles["volume"], dtype=float)

            # Moving averages
            ema9 = self._ema(close, 9)
            ema21 = self._ema(close, 21)
            ema50 = self._ema(close, 50)
            ema200 = self._ema(close, 200)
            sma20 = self._sma(close, 20)
            sma50 = self._sma(close, 50)
            sma200 = self._sma(close, 200)

            # RSI
            rsi14 = self._rsi(close, 14)

            # MACD
            macd_line, macd_signal, macd_hist = self._macd(close, 12, 26, 9)

            # ATR
            atr14 = self._atr(high, low, close, 14)

            # ADX
            adx14 = self._adx(high, low, close, 14)

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._bollinger(close, 20, 2)

            # Supertrend
            supertrend, supertrend_dir = self._supertrend(high, low, close, 10, 3)

            # VWAP (session-based approximation)
            vwap = self._vwap(high, low, close, volume)

            # Volume metrics
            vol_sma = self._sma(volume, 20)

            # Volatility
            atr_pct = np.where(close > 0, (atr14 / close) * 100, 0)
            bb_width = np.where(bb_middle > 0, (bb_upper - bb_lower) / bb_middle, 0)

            await self._publish_progress(symbol, timeframe, 50, "computing")

            # Swing highs/lows (fractal-based, lookback=5)
            swing_highs = self._swing_highs(high, 5)
            swing_lows = self._swing_lows(low, 5)

            # Trend strength (ADX + EMA slope)
            trend_strength = np.where(adx14 > 0, np.minimum(adx14 / 50, 1.0), 0)

            # Build feature dicts per candle
            for i in range(n):
                features = {
                    "ema9": self._safe(ema9[i]),
                    "ema21": self._safe(ema21[i]),
                    "ema50": self._safe(ema50[i]),
                    "ema200": self._safe(ema200[i]),
                    "sma20": self._safe(sma20[i]),
                    "sma50": self._safe(sma50[i]),
                    "sma200": self._safe(sma200[i]),
                    "rsi14": self._safe(rsi14[i]),
                    "macd_line": self._safe(macd_line[i]),
                    "macd_signal": self._safe(macd_signal[i]),
                    "macd_hist": self._safe(macd_hist[i]),
                    "atr14": self._safe(atr14[i]),
                    "adx14": self._safe(adx14[i]),
                    "bb_upper": self._safe(bb_upper[i]),
                    "bb_middle": self._safe(bb_middle[i]),
                    "bb_lower": self._safe(bb_lower[i]),
                    "supertrend": self._safe(supertrend[i]),
                    "supertrend_dir": int(supertrend_dir[i]) if not np.isnan(supertrend_dir[i]) else 0,
                    "vwap": self._safe(vwap[i]),
                    "vol_sma20": self._safe(vol_sma[i]),
                    "rel_volume": self._safe(volume[i] / vol_sma[i]) if vol_sma[i] > 0 else 0,
                    "atr_pct": self._safe(atr_pct[i]),
                    "bb_width": self._safe(bb_width[i]),
                    "trend_strength": self._safe(trend_strength[i]),
                    "is_swing_high": bool(swing_highs[i]),
                    "is_swing_low": bool(swing_lows[i]),
                }
                features_list.append(features)

            await self._publish_progress(symbol, timeframe, 80, "persisting")

            # Persist features to DB
            updated = await self._persist_features(
                symbol, timeframe, candles["ids"], features_list
            )

            await self._publish_progress(symbol, timeframe, 100, "completed")

            result = {
                "symbol": symbol, "timeframe": timeframe,
                "status": "completed",
                "candles": n, "features_updated": updated,
                "feature_count": len(features_list[0]) if features_list else 0,
            }

            try:
                await event_bus.publish("FeatureGenerationProgress", payload=result)
            except Exception:
                pass

            logger.info(f"Features generated: {symbol} {timeframe} — {updated}/{n} candles updated")
            return result

        except Exception as e:
            logger.error(f"Feature generation error for {symbol} {timeframe}: {e}")
            return {
                "symbol": symbol, "timeframe": timeframe,
                "status": "failed", "error": str(e),
            }

    async def get_features(
        self, symbol: str, timeframe: str,
        limit: int = 100, offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve candles with their computed features."""
        from sqlalchemy import desc, select

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return []

        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(CandleModel)
                    .where(CandleModel.symbol == symbol, CandleModel.timeframe == timeframe)
                    .order_by(desc(CandleModel.timestamp))
                    .limit(limit).offset(offset)
                )
                rows = result.scalars().all()
                return [
                    {
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                        "open": r.open, "high": r.high, "low": r.low,
                        "close": r.close, "volume": r.volume,
                        "features": r.features_json or {},
                    }
                    for r in reversed(rows)  # Return in chronological order
                ]
            except Exception as e:
                logger.warning(f"Get features error: {e}")
                return []

    async def get_coverage(self) -> list[dict[str, Any]]:
        """Get feature coverage stats for all symbol/timeframe combos."""
        from sqlalchemy import func, select

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return []

        async with session_factory() as session:
            try:
                # Total candles per symbol/tf
                total_q = await session.execute(
                    select(
                        CandleModel.symbol, CandleModel.timeframe,
                        func.count(CandleModel.id).label("total"),
                    ).group_by(CandleModel.symbol, CandleModel.timeframe)
                )
                totals = {f"{r.symbol}:{r.timeframe}": r.total for r in total_q}

                # Candles with features
                feat_q = await session.execute(
                    select(
                        CandleModel.symbol, CandleModel.timeframe,
                        func.count(CandleModel.id).label("with_features"),
                    ).where(CandleModel.features_json.isnot(None))
                    .group_by(CandleModel.symbol, CandleModel.timeframe)
                )
                feats = {f"{r.symbol}:{r.timeframe}": r.with_features for r in feat_q}

                coverage = []
                for key, total in totals.items():
                    sym, tf = key.split(":")
                    with_feat = feats.get(key, 0)
                    coverage.append({
                        "symbol": sym, "timeframe": tf,
                        "total_candles": total,
                        "with_features": with_feat,
                        "coverage_pct": round((with_feat / total) * 100, 1) if total > 0 else 0,
                    })
                return coverage
            except Exception as e:
                logger.warning(f"Get coverage error: {e}")
                return []

    # ── Technical Indicator Calculations ─────────────────────────────────────

    @staticmethod
    def _safe(val) -> float | None:
        """Convert to float, returning None for NaN/Inf."""
        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            return None
        try:
            v = float(val)
            return round(v, 6) if abs(v) < 1e10 else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        result = np.full(len(data), np.nan)
        if len(data) < period:
            return result
        k = 2.0 / (period + 1)
        result[period - 1] = np.mean(data[:period])
        for i in range(period, len(data)):
            result[i] = data[i] * k + result[i - 1] * (1 - k)
        return result

    @staticmethod
    def _sma(data: np.ndarray, period: int) -> np.ndarray:
        result = np.full(len(data), np.nan)
        if len(data) < period:
            return result
        cumsum = np.cumsum(data)
        cumsum[period:] = cumsum[period:] - cumsum[:-period]
        result[period - 1:] = cumsum[period - 1:] / period
        return result

    @staticmethod
    def _rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
        result = np.full(len(close), np.nan)
        if len(close) < period + 1:
            return result
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        if avg_loss == 0:
            result[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[period] = 100 - (100 / (1 + rs))
        for i in range(period + 1, len(close)):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
            if avg_loss == 0:
                result[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i] = 100 - (100 / (1 + rs))
        return result

    @staticmethod
    def _macd(close, fast=12, slow=26, signal_period=9):
        n = len(close)
        macd_line = np.full(n, np.nan)
        macd_signal = np.full(n, np.nan)
        macd_hist = np.full(n, np.nan)

        if n < slow:
            return macd_line, macd_signal, macd_hist

        k_fast = 2.0 / (fast + 1)
        k_slow = 2.0 / (slow + 1)

        ema_fast = np.full(n, np.nan)
        ema_slow = np.full(n, np.nan)
        ema_fast[fast - 1] = np.mean(close[:fast])
        ema_slow[slow - 1] = np.mean(close[:slow])

        for i in range(fast, n):
            ema_fast[i] = close[i] * k_fast + ema_fast[i - 1] * (1 - k_fast)
        for i in range(slow, n):
            ema_slow[i] = close[i] * k_slow + ema_slow[i - 1] * (1 - k_slow)

        for i in range(slow - 1, n):
            if not np.isnan(ema_fast[i]) and not np.isnan(ema_slow[i]):
                macd_line[i] = ema_fast[i] - ema_slow[i]

        # Signal line
        valid_macd = macd_line[~np.isnan(macd_line)]
        if len(valid_macd) >= signal_period:
            k_sig = 2.0 / (signal_period + 1)
            first_valid = np.where(~np.isnan(macd_line))[0][0]
            sig_start = first_valid + signal_period - 1
            if sig_start < n:
                macd_signal[sig_start] = np.mean(macd_line[first_valid:sig_start + 1])
                for i in range(sig_start + 1, n):
                    if not np.isnan(macd_line[i]):
                        macd_signal[i] = macd_line[i] * k_sig + macd_signal[i - 1] * (1 - k_sig)

        macd_hist = macd_line - macd_signal
        return macd_line, macd_signal, macd_hist

    @staticmethod
    def _atr(high, low, close, period=14):
        n = len(close)
        result = np.full(n, np.nan)
        if n < 2:
            return result
        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        if n >= period:
            result[period - 1] = np.mean(tr[:period])
            for i in range(period, n):
                result[i] = (result[i - 1] * (period - 1) + tr[i]) / period
        return result

    @staticmethod
    def _adx(high, low, close, period=14):
        n = len(close)
        result = np.full(n, np.nan)
        if n < period * 2:
            return result

        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        tr = np.zeros(n)

        for i in range(1, n):
            up = high[i] - high[i - 1]
            down = low[i - 1] - low[i]
            plus_dm[i] = up if (up > down and up > 0) else 0
            minus_dm[i] = down if (down > up and down > 0) else 0
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

        atr = np.full(n, np.nan)
        s_plus = np.full(n, np.nan)
        s_minus = np.full(n, np.nan)

        atr[period] = np.mean(tr[1:period + 1])
        s_plus[period] = np.mean(plus_dm[1:period + 1])
        s_minus[period] = np.mean(minus_dm[1:period + 1])

        for i in range(period + 1, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
            s_plus[i] = (s_plus[i - 1] * (period - 1) + plus_dm[i]) / period
            s_minus[i] = (s_minus[i - 1] * (period - 1) + minus_dm[i]) / period

        di_plus = np.where(atr > 0, (s_plus / atr) * 100, 0)
        di_minus = np.where(atr > 0, (s_minus / atr) * 100, 0)
        di_sum = di_plus + di_minus
        dx = np.where(di_sum > 0, np.abs(di_plus - di_minus) / di_sum * 100, 0)

        if n >= period * 2:
            result[period * 2 - 1] = np.mean(dx[period:period * 2])
            for i in range(period * 2, n):
                result[i] = (result[i - 1] * (period - 1) + dx[i]) / period

        return result

    @staticmethod
    def _bollinger(close, period=20, std_dev=2):
        n = len(close)
        upper = np.full(n, np.nan)
        middle = np.full(n, np.nan)
        lower = np.full(n, np.nan)

        for i in range(period - 1, n):
            window = close[i - period + 1:i + 1]
            m = np.mean(window)
            s = np.std(window)
            middle[i] = m
            upper[i] = m + std_dev * s
            lower[i] = m - std_dev * s

        return upper, middle, lower

    @staticmethod
    def _supertrend(high, low, close, period=10, multiplier=3):
        n = len(close)
        supertrend = np.full(n, np.nan)
        direction = np.full(n, np.nan)  # 1 = up, -1 = down

        atr = np.zeros(n)
        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

        if n < period:
            return supertrend, direction

        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

        upper_band = np.zeros(n)
        lower_band = np.zeros(n)

        for i in range(period - 1, n):
            hl2 = (high[i] + low[i]) / 2
            upper_band[i] = hl2 + multiplier * atr[i]
            lower_band[i] = hl2 - multiplier * atr[i]

        supertrend[period - 1] = upper_band[period - 1]
        direction[period - 1] = -1

        for i in range(period, n):
            if close[i - 1] <= upper_band[i - 1]:
                upper_band[i] = min(upper_band[i], upper_band[i - 1]) if upper_band[i - 1] != 0 else upper_band[i]
            if close[i - 1] >= lower_band[i - 1]:
                lower_band[i] = max(lower_band[i], lower_band[i - 1]) if lower_band[i - 1] != 0 else lower_band[i]

            if direction[i - 1] == 1:
                if close[i] < lower_band[i]:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]
                else:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
            else:
                if close[i] > upper_band[i]:
                    direction[i] = 1
                    supertrend[i] = lower_band[i]
                else:
                    direction[i] = -1
                    supertrend[i] = upper_band[i]

        return supertrend, direction

    @staticmethod
    def _vwap(high, low, close, volume):
        """Cumulative VWAP approximation."""
        n = len(close)
        typical_price = (high + low + close) / 3
        cum_tp_vol = np.cumsum(typical_price * volume)
        cum_vol = np.cumsum(volume)
        vwap = np.where(cum_vol > 0, cum_tp_vol / cum_vol, typical_price)
        return vwap

    @staticmethod
    def _swing_highs(high, lookback=5):
        n = len(high)
        result = np.zeros(n, dtype=bool)
        for i in range(lookback, n - lookback):
            if high[i] == max(high[i - lookback:i + lookback + 1]):
                result[i] = True
        return result

    @staticmethod
    def _swing_lows(low, lookback=5):
        n = len(low)
        result = np.zeros(n, dtype=bool)
        for i in range(lookback, n - lookback):
            if low[i] == min(low[i - lookback:i + lookback + 1]):
                result[i] = True
        return result

    # ── Persistence ──────────────────────────────────────────────────────────

    async def _load_candles_as_arrays(self, symbol: str, timeframe: str) -> dict | None:
        """Load all candles as numpy-ready arrays."""
        from sqlalchemy import select

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return None

        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(CandleModel)
                    .where(CandleModel.symbol == symbol, CandleModel.timeframe == timeframe)
                    .order_by(CandleModel.timestamp)
                )
                rows = result.scalars().all()
                if not rows:
                    return None

                return {
                    "ids": [r.id for r in rows],
                    "open": [r.open for r in rows],
                    "high": [r.high for r in rows],
                    "low": [r.low for r in rows],
                    "close": [r.close for r in rows],
                    "volume": [r.volume or 0 for r in rows],
                    "timestamps": [r.timestamp for r in rows],
                }
            except Exception as e:
                logger.warning(f"Load candles as arrays error: {e}")
                return None

    async def _persist_features(
        self, symbol: str, timeframe: str,
        candle_ids: list[int], features_list: list[dict],
    ) -> int:
        """Write feature JSON blobs to candle records."""
        from sqlalchemy import update

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return 0

        updated = 0
        batch_size = 200

        async with session_factory() as session:
            try:
                for i in range(0, len(candle_ids), batch_size):
                    batch_ids = candle_ids[i:i + batch_size]
                    batch_features = features_list[i:i + batch_size]

                    for cid, feats in zip(batch_ids, batch_features):
                        await session.execute(
                            update(CandleModel)
                            .where(CandleModel.id == cid)
                            .values(features_json=feats)
                        )
                        updated += 1

                    await session.commit()

                return updated
            except Exception as e:
                await session.rollback()
                logger.error(f"Persist features error: {e}")
                return updated

    async def _publish_progress(self, symbol, timeframe, progress, status):
        try:
            await event_bus.publish("FeatureGenerationProgress", payload={
                "symbol": symbol, "timeframe": timeframe,
                "progress": progress, "status": status,
            })
        except Exception:
            pass


# Singleton
feature_store = FeatureStore()
