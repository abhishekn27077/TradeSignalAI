from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class SizingResult:
    asset: str
    direction: str
    recommended_lots: float
    risk_amount_usd: float
    risk_pct_used: float
    is_trade_allowed: bool
    rejection_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "direction": self.direction,
            "recommended_lots": round(float(self.recommended_lots), 3),
            "risk_amount_usd": round(float(self.risk_amount_usd), 2),
            "risk_pct_used": round(float(self.risk_pct_used), 3),
            "is_trade_allowed": self.is_trade_allowed,
            "rejection_reason": self.rejection_reason,
            "details": self.details,
        }


class RiskBudgetEngine:
    """
    Dynamic Portfolio Risk Budget & Position Sizing Engine.
    Adjusts position sizing according to account equity, stop distance, ATR volatility, and portfolio drawdown.
    """

    def __init__(
        self,
        default_risk_pct: float = 0.01,  # 1.0% risk per trade
        max_daily_drawdown_pct: float = 0.05,  # 5.0% max daily drawdown halt
        max_open_positions: int = 5,
        min_lot_size: float = 0.01,
        max_lot_size: float = 10.0
    ):
        self.default_risk_pct = default_risk_pct
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_open_positions = max_open_positions
        self.min_lot_size = min_lot_size
        self.max_lot_size = max_lot_size

    def calculate_position_size(
        self,
        account_equity: float,
        entry_price: float,
        stop_loss: float,
        asset: str = "EURUSD",
        direction: str = "BUY",
        current_daily_drawdown_pct: float = 0.0,
        current_open_positions_count: int = 0,
        atr_volatility_multiplier: float = 1.0
    ) -> SizingResult:
        if account_equity <= 0:
            return SizingResult(asset, direction, 0.0, 0.0, 0.0, False, "Account equity is zero or negative.")

        if current_open_positions_count >= self.max_open_positions:
            return SizingResult(asset, direction, 0.0, 0.0, 0.0, False, f"Max open positions ({self.max_open_positions}) reached.")

        if current_daily_drawdown_pct >= self.max_daily_drawdown_pct:
            return SizingResult(asset, direction, 0.0, 0.0, 0.0, False, f"Daily drawdown ({current_daily_drawdown_pct*100:.1f}%) exceeds limit ({self.max_daily_drawdown_pct*100:.1f}%). Trading halted.")

        # Risk percentage modulation (e.g. cut risk in half if daily drawdown > 3%)
        risk_pct = self.default_risk_pct
        if current_daily_drawdown_pct >= 0.03:
            risk_pct *= 0.5

        # Modulate by volatility
        if atr_volatility_multiplier > 1.5:
            risk_pct /= (atr_volatility_multiplier / 1.2)

        risk_amount = account_equity * risk_pct
        stop_distance = abs(entry_price - stop_loss)

        if stop_distance <= 1e-6:
            return SizingResult(asset, direction, 0.0, 0.0, 0.0, False, "Invalid stop loss: distance to entry is zero.")

        # Pip value approximation
        is_jpy = "JPY" in asset
        is_crypto = "BTC" in asset or "ETH" in asset
        is_gold = "XAU" in asset
        is_index = "NAS" in asset or "SPX" in asset

        if is_crypto or is_gold or is_index:
            # 1 unit per price point
            lots = risk_amount / stop_distance
        else:
            # Standard FX lot = 100,000 units
            pip_size = 0.01 if is_jpy else 0.0001
            stop_pips = stop_distance / pip_size
            pip_value_per_standard_lot = 10.0  # approximate $10/pip for standard lot
            lots = risk_amount / (stop_pips * pip_value_per_standard_lot)

        lots = max(self.min_lot_size, min(self.max_lot_size, round(lots, 2)))

        return SizingResult(
            asset=asset,
            direction=direction,
            recommended_lots=lots,
            risk_amount_usd=risk_amount,
            risk_pct_used=risk_pct,
            is_trade_allowed=True,
            details={
                "stop_distance": round(stop_distance, 5),
                "account_equity": account_equity,
                "volatility_multiplier": round(atr_volatility_multiplier, 2)
            }
        )
