import React, { useEffect } from 'react';
import { TopToolbar } from './components/layout/TopToolbar';
import { Sidebar } from './components/layout/Sidebar';
import { StatusBar } from './components/layout/StatusBar';
import { useAppStore } from './store/useAppStore';

/* ── New Trading Terminal Pages ─────────────────────────────────────────── */
import { TradeSignalTerminal } from './pages/signals/TradeSignalTerminal';
import { TradingDashboard } from './pages/TradingDashboard';
import { TodaysSignals } from './pages/signals/TodaysSignals';
import { H4ForecastsPage as H4ForecastsNew } from './pages/signals/H4Forecasts';
import { SwingSignals } from './pages/signals/SwingSignals';
import { SignalHistory } from './pages/signals/SignalHistory';
import { SignalFeedSchedule } from './pages/signals/SignalFeedSchedule';

/* ── Existing Pages (preserved for Admin mode) ─────────────────────────── */
import { TerminalPage } from './pages/Terminal';
import { AICommandPage } from './pages/AICommand';
import { PortfolioPage } from './pages/Portfolio';
import { RiskPage } from './pages/Risk';
import { JournalPage } from './pages/Journal';
import { SystemPage } from './pages/System';
import { StrategiesPage } from './pages/Strategies';
import { SignalsPage } from './pages/Signals';
import { NewsPage } from './pages/News';
import { ExecutionPage } from './pages/Execution';
import { MemoryPage } from './pages/Memory';
import { QualificationPage } from './pages/Qualification';
import { MarketDatabasePage } from './pages/forecast/MarketDatabase';
import { DataManagerPage } from './pages/forecast/DataManager';
import { FeatureStorePage } from './pages/forecast/FeatureStore';
import { Dashboard } from './pages/forecast/Dashboard';
import { PredictionCenterPage } from './pages/forecast/PredictionCenter';
import { H4ForecastsPage } from './pages/forecast/H4Forecasts';
import { SwingScanner } from './pages/forecast/SwingScanner';
import { OpportunityRanking } from './pages/forecast/OpportunityRanking';
import { DailyOutlook } from './pages/forecast/DailyOutlook';
import { WeeklyOutlook } from './pages/forecast/WeeklyOutlook';
import { ModelPerformance } from './pages/forecast/ModelPerformance';
import { TradeScheduleCenter } from './pages/forecast/TradeScheduleCenter';
import { MarketHeatmap } from './pages/forecast/MarketHeatmap';
import { ForecastValidation } from './pages/forecast/ForecastValidation';
import { ForecastArchive } from './pages/forecast/ForecastArchive';

// Research Pages
import { EnterpriseBacktest } from './pages/research/EnterpriseBacktest';
import { HistoricalReplay } from './pages/research/HistoricalReplay';
import { ModelComparisonLab } from './pages/research/ModelComparisonLab';
import { HyperparameterLab } from './pages/research/HyperparameterLab';
import { AIResearchDashboard } from './pages/research/AIResearchDashboard';
import { ModelLeaderboard } from './pages/research/ModelLeaderboard';

// Decision Intelligence Layer
import { DecisionDashboard } from './pages/decision/DecisionDashboard';
import { DecisionHistory } from './pages/decision/DecisionHistory';

// Market Intelligence (Phase 8)
import { MarketCommandCenter } from './pages/market_intelligence/MarketCommandCenter';
import { MarketStructureIntelligence } from './pages/market_intelligence/MarketStructureIntelligence';
import { CurrencyStrength } from './pages/market_intelligence/CurrencyStrength';
import { CorrelationMatrix } from './pages/market_intelligence/CorrelationMatrix';
import { PortfolioIntelligence } from './pages/market_intelligence/PortfolioIntelligence';
import { CapitalAllocation } from './pages/market_intelligence/CapitalAllocation';
import { ExposureMonitor } from './pages/market_intelligence/ExposureMonitor';
import { AIPortfolioManager } from './pages/market_intelligence/AIPortfolioManager';
import { SectorRotation } from './pages/market_intelligence/SectorRotation';
import { OpportunityExplorer } from './pages/market_intelligence/OpportunityExplorer';
import { GlobalRiskDashboard } from './pages/market_intelligence/GlobalRiskDashboard';

// Enterprise (Phase 10)
import { SystemHealth } from './pages/enterprise/SystemHealth';
import { AuditLog } from './pages/enterprise/AuditLog';
import { ConfigurationCenter } from './pages/enterprise/ConfigurationCenter';
import { PluginManager } from './pages/enterprise/PluginManager';

// Strategy Lab (Phase 11)
import StrategyLabDashboard from './pages/strategy_lab/StrategyLabDashboard';
import StrategyBuilder from './pages/strategy_lab/StrategyBuilder';
import StrategyLibrary from './pages/strategy_lab/StrategyLibrary';
import FeatureImportance from './pages/strategy_lab/FeatureImportance';
import ExperimentManager from './pages/strategy_lab/ExperimentManager';
import ResearchNotebook from './pages/strategy_lab/ResearchNotebook';
import BenchmarkCenter from './pages/strategy_lab/BenchmarkCenter';
import AIRecommendations from './pages/strategy_lab/AIRecommendations';

