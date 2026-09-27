import { create } from 'zustand';
import { api } from '../services/api-client';
import { wsManager } from '../services/websocket-manager';
import type { SystemHealth,
  Ticker, Position, Order, AIConsensus, AIAgent,
  PortfolioSummary, RiskMetrics, NewsItem, Signal, 
} from '../types';

interface AppState {
  sidebarCollapsed: boolean;
  activePage: string;
  activeAsset: string;
  adminMode: boolean;
  toggleSidebar: () => void;
  setActivePage: (page: string) => void;
  setActiveAsset: (asset: string) => void;
  toggleAdminMode: () => void;

  tickers: Record<string, Ticker>;
  updateTicker: (t: Ticker) => void;

  portfolio: PortfolioSummary;
  positions: Position[];
  orders: Order[];
  setPortfolio: (p: PortfolioSummary) => void;
  setPositions: (p: Position[]) => void;
  setOrders: (o: Order[]) => void;
  refreshOrders: () => Promise<void>;
  refreshPositions: () => Promise<void>;
  refreshPortfolio: () => Promise<void>;

  aiConsensus: AIConsensus | null;
  aiAgents: AIAgent[];
  setAIConsensus: (c: AIConsensus) => void;
  setAIAgents: (a: AIAgent[]) => void;
  refreshAgents: () => Promise<void>;
  initializeAgents: () => Promise<void>;

  riskMetrics: RiskMetrics | null;
  setRiskMetrics: (r: RiskMetrics) => void;
  refreshRisk: () => Promise<void>;

  signals: Signal[];
  addSignal: (s: Signal) => void;
  refreshSignals: () => Promise<void>;

  news: NewsItem[];
  setNews: (n: NewsItem[]) => void;
  refreshNews: () => Promise<void>;

  systemHealth: SystemHealth | null;
  setSystemHealth: (h: SystemHealth) => void;
  refreshSystemHealth: () => Promise<void>;

  marketRegime: any;
  aiLearningStats: any;
  advancedRisk: any;
  refreshExtensions: () => Promise<void>;

  initialized: boolean;
  initialize: () => Promise<void>;
}

function mapPosition(p: any): Position {
  return {
    id: p.id || p.ticket || `${p.symbol}-${Date.now()}`,
    symbol: p.symbol || '',
    direction: p.direction || p.type || (p.pnl >= 0 ? 'LONG' : 'SHORT'),
    quantity: p.quantity || p.qty || p.volume || 0,
    entryPrice: p.entry_price || p.entryPrice || p.price_open || 0,
    currentPrice: p.current_price || p.currentPrice || p.price_current || 0,
    pnl: p.pnl || p.profit || 0,
    pnlPct: p.pnlPct ?? p.pnl_percent ?? 0,
    openedAt: p.opened_at || p.openedAt || p.time || Date.now(),
  };
}

function mapOrder(o: any): Order {
  return {
    id: o.id || o.ticket || `${Date.now()}`,
    symbol: o.symbol || '',
    direction: o.direction || o.type || 'BUY',
    type: o.type === 'LIMIT' ? 'LIMIT' : o.type === 'STOP' ? 'STOP' : 'MARKET',
    status: o.status || 'PENDING',
    quantity: o.quantity || o.qty || o.volume || 0,
    price: o.price || 0,
    filledPrice: o.filled_price || o.filledPrice,
    createdAt: o.created_at || o.createdAt || o.time_open || Date.now(),
  };
}

function mapSignal(s: any): Signal {
  return {
    id: s.id || s.signal_id || `${Date.now()}`,
    strategy: s.strategy || s.strategy_name || '',
    symbol: s.symbol || s.asset || '',
    direction: s.direction === 'SELL' ? 'SELL' : 'BUY',
    strength: typeof s.confidence === 'number' ? s.confidence * 100 : (s.strength ?? s.score ?? null),
    price: s.price || (s.entry_zone ? s.entry_zone[0] : 0),
    timestamp: typeof s.timestamp === 'string' ? new Date(s.timestamp).getTime() : (s.timestamp ?? Date.now()),
    indicators: s.indicators || s.supporting_indicators || {},
  };
}

function mapNewsItem(n: any): NewsItem {
  const now = Date.now();
  const ts = n.published_at || n.publishedAt || n.timestamp || n.date || now;
  return {
    id: n.id || `${now}-${Math.random().toString(36).slice(2, 6)}`,
    title: n.title || n.headline || '',
    source: n.source || '',
    sentiment: n.sentiment || 'neutral',
    impact: n.impact || 'medium',
    affectedAssets: n.affected_assets || n.affectedAssets || n.symbols || [],
    publishedAt: typeof ts === 'number' ? ts : new Date(ts).getTime(),
    summary: n.summary || n.ai_summary || n.aiSummary || n.description || '',
  };
}

