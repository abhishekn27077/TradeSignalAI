import uuid
from sqlalchemy.future import select
from app.database.manager import db_manager
from app.database.models.paper import PaperPosition, PaperAccount, PaperOrder
from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class PortfolioManager:
    """Manages Paper Accounts and Positions."""
    def __init__(self):
        pass

    def start(self):
        event_bus.subscribe("PaperOrderStatusUpdated", self.handle_order_update)
        event_bus.subscribe("MarketDataTick", self.handle_tick)
        logger.info("Portfolio Manager started")

    async def get_or_create_account(self, account_id: str) -> PaperAccount:
        session_factory = db_manager.get_session()
        async with session_factory() as session:
            stmt = select(PaperAccount).where(PaperAccount.id == account_id)
            result = await session.execute(stmt)
            acc = result.scalar_one_or_none()
            if not acc:
                acc = PaperAccount(id=account_id, name="Paper Trading", balance=100000.0, equity=100000.0)
                session.add(acc)
                await session.commit()
            return acc

    async def handle_order_update(self, payload: dict):
        status = payload.get("status")
        if status != "FILLED":
            return
            
        order_id = payload.get("order_id")
        
        session_factory = db_manager.get_session()
        async with session_factory() as session:
            stmt = select(PaperOrder).where(PaperOrder.id == order_id)
            result = await session.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                return
                
            # Create or update position
            pos_stmt = select(PaperPosition).where(
                PaperPosition.account_id == order.account_id,
                PaperPosition.symbol == order.symbol
            )
            res = await session.execute(pos_stmt)
            position = res.scalar_one_or_none()
            
            fill_price = order.fill_price or 0.0
            
            if not position:
                pos_side = "LONG" if order.side == "BUY" else "SHORT"
                position = PaperPosition(
                    id=str(uuid.uuid4()),
                    account_id=order.account_id,
                    symbol=order.symbol,
                    side=pos_side,
                    entry_price=fill_price,
                    quantity=order.filled_quantity,
                    take_profit=order.take_profit,
                    stop_loss=order.stop_loss
                )
                session.add(position)
                logger.info(f"Created new position for {order.symbol} at {fill_price}")
            else:
                # Update existing position (simplistic averaging or closing)
                if (position.side == "LONG" and order.side == "SELL") or (position.side == "SHORT" and order.side == "BUY"):
                    # Closing
                    position.quantity -= order.filled_quantity
                    if position.quantity <= 0:
                        await session.delete(position)
                        logger.info(f"Closed position for {order.symbol}")
                else:
                    # Adding
                    total_qty = position.quantity + order.filled_quantity
                    avg_price = ((position.entry_price * position.quantity) + (fill_price * order.filled_quantity)) / total_qty
                    position.quantity = total_qty
                    position.entry_price = avg_price
                    logger.info(f"Added to position for {order.symbol}, new avg {avg_price}")
                    
            await session.commit()

    async def handle_tick(self, payload: dict):
        symbol = payload.get("symbol")
        price = payload.get("price")
        
        # Check TP/SL for open positions
        session_factory = db_manager.get_session()
        async with session_factory() as session:
            stmt = select(PaperPosition).where(PaperPosition.symbol == symbol)
            res = await session.execute(stmt)
            positions = res.scalars().all()
            
            for pos in positions:
                close_position = False
                close_reason = ""
                
                if pos.side == "LONG":
                    if pos.take_profit and price >= pos.take_profit:
                        close_position = True
                        close_reason = "TP hit"
                    elif pos.stop_loss and price <= pos.stop_loss:
                        close_position = True
                        close_reason = "SL hit"
                elif pos.side == "SHORT":
                    if pos.take_profit and price <= pos.take_profit:
                        close_position = True
                        close_reason = "TP hit"
                    elif pos.stop_loss and price >= pos.stop_loss:
                        close_position = True
                        close_reason = "SL hit"
                        
                if close_position:
                    logger.info(f"Closing {pos.side} position for {symbol} at {price} ({close_reason})")
                    # In a real engine, this creates a MARKET closing order.
                    await session.delete(pos)
            
            await session.commit()

portfolio_manager = PortfolioManager()
