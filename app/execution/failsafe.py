import logging
from typing import Any

from app.config.settings import get_settings
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class FailsafeManager:
    """
    Emergency Failsafe System for TradeSignalAI-v3.
    Handles Emergency Kill Switch, Manual/Auto trading toggles,
    Daily Loss Shutdowns, and Drawdown Circuit Breakers.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.kill_switch_active: bool = self.settings.EMERGENCY_KILL_SWITCH
        self.auto_trading_enabled: bool = self.settings.AUTO_TRADING_ENABLED
        self.manual_override: bool = False
        
    def activate_kill_switch(self, reason: str = "Manual activation"):
        """Activates emergency kill switch. Immediately halts all trading."""
        self.kill_switch_active = True
        logger.critical(f"EMERGENCY KILL SWITCH ACTIVATED! Reason: {reason}")
        event_bus.publish_sync("FailsafeTriggered", {
            "type": "KILL_SWITCH",
            "reason": reason
        })

    def deactivate_kill_switch(self):
        """Deactivates kill switch to resume normal operations."""
        self.kill_switch_active = False
        logger.info("Emergency Kill Switch deactivated.")

    def set_auto_trading(self, enabled: bool):
        """Toggles automated trading state."""
        self.auto_trading_enabled = enabled
        logger.info(f"Auto Trading state changed to: {enabled}")

    def evaluate_failsafes(self, account_state: dict[str, Any], trade_proposal: dict[str, Any]) -> tuple[bool, str]:
        """
        Evaluates failsafes before trade execution.
        Returns (can_execute, rejection_reason).
        """
        # 1. Emergency Kill Switch
        if self.kill_switch_active:
            return False, "REJECTED: Emergency Kill Switch is ACTIVE."
            
        # 2. Auto Trading Disabled Check
        if not self.auto_trading_enabled:
            return False, "REJECTED: Automated Trading is currently DISABLED."

        # 3. Daily Loss Shutdown
        daily_loss_pct = account_state.get("daily_loss_pct", 0.0)
        if daily_loss_pct >= self.settings.MAX_DAILY_LOSS_PCT:
            self.activate_kill_switch(f"Daily loss limit reached ({daily_loss_pct:.2f}% >= {self.settings.MAX_DAILY_LOSS_PCT:.2f}%)")
            return False, f"REJECTED: Daily loss limit reached ({daily_loss_pct:.2f}%)."

        # 4. Max Drawdown Shutdown
        drawdown_pct = account_state.get("drawdown_pct", 0.0)
        if drawdown_pct >= self.settings.MAX_DRAWDOWN_PCT:
            self.activate_kill_switch(f"Maximum drawdown reached ({drawdown_pct:.2f}% >= {self.settings.MAX_DRAWDOWN_PCT:.2f}%)")
            return False, f"REJECTED: Max drawdown threshold reached ({drawdown_pct:.2f}%)."

        # 5. Connection Protection
        if not account_state.get("broker_connected", True):
            return False, "REJECTED: Broker connection is offline."

        return True, "Failsafe checks passed"

failsafe_manager = FailsafeManager()
