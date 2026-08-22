from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class PatternDetector:
    def __init__(self):
        self._patterns: list[dict[str, Any]] = []

    def detect(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(data) < 10:
            return []
        patterns = []
        closes = [d.get("close", 0) for d in data]
        opens = [d.get("open", 0) for d in data]
        highs = [d.get("high", 0) for d in data]
        lows = [d.get("low", 0) for d in data]

        for i in range(3, len(data)):
            c, o, h, l = closes[i], opens[i], highs[i], lows[i]
            pc, po = closes[i - 1], opens[i - 1]

            body = abs(c - o)
            upper_wick = h - max(c, o)
            lower_wick = min(c, o) - l

            is_hammer = lower_wick >= 2 * body and upper_wick <= body * 0.5 and pc < po
            is_shooting_star = upper_wick >= 2 * body and lower_wick <= body * 0.5 and pc > po
            is_engulfing = abs(c - o) > abs(pc - po) and (c > o and pc < po or c < o and pc > po)

            if is_hammer:
                patterns.append({"type": "hammer", "index": i, "confidence": "high"})
            elif is_shooting_star:
                patterns.append({"type": "shooting_star", "index": i, "confidence": "high"})
            elif is_engulfing:
                patterns.append({"type": "engulfing", "index": i, "confidence": "medium"})

        self._patterns = patterns
        return patterns


pattern_detector = PatternDetector()