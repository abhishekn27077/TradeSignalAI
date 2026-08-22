# Database models registry - imported by init_db to register with SQLAlchemy Base
from app.database.models.ai import (
    DecisionHistoryModel,
    ReasoningLogModel,
    TokenUsageModel,
)
from app.database.models.backtest import BacktestRun, BacktestTrade
from app.database.models.decision import DecisionHistoryModel
from app.database.models.forecast import (
    DailyOutlookModel,
    ForecastConsensusModel,
    ForecastEvaluationModel,
    ForecastModelMetadata,
    ForecastPerformanceModel,
    ForecastRequestModel,
    ForecastResultModel,
    WeeklyOutlookModel,
)
from app.database.models.journal import AIReview, Recommendation, TradeRecord, TradeTag
from app.database.models.market import (
    CandleModel,
    DataQualityReportModel,
    DataSyncJobModel,
    SymbolModel,
)
from app.database.models.news import HistoricalNews
from app.database.models.paper import PaperAccount, PaperOrder, PaperPosition
from app.database.models.prediction import PredictionRecord
from app.database.models.research import (
    BacktestResultModel,
    ConsensusEvaluationModel,
    ExperimentTrackingModel,
    ModelCalibrationModel,
)
from app.database.models.smc import (
    FVGModel,
    LiquidityZoneModel,
    MarketStructureModel,
    OrderBlockModel,
)
from app.database.models.strategy_config import (
    StrategyAnalyticsModel,
    StrategyConfigModel,
)
from app.database.models.strategy_lab import (
    StrategyBenchmarkModel,
    StrategyExperimentModel,
    StrategyLabModel,
    StrategyNotebookModel,
)
from app.database.models.validation import ResearchValidationRecord
from app.database.models.signal import SignalLifecycleModel
from app.database.models.user import UserModel

# Phase 40: Walk-Forward Forecasting & Economic Calendar
from app.database.models.forecast_snapshot import ForecastSnapshotModel
from app.database.models.economic_event import EconomicEventModel

# Phase 50: Actionable Signal & Trade Lifecycle Model
from app.database.models.actionable_signal import ActionableSignalModel
