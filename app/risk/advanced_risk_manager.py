from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

class AdvancedRiskManager:
    """
    Phases 8 & 9: Advanced Risk & Portfolio Engine
    Handles daily drawdown, consecutive losses, and sector exposure.
    """
    def __init__(self, 
                 max_daily_drawdown_pct: float = 5.0, 
                 max_consecutive_losses: int = 3,
                 max_sector_exposure_pct: float = 25.0):
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_sector_exposure_pct = max_sector_exposure_pct
        
    def check_daily_drawdown(self, portfolio: dict[str, Any]) -> bool:
        """
        Returns True if daily drawdown is ACCEPTABLE.
        False if limit breached.
        """
        start_balance = portfolio.get("daily_start_balance", 0.0)
        current_balance = portfolio.get("current_balance", 0.0)
        
        if start_balance == 0.0:
            return True
            
        drawdown_pct = ((start_balance - current_balance) / start_balance) * 100
        
        if drawdown_pct >= self.max_daily_drawdown_pct:
            logger.warning(f"Daily drawdown limit breached: {drawdown_pct:.2f}% >= {self.max_daily_drawdown_pct}%")
            return False
            
        return True
        
    def check_consecutive_losses(self, trade_history: list[dict[str, Any]]) -> bool:
        """
        Returns True if consecutive losses are ACCEPTABLE.
        False if limit breached (too many losses in a row).
        """
        losses = 0
        for trade in reversed(trade_history):
            if trade.get("pnl", 0.0) < 0:
                losses += 1
            else:
                break # Broken the losing streak
                
        if losses >= self.max_consecutive_losses:
            logger.warning(f"Consecutive loss limit breached: {losses} >= {self.max_consecutive_losses}")
            return False
            
        return True
        
    def check_sector_exposure(self, symbol_sector: str, open_positions: list[dict[str, Any]], total_equity: float) -> bool:
        """
        Returns True if adding to this sector is ACCEPTABLE.
        False if sector exposure limit breached.
        """
        if total_equity == 0:
            return True
            
        sector_capital = 0.0
        for pos in open_positions:
            if pos.get("sector") == symbol_sector:
                sector_capital += pos.get("position_size_usd", 0.0)
                
        exposure_pct = (sector_capital / total_equity) * 100
        
        if exposure_pct >= self.max_sector_exposure_pct:
            logger.warning(f"Sector exposure limit breached for {symbol_sector}: {exposure_pct:.2f}% >= {self.max_sector_exposure_pct}%")
            return False
            
        return True

advanced_risk_manager = AdvancedRiskManager()
