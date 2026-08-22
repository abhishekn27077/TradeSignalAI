from typing import Any


class RegimeAnalyzer:
    @staticmethod
    def analyze(trades: list[dict]) -> dict[str, Any]:
        """
        Group trades by market regime and calculate stats.
        """
        regime_stats = {}
        for t in trades:
            regime = t.get("regime", "UNKNOWN")
            if regime not in regime_stats:
                regime_stats[regime] = {"trades": 0, "wins": 0, "pnl": 0.0, "total_profit": 0.0, "total_loss": 0.0}
            
            pnl = t.get("pnl", 0)
            regime_stats[regime]["trades"] += 1
            regime_stats[regime]["pnl"] += pnl
            
            if pnl > 0:
                regime_stats[regime]["wins"] += 1
                regime_stats[regime]["total_profit"] += pnl
            else:
                regime_stats[regime]["total_loss"] += abs(pnl)

        for regime, stats in regime_stats.items():
            stats["win_rate"] = (stats["wins"] / stats["trades"]) * 100 if stats["trades"] > 0 else 0.0
            stats["profit_factor"] = stats["total_profit"] / stats["total_loss"] if stats["total_loss"] > 0 else (float('inf') if stats["total_profit"] > 0 else 0)
            stats["avg_profit"] = stats["total_profit"] / stats["wins"] if stats["wins"] > 0 else 0.0
            losses = stats["trades"] - stats["wins"]
            stats["avg_loss"] = stats["total_loss"] / losses if losses > 0 else 0.0

        if not regime_stats:
            return {}

        best_regime = max(regime_stats.keys(), key=lambda r: regime_stats[r]["pnl"])
        worst_regime = min(regime_stats.keys(), key=lambda r: regime_stats[r]["pnl"])

        return {
            "detailed_stats": regime_stats,
            "best_regime": best_regime,
            "worst_regime": worst_regime
        }
