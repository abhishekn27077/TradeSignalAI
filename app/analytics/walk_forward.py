

class WalkForwardOptimizer:
    @staticmethod
    def optimize(trades: list[dict], window_size: int = 100, step_size: int = 50) -> dict:
        """
        Simulate Walk-Forward Optimization on a sequence of trades.
        Splits trades into overlapping windows.
        Train -> Validate -> Shift.
        """
        if not trades or len(trades) < window_size:
            return {"status": "insufficient_data"}
            
        windows = []
        start = 0
        while start + window_size <= len(trades):
            window_trades = trades[start:start+window_size]
            train_split = int(window_size * 0.7)
            train_trades = window_trades[:train_split]
            validate_trades = window_trades[train_split:]
            
            train_pnl = sum(t.get("pnl", 0) for t in train_trades)
            validate_pnl = sum(t.get("pnl", 0) for t in validate_trades)
            
            windows.append({
                "window_start_idx": start,
                "train_pnl": train_pnl,
                "validate_pnl": validate_pnl,
                "overfitted": train_pnl > 0 and validate_pnl < 0
            })
            start += step_size
            
        overfit_count = sum(1 for w in windows if w["overfitted"])
        stability_score = 100 - ((overfit_count / len(windows)) * 100) if windows else 0
        
        return {
            "windows_analyzed": len(windows),
            "stability_score": stability_score,
            "overfitted_windows": overfit_count,
            "is_robust": stability_score > 70.0,
            "windows": windows
        }
