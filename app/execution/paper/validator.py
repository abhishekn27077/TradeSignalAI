from app.paper_trading.account_manager import VirtualAccount


class OrderValidator:
    """Validates if an order can be placed."""
    
    @staticmethod
    def validate(account: VirtualAccount, symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> tuple[bool, str]:
        if quantity <= 0:
            return False, "Quantity must be greater than 0"
            
        if order_type in ["LIMIT", "STOP"] and price is None:
            return False, f"Price required for {order_type} orders"
            
        # Basic margin check (without leverage for now)
        est_price = price if price else 1.0 # Requires current price ideally
        est_cost = est_price * quantity
        
        if est_cost > account.free_margin:
            return False, "Insufficient free margin"
            
        return True, "Valid"
