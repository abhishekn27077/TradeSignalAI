import uuid
from datetime import datetime, timezone

import pandas as pd

from app.logs.logger import get_logger
from app.market_data.providers.manager import market_provider_manager
from app.strategies.plugins.registry import strategy_registry
from app.strategies.strategy_engine.core import BaseStrategy
from app.strategies.strategy_engine.metadata import StrategyMetadata, StrategyStatus
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class ManagedStrategyInstance:
    def __init__(self, name: str, strategy: BaseStrategy, metadata: StrategyMetadata):
        self.name = name
        self.strategy = strategy
        self.metadata = metadata
        self.instance: BaseStrategy | None = None
        self.status: StrategyStatus = metadata.status
        self.priority: int = metadata.priority
        self.weight: float = metadata.weight
        self.max_concurrent_trades: int = metadata.max_concurrent_trades
        self.daily_trade_limit: int = metadata.daily_trade_limit
        self.allowed_sessions: list[str] = metadata.allowed_sessions
        self.allowed_assets: list[str] = metadata.allowed_assets
        self.allowed_timeframes: list[str] = metadata.allowed_timeframes
        self.min_trade_quality: int = metadata.min_trade_quality
        self.min_ai_confidence: float = metadata.min_ai_confidence
        self.current_trades: int = 0
        self.daily_trades: int = 0
        self.last_signal: dict | None = None
        self.today_signals: int = 0
        self.last_signal_time: datetime | None = None
        self.signals_today: int = 0

    def can_trade(self, asset: str, timeframe: str, session: str) -> bool:
        if self.status != StrategyStatus.ENABLED:
            return False
        if "all" not in self.allowed_assets and asset not in self.allowed_assets:
            return False
        if "all" not in self.allowed_timeframes and timeframe not in self.allowed_timeframes:
            return False
        if "all" not in self.allowed_sessions and session not in self.allowed_sessions:
            return False
        if self.current_trades >= self.max_concurrent_trades:
            return False
        if self.signals_today >= self.daily_trade_limit:
            return False
        return True


