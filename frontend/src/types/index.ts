export interface Ticker {
  symbol: string;
  price: number;
  change24h: number;
  changePct24h: number;
  volume: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  bid: number;
  ask: number;
  timestamp: number;
}

export interface OHLCV {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderBookLevel {
  price: number;
  size: number;
  total: number;
}

export type AgentStatus = 'thinking' | 'confident' | 'waiting' | 'error';
export type AgentDecision = 'BUY' | 'SELL' | 'WAIT';

export interface AIAgent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  confidence: number;
  decision: AgentDecision;
  reasoning: string;
  lastUpdated: number;
  performanceScore: number;
}

export interface AIConsensus {
  decision: AgentDecision;
  overallConfidence: number;
  agents: AIAgent[];
  riskSummary: string;
  newsSummary: string;
  technicalSummary: string;
  timestamp: number;
}

export interface Signal {
  id: string;
  strategy: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  strength: number;
  price: number;
  timestamp: number;
  indicators: Record<string, number>;
}

export interface StrategyConfig {
  name: string;
  description: string;
  version: string;
  category: string;
  status: 'ENABLED' | 'DISABLED' | 'PAUSED';
  priority: number;
  weight: number;
  risk_profile: string;
  supported_timeframes: string[];
  supported_assets: string[];
  required_indicators: string[];
  max_concurrent_trades: number;
  daily_trade_limit: number;
  min_trade_quality: number;
  min_ai_confidence: number;
  current_trades: number;
  signals_today: number;
  last_signal: any;
  entry_rules?: string[];
  exit_rules?: string[];
  supported_regimes?: string[];
}

export interface StrategyAnalytics {
  strategy_name: string;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  avg_profit: number;
  avg_loss: number;
  avg_hold_time_minutes: number;
  avg_r_multiple: number;
  total_pnl: number;
  regime_performance: Record<string, any>;
  asset_performance: Record<string, any>;
  best_asset: string;
  worst_asset: string;
}

export interface LiveSignal {
  signal: any;
  prediction: {
    expected_direction: string;
    bullish_probability: number;
    bearish_probability: number;
    expected_holding_hours: number;
    expected_move_pct: number;
    expected_price_range: [number, number];
    expected_volatility: number;
    confidence: number;
    reasoning: string;
  };
  trade_quality: {
    score: number;
    grade: string;
    details: { score: number; grade: string; verdict: string; breakdown: Record<string, number> };
  };
  ai_validation: {
    decision: string;
    confidence_adjustment: number;
    reasoning: string;
    risk_summary: string;
    alternative_scenario: string;
  };
}

export interface OptimizerRecommendation {
  strategy_name: string;
  recommendations: string[];
  urgency: string;
  reasoning: string;
}

export interface Forecast {
  symbol: string;
  timeframe: string;
  direction: string;
  confidence: number;
  price_target: number | null;
  stop_level: number | null;
  expected_move_pct: number;
  expected_holding_hours: number;
  model_name: string;
  features_used: string[];
  timestamp: string;
}

export interface Position {
  id: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
  openedAt: number;
}

export interface Order {
  id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP';
  status: 'PENDING' | 'SUBMITTED' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  quantity: number;
  price: number;
  filledPrice?: number;
  createdAt: number;
}

export interface PortfolioSummary {
  totalEquity: number;
  totalPnl: number;
  totalPnlPct: number;
  dailyPnl: number;
  dailyPnlPct: number;
  openPositions: number;
  drawdown: number;
  maxDrawdown: number;
}

export interface RiskMetrics {
  portfolioVaR: number;
  var1d?: number;
  sharpeRatio: number;
  maxDrawdown: number;
  currentDrawdown: number;
  leverageUsed: number;
  leverage?: number;
  maxLeverage: number;
  riskScore: number;
  exposureLong: number;
  exposureShort: number;
  exposureNet: number;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  impact: 'high' | 'medium' | 'low';
  affectedAssets: string[];
  publishedAt: number;
  summary: string;
}

export interface JournalEntry {
  id: string;
  tradeId: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  pnl: number;
  aiDecision: AgentDecision;
  aiConfidence: number;
  lessons: string[];
  timestamp: number;
}

export type HealthStatus = 'online' | 'degraded' | 'offline';

export interface SystemHealth {
  api: HealthStatus;
  database: HealthStatus;
  websocket: HealthStatus;
  marketFeed: HealthStatus;
  aiEngine: HealthStatus;
  brokerConnection: HealthStatus;
  latencyMs: number;
  apiLatency?: number;
  wsLatency?: number;
  aiLatency?: number;
  feedLatency?: number;
  brokerLatency?: number;
  avgLatency?: number;
  cpuUsage: number;
  memoryUsage: number;
  memoryTotal?: number;
  uptime: string | number;
}

export type PanelId =
  | 'chart'
  | 'orderbook'
  | 'watchlist'
  | 'positions'
  | 'orders'
  | 'signals'
  | 'aiCommand'
  | 'news'
  | 'risk'
  | 'journal';
