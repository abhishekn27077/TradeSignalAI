
class AIInsightsGenerator:
    def generate_brief(self, session: str) -> str:
        """
        Generates natural language market briefs.
        """
        if session == "Morning":
            return "Markets open with strong tech momentum. Keep an eye on inflation data at 13:30 GMT."
        elif session == "London":
            return "European equities flat. GBP/USD breaking out of consolidation."
        elif session == "New York":
            return "S&P500 rallies on earnings. High correlation risk between BTC and NASDAQ."
        elif session == "EOD":
            return "Risk-on sentiment dominated. USD slightly weaker across the board."
        elif session == "Weekly":
            return "This week favors defensive positioning ahead of FOMC."
        return "No insights available."

ai_insights_generator = AIInsightsGenerator()
