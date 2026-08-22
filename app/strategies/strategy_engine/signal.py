import logging

from app.strategies.strategy_engine.types import StrategySignal
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class SignalValidator:
    """
    Validates signals before they are pushed to the EventBus.
    """
    @staticmethod
    def validate(signal: StrategySignal) -> bool:
        if signal.confidence < 0 or signal.confidence > 1:
            return False
            
        if signal.direction not in ["BUY", "SELL", "WAIT"]:
            return False
            
        # Ensure STOP LOSS is valid relative to ENTRY ZONE
        if signal.direction == "BUY" and signal.stop_loss_suggestion and signal.entry_zone:
            if signal.stop_loss_suggestion >= min(signal.entry_zone):
                return False # Stop loss must be below entry for buy
                
        if signal.direction == "SELL" and signal.stop_loss_suggestion and signal.entry_zone:
            if signal.stop_loss_suggestion <= max(signal.entry_zone):
                return False # Stop loss must be above entry for sell
                
        return True

class SignalEngine:
    """
    Normalizes, validates, aggregates and publishes signals.
    """
    def __init__(self):
        self.validator = SignalValidator()
        self.active_signals: list[StrategySignal] = []

    async def process_signal(self, signal: StrategySignal):
        """
        Receives a raw signal from a strategy plugin.
        """
        if not self.validator.validate(signal):
            logger.warning(f"Invalid signal rejected: {signal.signal_id}")
            await event_bus.publish("SignalRejected", payload=signal.model_dump())
            return
            
        # Normalization steps could occur here
        self.active_signals.append(signal)
        
        # Publish
        logger.info(f"Signal Generated [{signal.asset} {signal.timeframe}]: {signal.direction} (Conf: {signal.confidence})")
        await event_bus.publish("SignalGenerated", payload=signal.model_dump())

signal_engine = SignalEngine()
