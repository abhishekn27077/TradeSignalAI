from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class RiskModel:
    def __init__(self, id: str, limit_type: str, threshold: float):
        self.id = id
        self.limit_type = limit_type
        self.threshold = threshold
        self.current_value = 0.0
        self.active = True


class LimitManager:
    def __init__(self):
        self._limits: dict[str, RiskModel] = {}
        self._limits["global_max_dd"] = RiskModel(id="l1", limit_type="MAX_DRAWDOWN", threshold=0.15)
        self._limits["global_daily_loss"] = RiskModel(id="l2", limit_type="MAX_DAILY_LOSS", threshold=0.03)
        self._limits["max_exposure_per_asset"] = RiskModel(id="l3", limit_type="MAX_EXPOSURE_PCT", threshold=0.20)

    def update_limit(self, limit_id: str, current_value: float):
        if limit_id in self._limits:
            self._limits[limit_id].current_value = current_value

    def get_all_limits(self) -> dict[str, Any]:
        return {
            lid: {"threshold": lm.threshold, "current": lm.current_value, "active": lm.active, "type": lm.limit_type}
            for lid, lm in self._limits.items()
        }

    def check_global_limits(self, account_state: dict[str, Any]) -> bool:
        if "max_drawdown" in account_state:
            dd = self._limits.get("global_max_dd")
            if dd and dd.active and account_state["max_drawdown"] > dd.threshold:
                logger.warning(f"Max drawdown exceeded: {account_state['max_drawdown']} > {dd.threshold}")
                return False
        if "daily_pnl_pct" in account_state:
            dl = self._limits.get("global_daily_loss")
            if dl and dl.active and account_state["daily_pnl_pct"] < 0 and abs(account_state["daily_pnl_pct"]) > dl.threshold:
                logger.warning(f"Daily loss exceeded: {abs(account_state['daily_pnl_pct'])} > {dl.threshold}")
                return False
        return True

    def check_exposure_limits(self, account_state: dict[str, Any], trade_proposal: dict[str, Any]) -> bool:
        el = self._limits.get("max_exposure_per_asset")
        if not el or not el.active:
            return True
        proposed = trade_proposal.get("price", 0) * trade_proposal.get("quantity", 0)
        equity = account_state.get("equity", 1.0)
        existing = account_state.get("asset_exposures", {}).get(trade_proposal.get("symbol"), 0.0)
        new_pct = (existing + proposed) / equity
        if new_pct > el.threshold:
            logger.warning(f"Exposure limit exceeded for {trade_proposal.get('symbol')}: {new_pct}")
            return False
        return True


limit_manager = LimitManager()
risk_limits = limit_manager
GlobalLimitsManager = LimitManager
PortfolioRiskManager = LimitManager