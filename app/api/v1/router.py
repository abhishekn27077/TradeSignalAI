from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.brokers import router as brokers_router
from app.api.v1.execution import router as execution_router
from app.api.v1.extensions import router as extensions_router
from app.api.v1.forecast import router as forecast_router

from .agents import router as agents_router
from .auth import router as auth_router
from .backtest import router as backtest_router
from .data import router as data_router
from .health import router as health_router
from .journal import router as journal_router
from .market import router as market_router
from .memory import router as memory_router
from .news import router as news_router
from .paper import router as paper_router
from .portfolio import router as portfolio_router
from .qualification import router as qualification_router
from .risk import router as risk_router
from .signals import router as signals_router
from .strategies import router as strategies_router
from .ws import router as ws_router
from .jobs import router as jobs_router
from .forward_validation import router as forward_validation_router

# Main v1 router
api_v1_router = APIRouter()

# Register sub-routers
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(ws_router)
api_v1_router.include_router(health_router, prefix="/system")
api_v1_router.include_router(jobs_router, prefix="/system")
api_v1_router.include_router(market_router)
api_v1_router.include_router(agents_router)

api_v1_router.include_router(strategies_router)
# Phase 50: Actionable Trade Timing, Revalidation & Position Lifecycle
from app.api.v1.actionable_routes import router as phase50_actionable_router
# Phase 51: Market Intelligence, SMC, Confluence & Analysis Routes
from app.api.v1.analysis_routes import router as phase51_analysis_router

# Sub-router inclusions (Actionable and Analysis routes take precedence over generic {signal_id})
api_v1_router.include_router(phase50_actionable_router)
api_v1_router.include_router(phase51_analysis_router)
api_v1_router.include_router(signals_router)