// Phase 40, 41, 42, 43, 44, 45 & 46: Forecast Intelligence, Shadow Validation & Live Edge Evidence
import { TomorrowForecast } from './pages/forecasts/TomorrowForecast';
import { EconomicCalendar } from './pages/calendar/EconomicCalendar';
import { NewsIntelligence } from './pages/news/NewsIntelligence';
import { PredictionLedger } from './pages/forecasts/PredictionLedger';
import { PredictionLab } from './pages/forecasts/PredictionLab';
import { Phase43ShadowDashboard } from './pages/forecasts/Phase43ShadowDashboard';
import { RealityEvidenceDashboard } from './pages/forecasts/RealityEvidenceDashboard';
import { DailyCommandCenter } from './pages/forecasts/DailyCommandCenter';
import { LiveEdgeEvidence } from './pages/forecasts/LiveEdgeEvidence';
import { ValidationPage } from './pages/ValidationPage';
import { ShadowLivePage } from './pages/ShadowLivePage';

const pageMap: Record<string, React.FC> = {
  /* ── Phase 69A Primary Trade Signal Terminal ─────────────────────── */
  'trade-terminal': TradeSignalTerminal,
  'terminal': TradeSignalTerminal,
  'signal-feed-schedule': TradeSignalTerminal,
  'signals-feed': TradeSignalTerminal,
  'signals': TradeSignalTerminal,
  'todays-signals': TradeSignalTerminal,

  /* ── Phase 71 Live Validation & Diagnostics ──────────────────────── */
  'validation': ValidationPage,
  'live-validation': ValidationPage,

  /* ── Phase 72 Shadow-Live Trading ────────────────────────────────── */
  'shadow-live': ShadowLivePage,
  'shadow': ShadowLivePage,

  /* ── Secondary Dashboard & Analytic Pages ────────────────────────── */
  'dashboard': TradingDashboard,
  'h4-forecasts-new': H4ForecastsNew,
  'swing-signals': SwingSignals,
  'signal-history': SignalHistory,

  /* ── Existing Pages (Admin) ──────────────────────────────────────── */
  'admin-terminal': TerminalPage,
  'ai-command': AICommandPage,
  strategies: StrategiesPage,
  'admin-signals': SignalsPage,
  news: NewsPage,
  portfolio: PortfolioPage,
  risk: RiskPage,
  execution: ExecutionPage,
  journal: JournalPage,
  memory: MemoryPage,
  system: SystemPage,
  qualification: QualificationPage,
  'market-database': MarketDatabasePage,
  'data-manager': DataManagerPage,
  'feature-store': FeatureStorePage,
  'forecast-dashboard': Dashboard,
  'prediction-center': PredictionCenterPage,
  'h4-forecasts': H4ForecastsPage,
  'swing-scanner': SwingScanner,
  'opportunity-ranking': OpportunityRanking,
  'daily-outlook': DailyOutlook,
  'weekly-outlook': WeeklyOutlook,
  'model-performance': ModelPerformance,
  'trade-schedule': TradeScheduleCenter,
  'market-heatmap': MarketHeatmap,
  'forecast-validation': ForecastValidation,
  'forecast-archive': ForecastArchive,
  'enterprise-backtest': EnterpriseBacktest,
  'historical-replay': HistoricalReplay,
  'model-comparison': ModelComparisonLab,
  'hyperparameter-lab': HyperparameterLab,
  'ai-research-dashboard': AIResearchDashboard,
  'model-leaderboard': ModelLeaderboard,
  'decision-dashboard': DecisionDashboard,
  'decision-history': DecisionHistory,
  'market-command': MarketCommandCenter,
  'market-structure': MarketStructureIntelligence,
  'phase51-intelligence': MarketStructureIntelligence,
  'currency-strength': CurrencyStrength,
  'correlation-matrix': CorrelationMatrix,
  'portfolio-intel': PortfolioIntelligence,
  'capital-allocation': CapitalAllocation,
  'exposure-monitor': ExposureMonitor,
  'ai-portfolio-manager': AIPortfolioManager,
  'sector-rotation': SectorRotation,
  'opportunity-explorer': OpportunityExplorer,
  'global-risk': GlobalRiskDashboard,
  'system-health': SystemHealth,
  'audit-log': AuditLog,
  'config-center': ConfigurationCenter,
  'plugin-manager': PluginManager,
  'strategy-lab': StrategyLabDashboard,
  'strategy-builder': StrategyBuilder,
  'strategy-library': StrategyLibrary,
  'feature-importance': FeatureImportance,
  'experiment-manager': ExperimentManager,
  'research-notebook': ResearchNotebook,
  'benchmark-center': BenchmarkCenter,
  'ai-recommendations': AIRecommendations,

  /* ── Phase 40, 41, 42, 43, 44, 45 & 46: Forecast Intelligence & Live Edge Evidence ────────── */
  'tomorrow-forecast': TomorrowForecast,
  'economic-calendar': EconomicCalendar,
  'news-intelligence': NewsIntelligence,
  'prediction-ledger': PredictionLedger,
  'prediction-lab': PredictionLab,
  'phase43-shadow': Phase43ShadowDashboard,
  'reality-evidence': RealityEvidenceDashboard,
  'daily-command': DailyCommandCenter,
  'phase45-daily': DailyCommandCenter,
  'live-edge': LiveEdgeEvidence,
  'phase46-evidence': LiveEdgeEvidence,
};

import { ErrorBoundary } from './components/common/ErrorBoundary';

const App: React.FC = () => {
  const activePage = useAppStore((s) => s.activePage);
  const initialize = useAppStore((s) => s.initialize);
  const ActivePage = pageMap[activePage] ?? TradingDashboard;

  useEffect(() => {
    initialize();
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-trading-dark">
      <TopToolbar />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-y-auto">
          <ErrorBoundary fallbackTitle="Unable to display this view">
            <ActivePage />
          </ErrorBoundary>
        </main>
      </div>
      <StatusBar />
    </div>
  );
};

export default App;
