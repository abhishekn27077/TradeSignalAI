from typing import Any


class PatternDetector:
    @staticmethod
    def detect_patterns(trades: list[dict[str, Any]]) -> dict[str, Any]:
        if not trades:
            return {"best_asset": "", "worst_asset": "", "long_win_rate": 0, "short_win_rate": 0}
        return {
            "best_asset": PatternDetector._best_category(trades, "symbol", positive=True),
            "worst_asset": PatternDetector._best_category(trades, "symbol", positive=False),
            "best_session": PatternDetector._best_category(trades, "session", positive=True),
            "worst_session": PatternDetector._best_category(trades, "session", positive=False),
            "long_win_rate": PatternDetector._win_rate_by(trades, "direction", "BUY"),
            "short_win_rate": PatternDetector._win_rate_by(trades, "direction", "SELL"),
        }

    @staticmethod
    def _best_category(trades: list[dict[str, Any]], attr: str, positive: bool = True) -> str:
        pnl_by_cat = {}
        for t in trades:
            val = t.get(attr, "Unknown")
            pnl_by_cat[val] = pnl_by_cat.get(val, 0) + t.get("pnl", 0)
        if not pnl_by_cat:
            return "None"
        best = max(pnl_by_cat.items(), key=lambda x: x[1]) if positive else min(pnl_by_cat.items(), key=lambda x: x[1])
        return best[0] if (best[1] > 0 if positive else best[1] < 0) else "None"

    @staticmethod
    def _win_rate_by(trades: list[dict[str, Any]], attr: str, value: str) -> float:
        subset = [t for t in trades if t.get(attr) == value]
        if not subset:
            return 0.0
        wins = len([t for t in subset if t.get("pnl", 0) > 0])
        return wins / len(subset)


pattern_detector = PatternDetector()
pattern_analyzer = pattern_detector