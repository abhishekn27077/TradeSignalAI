from typing import Any

from app.config.settings import get_settings
from app.logs.logger import get_logger

logger = get_logger(__name__)


class RiskEngine:
    def __init__(self):
        self._settings = get_settings()
        self._failsafe = None
        self._initialized = False

    async def initialize(self):
        try:
            from app.execution.failsafe import failsafe_manager
            self._failsafe = failsafe_manager
            self._initialized = True
        except Exception as e:
            logger.warning(f"Failsafe not available: {e}")
            self._initialized = True

    def validate_trade(self, trade_proposal: dict[str, Any]) -> dict[str, Any]:
        result = {"approved": True, "reason": "Risk check passed", "checks": {}}

        symbol = trade_proposal.get("symbol", "")
        direction = trade_proposal.get("direction", "BUY")
        quantity = trade_proposal.get("quantity", 0)
        price = trade_proposal.get("price", 0)

        max_qty = 100
        if quantity > max_qty:
            result["approved"] = False
            result["reason"] = f"Quantity {quantity} exceeds max {max_qty}"
            result["checks"]["quantity"] = False
            
        # RR Filter > 2:1
        # Coordinator passes "target" and "stop_loss"; accept both keys for resilience
        take_profit = trade_proposal.get("target") or trade_proposal.get("take_profit", 0)
        stop_loss = trade_proposal.get("stop_loss", 0)
        
        if take_profit > 0 and stop_loss > 0 and price > 0:
            if direction == "BUY":
                risk = price - stop_loss
                reward = take_profit - price
            else:
                risk = stop_loss - price
                reward = price - take_profit
                
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio < 2.0:
                    result["approved"] = False
                    result["reason"] = f"RR Ratio {rr_ratio:.2f} is below minimum 2.0"
                    result["checks"]["rr_ratio"] = False
            else:
                result["approved"] = False
                result["reason"] = "Invalid Risk parameter (SL = Entry)"
                result["checks"]["rr_ratio"] = False

        result["checks"]["max_daily_loss"] = self._settings.MAX_DAILY_LOSS_PCT
        result["checks"]["max_drawdown"] = self._settings.MAX_DRAWDOWN_PCT

        if self._failsafe:
            try:
                fs_result = self._failsafe.check()
                if isinstance(fs_result, dict) and fs_result.get("kill_switch_active"):
                    result["approved"] = False
                    result["reason"] = "Kill switch active"
            except Exception as e:
                logger.warning(f"Failsafe check error: {e}")
                # Fail closed on failsafe error to prevent unreviewed trades
                result["approved"] = False
                result["reason"] = f"Failsafe check error: {e}"

        return result