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

        import math

        if not symbol:
            return {"approved": False, "reason": "Missing trade symbol", "checks": {"symbol": False}}

        if direction not in ("BUY", "SELL"):
            return {"approved": False, "reason": f"Invalid direction: {direction}", "checks": {"direction": False}}

        if not isinstance(quantity, (int, float)) or math.isnan(quantity) or math.isinf(quantity) or quantity <= 0:
            return {"approved": False, "reason": f"Invalid quantity: {quantity}", "checks": {"quantity": False}}

        max_qty = 100
        if quantity > max_qty:
            return {"approved": False, "reason": f"Quantity {quantity} exceeds max {max_qty}", "checks": {"quantity": False}}

        if not isinstance(price, (int, float)) or math.isnan(price) or math.isinf(price) or price <= 0:
            return {"approved": False, "reason": f"Invalid entry price: {price}", "checks": {"price": False}}

        # Coordinator passes "target" and "stop_loss"; accept both keys for resilience
        take_profit = trade_proposal.get("target") or trade_proposal.get("take_profit", 0)
        stop_loss = trade_proposal.get("stop_loss", 0)

        # Enforce mandatory Stop Loss and Take Profit
        if not isinstance(stop_loss, (int, float)) or math.isnan(stop_loss) or math.isinf(stop_loss) or stop_loss <= 0:
            return {"approved": False, "reason": "Missing or non-positive Stop Loss", "checks": {"stop_loss": False}}

        if not isinstance(take_profit, (int, float)) or math.isnan(take_profit) or math.isinf(take_profit) or take_profit <= 0:
            return {"approved": False, "reason": "Missing or non-positive Take Profit", "checks": {"take_profit": False}}

        # Enforce geometric correctness: SL < Entry < TP for BUY, TP < Entry < SL for SELL
        if direction == "BUY":
            if not (stop_loss < price < take_profit):
                return {
                    "approved": False,
                    "reason": f"Invalid BUY geometry: SL ({stop_loss}) < Entry ({price}) < TP ({take_profit}) required",
                    "checks": {"geometry": False}
                }
            risk = price - stop_loss
            reward = take_profit - price
        else:
            if not (take_profit < price < stop_loss):
                return {
                    "approved": False,
                    "reason": f"Invalid SELL geometry: TP ({take_profit}) < Entry ({price}) < SL ({stop_loss}) required",
                    "checks": {"geometry": False}
                }
            risk = stop_loss - price
            reward = price - take_profit

        if risk <= 0:
            return {"approved": False, "reason": "Invalid Risk parameter (SL = Entry)", "checks": {"rr_ratio": False}}

        rr_ratio = reward / risk
        if rr_ratio < 2.0:
            return {"approved": False, "reason": f"RR Ratio {rr_ratio:.2f} is below minimum 2.0", "checks": {"rr_ratio": False}}

        result["checks"]["quantity"] = True
        result["checks"]["price"] = True
        result["checks"]["stop_loss"] = True
        result["checks"]["take_profit"] = True
        result["checks"]["rr_ratio"] = True

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