api_v1_router.include_router(news_router)
api_v1_router.include_router(backtest_router)
api_v1_router.include_router(paper_router)
api_v1_router.include_router(journal_router)
api_v1_router.include_router(memory_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(portfolio_router)
api_v1_router.include_router(execution_router)
api_v1_router.include_router(brokers_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(extensions_router)
api_v1_router.include_router(forecast_router)
api_v1_router.include_router(qualification_router)
api_v1_router.include_router(data_router)

# Forecast Intelligence Sub-routers
from app.api.v1.forecast_routes.heatmap import router as forecast_heatmap_router
from app.api.v1.forecast_routes.outlook import router as forecast_outlook_router
from app.api.v1.forecast_routes.predictions import router as forecast_predictions_router
from app.api.v1.forecast_routes.scanners import router as forecast_scanners_router
from app.api.v1.forecast_routes.schedule import router as forecast_schedule_router

api_v1_router.include_router(forecast_predictions_router, prefix="/forecast")
api_v1_router.include_router(forecast_outlook_router, prefix="/forecast")
api_v1_router.include_router(forecast_scanners_router, prefix="/forecast")
api_v1_router.include_router(forecast_schedule_router, prefix="/forecast/schedule")
api_v1_router.include_router(forecast_heatmap_router, prefix="/forecast/heatmap")
# Quantitative Research Routes
from app.api.v1.enterprise_routes import router as enterprise_router
from app.api.v1.research_routes.backtest import router as research_backtest_router
from app.api.v1.research_routes.evaluation import router as research_evaluation_router
from app.api.v1.research_routes.experiments import router as research_experiments_router
from app.api.v1.research_routes.models import router as research_models_router
from app.api.v1.research_routes.replay import router as research_replay_router
from app.api.v1.research_routes.reports import router as research_reports_router

api_v1_router.include_router(research_backtest_router, prefix="/research/backtest", tags=["Research"])
api_v1_router.include_router(research_replay_router, prefix="/research/replay", tags=["Research"])
api_v1_router.include_router(research_evaluation_router, prefix="/research/evaluation", tags=["Research"])
api_v1_router.include_router(research_models_router, prefix="/research/models", tags=["Research"])
api_v1_router.include_router(research_experiments_router, prefix="/research/experiments", tags=["Research"])
api_v1_router.include_router(research_reports_router, prefix="/research/reports", tags=["Research"])
api_v1_router.include_router(enterprise_router, prefix="/enterprise", tags=["Enterprise Operations"])

# AI Strategy Laboratory (Phase 11)
from app.api.v1.strategy_lab.benchmarks import router as strategy_benchmarks_router
from app.api.v1.strategy_lab.builder import router as strategy_builder_router
from app.api.v1.strategy_lab.features import router as strategy_features_router
from app.api.v1.strategy_lab.library import router as strategy_library_router
from app.api.v1.strategy_lab.notebook import router as strategy_notebook_router
from app.api.v1.strategy_lab.recommendations import (
    router as strategy_recommendations_router,
)

api_v1_router.include_router(strategy_library_router, prefix="/strategy-lab/library", tags=["AI Strategy Lab"])
api_v1_router.include_router(strategy_builder_router, prefix="/strategy-lab/builder", tags=["AI Strategy Lab"])
api_v1_router.include_router(strategy_features_router, prefix="/strategy-lab/features", tags=["AI Strategy Lab"])
api_v1_router.include_router(strategy_notebook_router, prefix="/strategy-lab/notebook", tags=["AI Strategy Lab"])
api_v1_router.include_router(strategy_benchmarks_router, prefix="/strategy-lab/benchmarks", tags=["AI Strategy Lab"])
api_v1_router.include_router(strategy_recommendations_router, prefix="/strategy-lab/recommendations", tags=["AI Strategy Lab"])

# Decision Intelligence Routes
from app.api.v1.decision_routes import router as decision_router

api_v1_router.include_router(decision_router, prefix="/decision", tags=["Decision Intelligence"])

# Validation Routes
from app.api.v1.validation_routes import router as validation_router

api_v1_router.include_router(validation_router, prefix="/validation", tags=["Validation"])

api_v1_router.include_router(forward_validation_router)

# Phase 40: Forecast Intelligence & Economic Calendar
from app.api.v1.forecast_intelligence_routes import router as phase40_forecast_router
from app.api.v1.calendar_routes import router as calendar_router

api_v1_router.include_router(phase40_forecast_router, tags=["Forecast Intelligence"])
api_v1_router.include_router(calendar_router, tags=["Economic Calendar"])

# Phase 41 & 42: Data Intelligence, Model Health, Ablation & Diagnostics
from app.api.v1.intelligence_routes import router as intelligence_router

api_v1_router.include_router(intelligence_router, tags=["Data Intelligence & Model Health"])

# Phase 43: Autonomous Live Shadow / Paper-Trading Validation & Statistical Edge
from app.api.v1.shadow_validation_routes import router as phase43_shadow_router

api_v1_router.include_router(phase43_shadow_router, tags=["Phase 43 Shadow Validation"])

# Phase 44: Live Reality Audit, Evidence Provenance & Forward-Edge Verification
from app.api.v1.reality_audit_routes import router as phase44_reality_router

api_v1_router.include_router(phase44_reality_router, tags=["Phase 44 Reality & Evidence Audit"])

# Phase 45: Live Daily Command Center & Forward Forecasting
from app.api.v1.live_command_routes import router as phase45_live_router

api_v1_router.include_router(phase45_live_router, tags=["Phase 45 Live Daily Command Center"])

# Phase 46: Forward-Edge Statistical Validation & Live Performance Governance
from app.api.v1.evidence_routes import router as phase46_evidence_router

api_v1_router.include_router(phase46_evidence_router, tags=["Phase 46 Live Statistical Evidence"])

# Phase 47: Unified Runtime Diagnostics & Error Observability
from app.api.v1.runtime_diagnostics import router as phase47_diagnostics_router

api_v1_router.include_router(phase47_diagnostics_router, tags=["Phase 47 Runtime Diagnostics"])