export const useAppStore = create<AppState>((set, get) => ({
  sidebarCollapsed: false,
  activePage: 'today',
  activeAsset: 'ALL',
  adminMode: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setActivePage: (page) => set({ activePage: page }),
  setActiveAsset: (asset) => set({ activeAsset: asset }),
  toggleAdminMode: () => set((state) => ({ adminMode: !state.adminMode })),

  tickers: {},
  updateTicker: (t) =>
    set((s) => ({ tickers: { ...s.tickers, [t.symbol]: t } })),

  portfolio: {
    totalEquity: 0, totalPnl: 0, totalPnlPct: 0,
    dailyPnl: 0, dailyPnlPct: 0, openPositions: 0,
    drawdown: 0, maxDrawdown: 0,
  },
  positions: [],
  orders: [],
  setPortfolio: (p) => set({ portfolio: p }),
  setPositions: (p) => set({ positions: p }),
  setOrders: (o) => set({ orders: o }),

  refreshOrders: async () => {
    try {
      const data = await api.execution.orders();
      set({ orders: data.map(mapOrder) });
    } catch { /* offline */ }
  },
  refreshPositions: async () => {
    try {
      const data = await api.execution.positions();
      set({ positions: data.map(mapPosition) });
    } catch { /* offline */ }
  },
  refreshPortfolio: async () => {
    try {
      const bal = await api.execution.balance();
      const perf = await api.analytics.performance();
      set({
        portfolio: {
          totalEquity: bal.equity ?? bal.balance ?? perf.total_equity ?? 0,
          totalPnl: perf.net_profit ?? bal.profit ?? 0,
          totalPnlPct: perf.return_pct ?? 0,
          dailyPnl: perf.daily_pnl ?? bal.daily_pnl ?? 0,
          dailyPnlPct: perf.daily_pnl_pct ?? 0,
          openPositions: perf.open_positions ?? 0,
          drawdown: perf.max_drawdown_percent ?? bal.drawdown ?? 0,
          maxDrawdown: perf.max_drawdown ?? bal.max_drawdown ?? 0,
        },
      });
    } catch { /* offline */ }
  },

  aiConsensus: null,
  aiAgents: [],
  setAIConsensus: (c) => set({ aiConsensus: c }),
  setAIAgents: (a) => set({ aiAgents: a }),
  initializeAgents: async () => {
      try {
        const agents = await api.agents.initialize();
        set({ aiAgents: Array.isArray(agents) ? agents.map((a: any) => ({
          id: a.id || a.role || `${Date.now()}`,
          name: a.name || a.role || 'Agent',
          role: a.role || 'Analyst',
          status: a.status || 'waiting',
          confidence: a.confidence ?? null,
          decision: a.decision || 'WAIT',
          reasoning: a.reasoning || '',
          lastUpdated: a.last_updated ?? Date.now(),
          performanceScore: a.performance_score ?? a.performanceScore ?? 0,
        })) : [],
        });
      } catch { /* offline */ }
    },
    refreshAgents: async () => {
    try {
      const agents = await api.agents.status();
      set({ aiAgents: Array.isArray(agents) ? agents.map((a: any) => ({
        id: a.id || a.role || `${Date.now()}`,
        name: a.name || a.role || 'Agent',
        role: a.role || 'Analyst',
        status: a.status || 'waiting',
        confidence: a.confidence ?? null,
        decision: a.decision || 'WAIT',
        reasoning: a.reasoning || '',
        lastUpdated: a.last_updated ?? Date.now(),
        performanceScore: a.performance_score ?? a.performanceScore ?? 0,
      })) : [],
      });
    } catch { /* offline */ }
  },

  riskMetrics: null,
  setRiskMetrics: (r) => set({ riskMetrics: r }),
  refreshRisk: async () => {
    try {
      const limits = await api.risk.limits();
      const status = limits;
      const limArr = Object.entries(limits);
      const maxDrawdown = (limArr.find(([k]) => k.includes('drawdown'))?.[1] as any)?.current ?? 0;
      const maxLev = (limArr.find(([k]) => k.includes('leverage'))?.[1] as any)?.threshold ?? 3;
      const currLev = (limArr.find(([k]) => k.includes('leverage'))?.[1] as any)?.current ?? 1;
      set({
        riskMetrics: {
          portfolioVaR: 0,
          var1d: (limArr.find(([k]) => k.includes('var'))?.[1] as any)?.current ?? 0,
          sharpeRatio: 0,
          maxDrawdown,
          currentDrawdown: maxDrawdown,
          leverageUsed: currLev,
          leverage: currLev,
          maxLeverage: maxLev,
          riskScore: (status as any)?.status === 'ALERT' ? 85 : 32,
          exposureLong: 0,
          exposureShort: 0,
          exposureNet: 0,
        },
      });
    } catch { /* offline */ }
  },

  signals: [],
  addSignal: (s) => set((st) => ({ signals: [s, ...st.signals].slice(0, 200) })),
  refreshSignals: async () => {
    try {
      const history = await api.signals.history(50);
      set({ signals: history.map(mapSignal) });
    } catch { /* offline */ }
  },

  news: [],
  setNews: (n) => set({ news: n }),
  refreshNews: async () => {
    try {
      const items = await api.news.latest();
      set({ news: items.map(mapNewsItem) });
    } catch { /* offline */ }
  },

  systemHealth: null,
  setSystemHealth: (h) => set({ systemHealth: h }),
  refreshSystemHealth: async () => {
    try {
      const data = await api.health.status();
      const components = (data as any)?.components || {};
      const toStatus = (v: string) => (v === 'ok' || v === 'online' || v === 'connected' || v === 'standby') ? 'online' as const : (v === 'uninitialized' || v === 'degraded') ? 'degraded' as const : 'offline' as const;
      set({
        systemHealth: {
          api: 'online',
          database: toStatus(components.database),
          websocket: wsManager.isConnected ? 'online' : (components.websocket === 'ok' || components.websocket === 'standby' ? 'online' : 'offline'),
          marketFeed: toStatus(components.market_feed),
          aiEngine: toStatus(components.ai_engine),
          brokerConnection: toStatus(components.broker_api),
          latencyMs: 0,
          avgLatency: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          memoryTotal: 0,
          uptime: '',
        },
      });
    } catch {
      set({
        systemHealth: {
          api: 'offline', database: 'offline', websocket: 'offline',
          marketFeed: 'offline', aiEngine: 'offline', brokerConnection: 'offline',
          latencyMs: 0, avgLatency: 0, cpuUsage: 0, memoryUsage: 0, memoryTotal: 0, uptime: '',
        },
      });
    }
  },

  marketRegime: null,
  aiLearningStats: null,
  advancedRisk: null,
  refreshExtensions: async () => {
    try {
      const [regime, learning, risk] = await Promise.all([
        api.get('/extensions/regime'),
        api.get('/extensions/learning'),
        api.get('/extensions/risk')
      ]);
      set({ marketRegime: regime, aiLearningStats: learning, advancedRisk: risk });
    } catch { /* offline */ }
  },

  initialized: false,
  initialize: async () => {
    if (get().initialized) return;
    wsManager.connect();

    wsManager.on('tick', (data: any) => {
      if (data?.symbol) {
        get().updateTicker({
          symbol: data.symbol,
          price: data.price ?? data.bid ?? 0,
          change24h: data.change24h ?? 0,
          changePct24h: data.changePct24h ?? 0,
          volume: data.volume ?? 0,
          volume24h: data.volume24h ?? 0,
          high24h: data.high24h ?? data.high ?? 0,
          low24h: data.low24h ?? data.low ?? 0,
          bid: data.bid ?? data.price ?? 0,
          ask: data.ask ?? data.price ?? 0,
          timestamp: data.timestamp ?? Date.now(),
        });
      }
    });

    wsManager.on('signal_generated', (data: any) => {
      if (data) get().addSignal(mapSignal(data));
    });

    wsManager.on('signal_outcome_updated', (_data: any) => {
      get().refreshSignals();
      get().refreshOrders();
      get().refreshPositions();
    });

    wsManager.on('connection_state', (data: any) => {
      const isConn = Boolean(data?.connected);
      const current = get().systemHealth;
      get().setSystemHealth({
        api: current?.api || (isConn ? 'online' : 'offline'),
        database: current?.database || 'online',
        websocket: isConn ? 'online' : 'offline',
        marketFeed: current?.marketFeed || 'online',
        aiEngine: current?.aiEngine || 'online',
        brokerConnection: current?.brokerConnection || 'online',
        latencyMs: current?.latencyMs || 0,
        avgLatency: current?.avgLatency || 0,
        cpuUsage: current?.cpuUsage || 0,
        memoryUsage: current?.memoryUsage || 0,
        memoryTotal: current?.memoryTotal || 0,
        uptime: current?.uptime || '',
      });
    });

    wsManager.on('system_health', (data: any) => {
      if (data) {
        const components = data.components || {};
        const toStatus = (v: string) => (v === 'ok' || v === 'online' || v === 'connected' || v === 'standby') ? 'online' : (v === 'uninitialized' || v === 'degraded') ? 'degraded' : 'offline';
        get().setSystemHealth({
          api: 'online',
          database: toStatus(components.database) as 'online' | 'degraded' | 'offline',
          websocket: wsManager.isConnected ? 'online' : 'offline',
          marketFeed: toStatus(components.market_feed) as 'online' | 'degraded' | 'offline',
          aiEngine: toStatus(components.ai_engine) as 'online' | 'degraded' | 'offline',
          brokerConnection: toStatus(components.broker_api) as 'online' | 'degraded' | 'offline',
          latencyMs: 0,
          avgLatency: 0,
          cpuUsage: 0,
          memoryUsage: 0,
          memoryTotal: 0,
          uptime: '',
        });
      }
    });

    wsManager.on('order_update', (data: any) => { 
      if (data) {
        get().refreshOrders(); 
      }
    });
    wsManager.on('position_update', (data: any) => { 
      if (data) {
        get().refreshPositions(); 
      }
    });

    wsManager.on('portfolio_update', (data: any) => {
      if (data) {
        set({
          portfolio: {
            ...get().portfolio,
            totalEquity: data.equity ?? data.balance ?? get().portfolio.totalEquity,
            totalPnl: data.net_profit ?? get().portfolio.totalPnl,
            totalPnlPct: data.win_rate ?? get().portfolio.totalPnlPct,
          }
        });
      }
    });

    wsManager.on('risk_update', (data: any) => {
      if (data) {
        const r = get().riskMetrics;
        const limArr = Object.entries(data);
        const maxDrawdown = (limArr.find(([k]) => k.includes('drawdown'))?.[1] as any)?.current ?? r?.maxDrawdown ?? 0;
        const currLev = (limArr.find(([k]) => k.includes('leverage'))?.[1] as any)?.current ?? r?.leverage ?? 1;
        set({
          riskMetrics: {
            ...r,
            maxDrawdown,
            currentDrawdown: maxDrawdown,
            leverageUsed: currLev,
            leverage: currLev,
            portfolioVaR: 0,
            var1d: (limArr.find(([k]) => k.includes('var'))?.[1] as any)?.current ?? r?.var1d ?? 0,
            sharpeRatio: 0,
            maxLeverage: (limArr.find(([k]) => k.includes('leverage'))?.[1] as any)?.threshold ?? r?.maxLeverage ?? 3,
            riskScore: (data as any)?.status === 'ALERT' ? 85 : 32,
            exposureLong: 0,
            exposureShort: 0,
            exposureNet: 0,
          }
        });
      }
    });

    wsManager.on('agent_update', (data: any) => {
      if (data && data.agents) {
        set({
          aiAgents: Array.isArray(data.agents) ? data.agents.map((a: any) => ({
            id: a.id || a.role || `${Date.now()}`,
            name: a.name || a.role || 'Agent',
            role: a.role || 'Analyst',
            status: a.status || 'waiting',
            confidence: a.confidence ?? null,
            decision: a.decision || 'WAIT',
            reasoning: a.reasoning || '',
            lastUpdated: a.last_updated ?? Date.now(),
            performanceScore: a.performance_score ?? a.performanceScore ?? 0,
          })) : []
        });
      }
    });

    wsManager.on('consensus_update', (data: any) => {
      if (data) {
        set({ aiConsensus: data });
      }
    });

    wsManager.on('news_received', (data: any) => {
      if (data) {
        get().setNews([mapNewsItem(data), ...get().news].slice(0, 50));
      }
    });

    wsManager.subscribe('system');
    wsManager.subscribe('signals');
    wsManager.subscribe('orders');
    wsManager.subscribe('positions');
    wsManager.subscribe('portfolio');
    wsManager.subscribe('risk');
    wsManager.subscribe('ai');
    wsManager.subscribe('news');
    wsManager.subscribe('ticks');

    await Promise.allSettled([
      get().refreshSystemHealth(),
      get().refreshPortfolio(),
      get().refreshPositions(),
      get().refreshOrders(),
      get().refreshAgents(),
      get().refreshRisk(),
      get().refreshSignals(),
      get().refreshNews(),
      get().refreshExtensions(),
    ]);

    // Periodically poll health if WebSocket reconnecting
    setInterval(() => {
      get().refreshSystemHealth();
    }, 5000);

    set({ initialized: true });
  },
}));
