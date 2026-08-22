
class StrategyLifecycle:
    STATES = [
        "Created",
        "Validated",
        "Backtested",
        "Walk-Forward Tested",
        "Paper Trading",
        "Qualified",
        "Production Candidate",
        "Retired"
    ]

    def promote(self, strategy_id: str, current_state: str) -> str:
        """Promote a strategy to the next lifecycle state."""
        try:
            idx = self.STATES.index(current_state)
            if idx < len(self.STATES) - 1:
                # Stub: normally you cannot skip paper trading unless tests passed
                return self.STATES[idx + 1]
            return current_state
        except ValueError:
            return "Created"

strategy_lifecycle = StrategyLifecycle()
