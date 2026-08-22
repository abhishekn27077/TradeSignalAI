import importlib

from sqlalchemy import select

from app.database.manager import db_manager
from app.database.models.forecast import ForecastModelMetadata
from app.forecast_engine.base.provider import BaseForecastProvider
from app.logs.logger import get_logger

logger = get_logger(__name__)

class ModelRegistry:
    """
    Manages discovery, instantiation, and state of all forecasting models.
    """
    def __init__(self):
        self._providers_cache: dict[str, BaseForecastProvider] = {}
        self._provider_classes: dict[str, type[BaseForecastProvider]] = {}

    def register_provider_class(self, provider_name: str, provider_cls: type[BaseForecastProvider]):
        """Register a provider class in memory for later instantiation."""
        self._provider_classes[provider_name] = provider_cls

    async def initialize(self):
        """
        Loads the active models from the database, instantiates them,
        and initializes them for inference.
        """
        session_factory = db_manager.get_session()
        if not session_factory:
            logger.warning("DB not configured, cannot load Forecast Registry.")
            return

        async with session_factory() as session:
            # Get all enabled models
            result = await session.execute(
                select(ForecastModelMetadata).where(ForecastModelMetadata.is_enabled == True)
            )
            models_meta = result.scalars().all()

            for meta in models_meta:
                try:
                    provider_cls = self._load_class(meta.provider_class)
                    if not provider_cls:
                        logger.error(f"Failed to load provider class {meta.provider_class}")
                        continue
                        
                    provider_instance = provider_cls(model_id=meta.id, config=meta.config)
                    success = await provider_instance.initialize()
                    
                    if success:
                        self._providers_cache[meta.id] = provider_instance
                        meta.health_status = "healthy"
                    else:
                        meta.health_status = "degraded"
                        logger.warning(f"Provider {meta.name} failed initialization.")
                        
                except Exception as e:
                    meta.health_status = "offline"
                    logger.error(f"Error loading provider {meta.name}: {e}")
            
            await session.commit()
            logger.info(f"Forecast Model Registry initialized with {len(self._providers_cache)} active providers.")

    def _load_class(self, class_path: str) -> type[BaseForecastProvider] | None:
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Failed to import {class_path}: {e}")
            return None

    def get_provider(self, model_id: str) -> BaseForecastProvider | None:
        return self._providers_cache.get(model_id)

    def get_all_active_providers(self) -> list[BaseForecastProvider]:
        return list(self._providers_cache.values())

    async def ensure_default_providers(self):
        """
        Populate the database with the default providers if they don't exist.
        """
        session_factory = db_manager.get_session()
        if not session_factory:
            return

        defaults = [
            {"name": "Kronos-V1", "class": "app.forecast_engine.providers.kronos_provider.KronosProvider", "priority": 1},
            {"name": "XGBoost-Ensemble", "class": "app.forecast_engine.providers.xgboost_provider.XGBoostProvider", "priority": 2},
            {"name": "RandomForest-Standard", "class": "app.forecast_engine.providers.random_forest_provider.RandomForestProvider", "priority": 3},
            {"name": "Transformer-Alpha", "class": "app.forecast_engine.providers.transformer_provider.TransformerProvider", "priority": 4},
            {"name": "Prophet-Baseline", "class": "app.forecast_engine.providers.prophet_provider.ProphetProvider", "priority": 5},
            {"name": "Statistical-ARIMA", "class": "app.forecast_engine.providers.statistical_provider.StatisticalProvider", "priority": 6},
            {"name": "RuleBased-Heuristic", "class": "app.forecast_engine.providers.rule_based_provider.RuleBasedProvider", "priority": 7},
        ]

        async with session_factory() as session:
            try:
                for default in defaults:
                    existing = await session.execute(
                        select(ForecastModelMetadata).where(ForecastModelMetadata.name == default["name"])
                    )
                    if not existing.scalar():
                        new_meta = ForecastModelMetadata(
                            name=default["name"],
                            provider_class=default["class"],
                            priority=default["priority"],
                            is_enabled=True,
                            health_status="unknown"
                        )
                        session.add(new_meta)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to ensure default providers: {e}")

model_registry = ModelRegistry()
