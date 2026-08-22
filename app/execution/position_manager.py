from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

class PositionManager:
    """
    Phase 7: Position Manager
    Handles dynamic stop loss, break even, ATR trailing stops, and partial exits.
    """
    def __init__(self, atr_multiplier: float = 2.0, break_even_rr: float = 1.0, partial_profit_rr: float = 2.0):
        self.atr_multiplier = atr_multiplier
        self.break_even_rr = break_even_rr
        self.partial_profit_rr = partial_profit_rr

    def calculate_trailing_stop(self, position: dict[str, Any], current_price: float, atr: float) -> float:
        """
        Calculates a new ATR-based trailing stop if the position is profitable enough.
        """
        direction = position.get("direction")
        current_sl = position.get("stop_loss")
        entry = position.get("entry_price")
        
        if direction == "BUY":
            new_sl = current_price - (atr * self.atr_multiplier)
            if current_price > entry and new_sl > current_sl:
                return new_sl
                
        elif direction == "SELL":
            new_sl = current_price + (atr * self.atr_multiplier)
            if current_price < entry and new_sl < current_sl:
                return new_sl
                
        return current_sl

    def should_move_to_break_even(self, position: dict[str, Any], current_price: float) -> bool:
        """
        Moves SL to Break Even if price has reached 1R (or configured RR) of profit.
        """
        if position.get("sl_moved_to_be", False):
            return False
            
        entry = position.get("entry_price")
        initial_sl = position.get("initial_sl")
        risk = abs(entry - initial_sl)
        
        if risk == 0:
            return False
            
        direction = position.get("direction")
        if direction == "BUY":
            profit_rr = (current_price - entry) / risk
        else:
            profit_rr = (entry - current_price) / risk
            
        return profit_rr >= self.break_even_rr

    def should_take_partial_profit(self, position: dict[str, Any], current_price: float) -> bool:
        """
        Takes partial profit (e.g., 50%) when price reaches configured RR.
        """
        if position.get("partial_taken", False):
            return False
            
        entry = position.get("entry_price")
        initial_sl = position.get("initial_sl")
        risk = abs(entry - initial_sl)
        
        if risk == 0:
            return False
            
        direction = position.get("direction")
        if direction == "BUY":
            profit_rr = (current_price - entry) / risk
        else:
            profit_rr = (entry - current_price) / risk
            
        return profit_rr >= self.partial_profit_rr

    def manage_position(self, position: dict[str, Any], current_price: float, atr: float) -> dict[str, Any]:
        """
        Main loop hook to manage an open position.
        Returns the updated position dict or exit signals.
        """
        updates = {}
        
        # 1. Trailing Stop
        new_sl = self.calculate_trailing_stop(position, current_price, atr)
        if new_sl != position.get("stop_loss"):
            updates["stop_loss"] = new_sl
            updates["sl_updated_at"] = "NOW"
            
        # 2. Break Even
        if self.should_move_to_break_even(position, current_price):
            be_price = position.get("entry_price")
            direction = position.get("direction")
            current_best_sl = updates.get("stop_loss", position.get("stop_loss"))
            
            if direction == "BUY" and be_price > current_best_sl or direction == "SELL" and be_price < current_best_sl:
                updates["stop_loss"] = be_price
                
            updates["sl_moved_to_be"] = True
            
        # 3. Partial Profit
        if self.should_take_partial_profit(position, current_price):
            updates["partial_taken"] = True
            updates["exit_partial_amount"] = 0.5  # 50% scale out
            
        return updates

position_manager = PositionManager()
