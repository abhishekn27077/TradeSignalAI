from typing import Any


class ExitIntelligence:
    def analyze(self, symbol: str, direction: str, current_price: float, expected_move: float) -> dict[str, Any]:
        """
        Recommends profit target, stop loss, trailing stop, partial exit logic.
        """
        multiplier = 1 if direction == "BULLISH" else -1
        profit_target = current_price * (1 + (expected_move * multiplier))
        stop_loss = current_price * (1 - ((expected_move / 2) * multiplier)) # 2:1 RR
        
        return {
            "recommended_profit_target": round(profit_target, 2),
            "recommended_stop_loss": round(stop_loss, 2),
            "recommended_trailing_stop": round(current_price * (1 - (0.01 * multiplier)), 2)
        }

exit_intelligence = ExitIntelligence()
