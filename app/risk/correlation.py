from typing import Any


class CorrelationEngine:
    """Checks correlation between proposed trades and existing portfolio."""
    
    def check_correlation(self, account_state: dict[str, Any], trade_proposal: dict[str, Any]) -> bool:
        """
        MVP: Basic check if we already have > N correlated positions.
        In production, this would query a correlation matrix (e.g., Pearson coeff) across assets.
        """
        symbol = trade_proposal.get("symbol", "")
        existing_positions = account_state.get("positions", [])
        
        # Simple heuristic: If we have 3 or more long positions, and we try to add another long, check correlation
        # For MVP, we will just count how many positions we have in the same base currency
        base_currency = symbol.split('-')[0] if '-' in symbol else symbol
        
        correlated_count = sum(1 for p in existing_positions if base_currency in p.get("symbol", ""))
        
        if correlated_count >= 3:
            return False # Reject trade to avoid concentration risk
            
        return True

correlation_engine = CorrelationEngine()
