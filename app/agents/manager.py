import logging

from app.agents.base import BaseAIAgent
from app.agents.types import AgentRole

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Holds references to all active AI Agents in the system.
    """
    def __init__(self):
        self._agents: dict[str, BaseAIAgent] = {}

    def register(self, agent: BaseAIAgent):
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered Agent: {agent.agent_id} ({agent.role})")

    def get_agent(self, agent_id: str) -> BaseAIAgent | None:
        return self._agents.get(agent_id)

    def get_agents_by_role(self, role: AgentRole) -> list[BaseAIAgent]:
        return [a for a in self._agents.values() if a.role == role]

class AgentFactory:
    """
    Instantiates AI Agents with the correct configuration.
    """
    @staticmethod
    def create_agent(agent_id: str, role: AgentRole) -> BaseAIAgent:
        # In a full system, you might map roles to specific subclass implementations
        # e.g., ChiefTraderAgent(BaseAIAgent), MarketAnalystAgent(BaseAIAgent)
        # For this Phase, we instantiate the base class directly since the differing logic
        # is driven by Prompts and Tools.
        return BaseAIAgent(agent_id=agent_id, role=role)

class AgentLifecycleManager:
    """
    Orchestrates the startup, shutdown, and health checking of all agents.
    """
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def initialize_default_crew(self):
        """Bootstraps the standard trading team."""
        chief = AgentFactory.create_agent("chief_001", AgentRole.CHIEF_TRADER)
        market = AgentFactory.create_agent("market_001", AgentRole.MARKET_ANALYST)
        tech = AgentFactory.create_agent("tech_001", AgentRole.TECHNICAL_ANALYST)
        risk = AgentFactory.create_agent("risk_001", AgentRole.RISK_MANAGER)

        self.registry.register(chief)
        self.registry.register(market)
        self.registry.register(tech)
        self.registry.register(risk)
        
        logger.info("Default AI Crew initialized successfully.")

    async def _on_signal_generated(self, payload: dict, **kwargs):
        payload_data = kwargs.get("payload", payload) if kwargs else payload
        symbol = payload_data.get("asset") or payload_data.get("symbol")
        if symbol:
            import asyncio

            from app.agents.consensus.engine import consensus_engine
            asyncio.create_task(consensus_engine.run_consensus(symbol))

    def start(self):
        self.initialize_default_crew()
        
        from app.agents.consensus.engine import consensus_engine
        consensus_engine.chief = self.registry.get_agent("chief_001")
        consensus_engine.subordinates = [
            self.registry.get_agent("market_001"),
            self.registry.get_agent("tech_001"),
            self.registry.get_agent("risk_001")
        ]
        
        from app.utils.event_bus import event_bus
        event_bus.subscribe("SignalGenerated", self._on_signal_generated)
        logger.info("AgentLifecycleManager started and subscribed to SignalGenerated.")

agent_registry = AgentRegistry()
lifecycle_manager = AgentLifecycleManager(agent_registry)
