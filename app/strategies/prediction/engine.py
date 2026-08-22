from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    expected_direction: str = "WAIT"
    bullish_probability: float = 50.0
    bearish_probability: float = 50.0
    expected_holding_hours: float = 2.0
    expected_move_pct: float = 0.0
    expected_price_range: tuple[float, float] = (0.0, 0.0)
    expected_volatility: float = 0.0
    confidence: float = 0.5
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "expected_direction": self.expected_direction,
            "bullish_probability": round(self.bullish_probability, 1),
            "bearish_probability": round(self.bearish_probability, 1),
            "expected_holding_hours": round(self.expected_holding_hours, 1),
            "expected_move_pct": round(self.expected_move_pct, 2),
            "expected_price_range": [round(self.expected_price_range[0], 5), round(self.expected_price_range[1], 5)],
            "expected_volatility": round(self.expected_volatility, 4),
            "confidence": round(self.confidence, 4),
            "reasoning": self.reasoning,
        }


class PredictionEngine:
    def predict(self, df: pd.DataFrame, direction: str, signal: dict | None = None) -> PredictionResult:
        if df is None or len(df) < 20:
            return PredictionResult(reasoning="Insufficient data for prediction")

        close = df['close'].values.astype(float)
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        current_price = close[-1]

        returns = np.diff(close) / close[:-1] * 100
        recent_returns = returns[-20:] if len(returns) >= 20 else returns
        volatility = float(np.std(recent_returns)) if len(recent_returns) > 1 else 0.5

        atr_values = self._compute_atr(high, low, close)
        atr_current = float(atr_values[-1]) if not np.isnan(atr_values[-1]) else current_price * 0.01
        atr_pct = (atr_current / current_price) * 100 if current_price > 0 else 0.5

        last_10_high = float(np.max(high[-10:]))
        last_10_low = float(np.min(low[-10:]))

        if direction == "BUY":
            bullish_prob = 50.0 + volatility * 10
            recent_up = np.sum(recent_returns > 0) / len(recent_returns) * 100 if len(recent_returns) > 0 else 50
            bullish_prob = min(95, bullish_prob * 0.5 + recent_up * 0.5)
            bearish_prob = 100 - bullish_prob
            expected_move = atr_pct * 1.5
            expected_range = (current_price - atr_current * 0.5, current_price + atr_current * 2.0)
        elif direction == "SELL":
            bearish_prob = 50.0 + volatility * 10
            recent_down = np.sum(recent_returns < 0) / len(recent_returns) * 100 if len(recent_returns) > 0 else 50
            bearish_prob = min(95, bearish_prob * 0.5 + recent_down * 0.5)
            bullish_prob = 100 - bearish_prob
            expected_move = -atr_pct * 1.5
            expected_range = (current_price - atr_current * 2.0, current_price + atr_current * 0.5)
        else:
            bullish_prob = 50.0
            bearish_prob = 50.0
            expected_move = 0.0
            expected_range = (last_10_low, last_10_high)

        vol_std = volatility
        expected_vol = vol_std

        conf = 100 - vol_std * 0.5
        if atr_pct > 0.3 and atr_pct < 3.0:
            conf = min(95, conf + 5)
        else:
            conf = max(30, conf - 10)
        conf = max(30, min(95, conf))

        rsi_values = self._compute_rsi(close)
        rsi_current = rsi_values[-1] if not np.isnan(rsi_values[-1]) else 50

        if direction == "BUY" and 40 < rsi_current < 80 or direction == "SELL" and 20 < rsi_current < 60:
            conf = min(95, conf + 5)

        holding_hours = 2.0
        if atr_pct > 2.0:
            holding_hours = 1.0
        elif atr_pct < 0.5:
            holding_hours = 4.0

        reasoning_parts = [
            f"Direction: {direction}",
            f"Volatility: {volatility:.2f}%",
            f"ATR%: {atr_pct:.2f}%",
            f"RSI: {rsi_current:.1f}",
        ]

        return PredictionResult(
            expected_direction=direction or "WAIT",
            bullish_probability=round(bullish_prob, 1),
            bearish_probability=round(bearish_prob, 1),
            expected_holding_hours=holding_hours,
            expected_move_pct=round(expected_move, 2),
            expected_price_range=(round(expected_range[0], 5), round(expected_range[1], 5)),
            expected_volatility=round(expected_vol, 4),
            confidence=round(conf / 100.0, 4),
            reasoning=" | ".join(reasoning_parts),
        )

    def _compute_atr(self, high, low, close, period=14):
        tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - close[:-1]))
        tr = np.maximum(tr, np.abs(low[1:] - close[:-1]))
        tr = np.concatenate([[tr[0]], tr]) if len(tr) > 0 else np.array([0])
        return pd.Series(tr).ewm(span=period, adjust=False).mean().values

    def _compute_rsi(self, close, period=14):
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        gains = np.concatenate([[0], gains])
        losses = np.concatenate([[0], losses])
        avg_gain = pd.Series(gains).ewm(span=period, adjust=False).mean().values
        avg_loss = pd.Series(losses).ewm(span=period, adjust=False).mean().values
        rs = np.divide(avg_gain, avg_loss, out=np.ones_like(avg_gain), where=avg_loss != 0)
        return 100 - (100 / (1 + rs))


prediction_engine = PredictionEngine()