class StrategyManager:
    def __init__(self):
        self._strategies: dict[str, ManagedStrategyInstance] = {}
        self._running = False
        self.recent_signals: list[dict] = []

    def initialize_strategies(self):
        strategy_registry.load_plugins()
        strategy_classes = strategy_registry.list_strategies()
        for s_name in strategy_classes:
            s_class = strategy_registry.get_strategy(s_name)
            metadata = strategy_registry.get_metadata(s_name)
            if metadata is None:
                from app.strategies.strategy_engine.metadata import (
                    StrategyCategory,
                    StrategyMetadata,
                )
                metadata = StrategyMetadata(name=s_name, description=f"{s_name} strategy", category=StrategyCategory.HYBRID)
            strategy = s_class(name=s_name)
            strategy.initialize()
            instance = self._strategies.get(s_name)
            if instance is None:
                instance = ManagedStrategyInstance(s_name, strategy, metadata)
                self._strategies[s_name] = instance
            instance.instance = strategy
            logger.info(f"Initialized Strategy: {s_name} | Priority={metadata.priority} | Status={metadata.status}")

    async def _on_market_tick(self, payload: dict, **kwargs):
        payload_data = kwargs.get("payload", payload) if kwargs else payload
        symbol = payload_data.get("symbol")
        if not symbol:
            return

        # Phase 4: Strategy Consensus Engine
        strategy_votes = []
        buy_weight = 0.0
        sell_weight = 0.0
        total_weight = 0.0
        
        for s_name, instance in self._strategies.items():
            if instance.status != StrategyStatus.ENABLED or not instance.instance:
                continue
                
            try:
                rates = await market_provider_manager.get_rates(symbol, "1m", count=50)
                if not rates:
                    continue
                df = pd.DataFrame(rates)
                
                # Phase 3: Multi-Timeframe Integration
                # We attempt to use MTF analysis if supported, otherwise fallback to standard analyze
                mtf_data = {"1m": df} # Mock MTF fetch - in a real scenario we'd pull H4, H1, M15
                signal = instance.instance.analyze_multi_timeframe(symbol, mtf_data)
                if not signal:
                    signal = instance.instance.analyze(symbol, df)
                
                if signal:
                    sig_dict = signal.model_dump() if hasattr(signal, 'model_dump') else signal.dict()
                    sig_dict["strategy_name"] = s_name
                    
                    vote_dir = sig_dict.get("direction", "WAIT")
                    weight = instance.weight * sig_dict.get("confidence", 0.5)
                    
                    if vote_dir == "BUY":
                        buy_weight += weight
                    elif vote_dir == "SELL":
                        sell_weight += weight
                        
                    total_weight += instance.weight
                    strategy_votes.append(sig_dict)
                    
            except Exception as e:
                logger.error(f"Strategy {s_name} analysis failed: {e}")
                
        if strategy_votes and total_weight > 0:
            consensus_dir = "WAIT"
            consensus_pct = 0.0
            
            if buy_weight > sell_weight and buy_weight >= (total_weight * 0.75):
                consensus_dir = "BUY"
                consensus_pct = buy_weight / total_weight
            elif sell_weight > buy_weight and sell_weight >= (total_weight * 0.75):
                consensus_dir = "SELL"
                consensus_pct = sell_weight / total_weight
                
            if consensus_dir != "WAIT":
                # Winning strategy is the one with highest confidence matching consensus
                matching_votes = [v for v in strategy_votes if v["direction"] == consensus_dir]
                winning_strategy = max(matching_votes, key=lambda x: x.get("confidence", 0)) if matching_votes else strategy_votes[0]
                
                final_signal = {
                    "signal_id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "asset": symbol,
                    "direction": consensus_dir,
                    "confidence": consensus_pct,
                    "strategy_name": "Consensus Engine",
                    "winning_strategy": winning_strategy["strategy_name"],
                    "strategy_votes": strategy_votes,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    
                    # Phase 1: Forward fields from winning strategy
                    "trade_quality": winning_strategy.get("trade_quality", "N/A"),
                    "expected_move_pct": winning_strategy.get("expected_move_pct"),
                    "expected_hold_hours": winning_strategy.get("expected_hold_hours"),
                    "market_regime": winning_strategy.get("market_regime"),
                    "volatility_pct": winning_strategy.get("volatility_pct")
                }
                
                self.recent_signals.insert(0, final_signal)
                if len(self.recent_signals) > 200:
                    self.recent_signals.pop()
                await event_bus.publish("SignalGenerated", payload=final_signal)

    async def start(self):
        if self._running:
            return
        self._running = True
        self.initialize_strategies()
        try:
            event_bus.subscribe("MarketDataTick", self._on_market_tick)
            logger.info("StrategyManager started and subscribed to MarketDataTick.")
        except Exception as e:
            logger.error(f"Failed to subscribe StrategyManager: {e}")

    async def stop(self):
        self._running = False
        self._strategies.clear()

    def get_recent_signals(self, limit: int = 50) -> list[dict]:
        return self.recent_signals[:limit]

    def enable_strategy(self, name: str) -> bool:
        if name in self._strategies:
            self._strategies[name].status = StrategyStatus.ENABLED
            strategy_registry.set_status(name, StrategyStatus.ENABLED)
            logger.info(f"Strategy {name} enabled")
            return True
        return False

    def disable_strategy(self, name: str) -> bool:
        if name in self._strategies:
            self._strategies[name].status = StrategyStatus.DISABLED
            strategy_registry.set_status(name, StrategyStatus.DISABLED)
            logger.info(f"Strategy {name} disabled")
            return True
        return False

    def pause_strategy(self, name: str) -> bool:
        if name in self._strategies:
            self._strategies[name].status = StrategyStatus.PAUSED
            strategy_registry.set_status(name, StrategyStatus.PAUSED)
            logger.info(f"Strategy {name} paused")
            return True
        return False

    def resume_strategy(self, name: str) -> bool:
        if name in self._strategies:
            self._strategies[name].status = StrategyStatus.ENABLED
            strategy_registry.set_status(name, StrategyStatus.ENABLED)
            logger.info(f"Strategy {name} resumed")
            return True
        return False

    def set_priority(self, name: str, priority: int) -> bool:
        if name in self._strategies:
            self._strategies[name].priority = priority
            strategy_registry.set_priority(name, priority)
            return True
        return False

    def set_weight(self, name: str, weight: float) -> bool:
        if name in self._strategies:
            self._strategies[name].weight = weight
            strategy_registry.set_weight(name, weight)
            return True
        return False

    def set_config(self, name: str, config: dict) -> bool:
        if name not in self._strategies:
            return False
        inst = self._strategies[name]
        if "priority" in config:
            inst.priority = int(config["priority"])
        if "weight" in config:
            inst.weight = float(config["weight"])
        if "max_concurrent_trades" in config:
            inst.max_concurrent_trades = int(config["max_concurrent_trades"])
        if "daily_trade_limit" in config:
            inst.daily_trade_limit = int(config["daily_trade_limit"])
        if "allowed_sessions" in config:
            inst.allowed_sessions = config["allowed_sessions"]
        if "allowed_assets" in config:
            inst.allowed_assets = config["allowed_assets"]
        if "allowed_timeframes" in config:
            inst.allowed_timeframes = config["allowed_timeframes"]
        if "min_trade_quality" in config:
            inst.min_trade_quality = int(config["min_trade_quality"])
        if "min_ai_confidence" in config:
            inst.min_ai_confidence = float(config["min_ai_confidence"])
        if "status" in config:
            status_map = {
                "ENABLED": StrategyStatus.ENABLED,
                "DISABLED": StrategyStatus.DISABLED,
                "PAUSED": StrategyStatus.PAUSED,
            }
            inst.status = status_map.get(config["status"], inst.status)
        return True

    def get_config(self, name: str) -> dict | None:
        if name not in self._strategies:
            return None
        inst = self._strategies[name]
        return {
            "name": inst.name,
            "status": inst.status.value,
            "priority": inst.priority,
            "weight": inst.weight,
            "max_concurrent_trades": inst.max_concurrent_trades,
            "daily_trade_limit": inst.daily_trade_limit,
            "allowed_sessions": inst.allowed_sessions,
            "allowed_assets": inst.allowed_assets,
            "allowed_timeframes": inst.allowed_timeframes,
            "min_trade_quality": inst.min_trade_quality,
            "min_ai_confidence": inst.min_ai_confidence,
            "current_trades": inst.current_trades,
            "daily_trades": inst.daily_trades,
            "last_signal": inst.last_signal,
        }

    def get_all_configs(self) -> list[dict]:
        result = []
        for name, inst in sorted(self._strategies.items(), key=lambda x: x[1].priority, reverse=True):
            meta = strategy_registry.get_metadata(name)
            result.append({
                "name": inst.name,
                "description": meta.description if meta else "",
                "version": meta.version if meta else "1.0.0",
                "category": meta.category.value if meta else "Hybrid",
                "status": inst.status.value,
                "priority": inst.priority,
                "weight": inst.weight,
                "risk_profile": meta.risk_profile.value if meta else "Medium",
                "supported_timeframes": meta.supported_timeframes if meta else [],
                "supported_assets": meta.supported_assets if meta else [],
                "required_indicators": meta.required_indicators if meta else [],
                "max_concurrent_trades": inst.max_concurrent_trades,
                "daily_trade_limit": inst.daily_trade_limit,
                "min_trade_quality": inst.min_trade_quality,
                "min_ai_confidence": inst.min_ai_confidence,
                "current_trades": inst.current_trades,
                "signals_today": inst.signals_today,
                "last_signal": inst.last_signal,
            })
        return result


strategy_manager = StrategyManager()
