from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class ExecutionBridge:
    """
    Listens to Forecast events and triggers paper trades if configured.
    """
    
    def __init__(self):
        self._auto_paper_trade = True # In production, read from config/settings
        
    def start(self):
        event_bus.subscribe("ForecastActive", self.handle_forecast_active)
        logger.info("Execution Bridge started")
        
    async def handle_forecast_active(self, payload):
        if not self._auto_paper_trade:
            return
            
        try:
            symbol = payload.get("symbol")
            direction = payload.get("direction")
            confidence = payload.get("confidence")
            expected_move = payload.get("expected_move_pct", 0.0)
            
            if not symbol or not direction:
                return
                
            if direction == "NEUTRAL":
                return
                
            # Get current market price
            from app.market_data.providers.manager import market_provider_manager
            ticker = await market_provider_manager.get_ticker(symbol)
            current_price = ticker.get("last_price") if ticker else 0.0
            
            if not current_price:
                logger.warning(f"Could not get current price for {symbol}, aborting paper trade.")
                return
                
            # Calculate TP and SL
            tp = 0.0
            sl = 0.0
            
            # Use 2:1 RR if expected move is valid, otherwise fallback to 1% move
            move_magnitude = abs(expected_move) if expected_move else 0.01
            
            if direction == "BULLISH":
                tp = current_price * (1 + move_magnitude)
                sl = current_price * (1 - (move_magnitude / 2))
            else:
                tp = current_price * (1 - move_magnitude)
                sl = current_price * (1 + (move_magnitude / 2))
            
            # Validate with Risk Engine
            from app.risk.engine import RiskEngine
            risk_engine = RiskEngine()
            
            trade_proposal = {
                "symbol": symbol,
                "direction": "BUY" if direction == "BULLISH" else "SELL",
                "quantity": 1.0,
                "price": current_price,
                "take_profit": tp,
                "stop_loss": sl
            }
            
            risk_result = risk_engine.validate_trade(trade_proposal)
            if not risk_result.get("approved"):
                logger.warning(f"ExecutionBridge: Trade rejected by RiskEngine: {risk_result.get('reason')}")
                return

            # Actually dispatch to the Execution Engine Order Manager
            from app.execution.paper.order_manager import order_manager
            
            side = trade_proposal["direction"]
            # For paper trading, assume a default account id "system_default"
            await order_manager.create_order(
                account_id="default_paper",
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=1.0,
                take_profit=tp,
                stop_loss=sl
            )
            
            # We would also ideally create a position tracking entry with TP/SL here
            # But the existing paper trading model only creates orders
            logger.info(f"ExecutionBridge: Auto Paper Trading triggered for {symbol} ({direction}) with TP={tp:.2f}, SL={sl:.2f}")
            
            # Would also update ForecastConsensusModel.paper_trade_id here
        except Exception as e:
            logger.error(f"Error in Execution Bridge: {e}")

execution_bridge = ExecutionBridge()
