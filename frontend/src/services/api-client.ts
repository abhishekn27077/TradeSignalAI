const API_BASE = '/api/v1';

interface ApiResponse<T = unknown> {
  success?: boolean;
  message?: string;
  data?: T;
  [key: string]: unknown;
}

class ApiError extends Error {
  status: number;
  body?: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: { ...headers, ...options.headers },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new ApiError(res.status, `API ${res.status}: ${res.statusText}`, body);
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, (err as Error).message || 'Network error');
  } finally {
    clearTimeout(timeout);
  }
}

function extractData<T>(raw: unknown, key?: string): T {
  const resp = raw as ApiResponse<T>;
  if (resp && typeof resp === 'object' && resp.success === false) {
    throw new ApiError(200, resp.message || 'API Error', resp);
  }
  if (key && resp && typeof resp === 'object' && key in resp) {
    return (resp as Record<string, unknown>)[key] as T;
  }
  if (resp && typeof resp === 'object' && resp.data !== undefined) return resp.data as T;
  return raw as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  auth: {
    login: (formData: URLSearchParams) =>
      request<{ access_token: string; token_type: string }>('/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString()
      }),
    logout: () => {
      localStorage.removeItem('token');
    }
  },

  health: {
    status: () => request<ApiResponse>('/system/status'),
    ping: () => request<{ message: string }>('/system/ping'),
  },

  market: {
    price: (symbol: string) =>
      request<ApiResponse>(`/market/price/${encodeURIComponent(symbol)}`).then(r => extractData<any>(r, 'data')),
    rates: (symbol: string, timeframe = '1h', count = 100) =>
      request<ApiResponse>(`/market/rates/${encodeURIComponent(symbol)}/${timeframe}?count=${count}`),
    ticker: (symbol: string) =>
      request<ApiResponse>(`/market/ticker/${encodeURIComponent(symbol)}`).then(r => extractData<any>(r, 'data')),
  },

  agents: {
    initialize: () =>
      request<ApiResponse>('/agents/initialize', { method: 'POST' }).then(r => extractData<any>(r, 'agents')),
    status: () => request<ApiResponse>('/agents/status').then(r => extractData<any>(r, 'agents')),
    health: () => request<ApiResponse>('/agents/health'),
    consensus: () => request<ApiResponse>('/agents/consensus').then(r => extractData<any>(r, 'consensus')),
    triggerConsensus: (symbol: string) =>
      request<ApiResponse>('/agents/consensus/trigger', { method: 'POST', body: JSON.stringify({ symbol }) }),
  },

  strategies: {
    list: () => request<ApiResponse>('/strategies').then(r => extractData<any[]>(r, 'strategies')),
    active: () => request<ApiResponse>('/strategies/active').then(r => extractData<any[]>(r, 'strategies')),
    get: (name: string) => request<ApiResponse>(`/strategies/${encodeURIComponent(name)}`).then(r => extractData<any>(r, 'strategy')),
    enable: (name: string) => request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/enable`, { method: 'POST' }),
    disable: (name: string) => request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/disable`, { method: 'POST' }),
    pause: (name: string) => request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/pause`, { method: 'POST' }),
    resume: (name: string) => request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/resume`, { method: 'POST' }),
    config: (name: string, cfg: any) =>
      request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/config`, { method: 'PUT', body: JSON.stringify(cfg) }),
    priority: (name: string, priority: number) =>
      request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/priority?priority=${priority}`, { method: 'POST' }),
    analytics: (name: string) =>
      request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/analytics`).then(r => extractData<any>(r, 'analytics')),
    optimize: (name: string) =>
      request<ApiResponse>(`/strategies/${encodeURIComponent(name)}/optimize`).then(r => extractData<any>(r, 'recommendations')),
    optimizeAll: () =>
      request<ApiResponse>('/strategies/optimize/all').then(r => extractData<any[]>(r, 'recommendations')),
    health: () => request<ApiResponse>('/strategies/health'),
  },

  signals: {
    history: (limit = 100) =>
      request<ApiResponse>(`/signals/history?limit=${limit}`).then(r => extractData<any[]>(r, 'signals')),
    historyWithFilter: (params: {
      time_range?: string;
      start_date?: string;
      end_date?: string;
      asset?: string;
      ablation_mode?: string;
      limit?: number;
    }) => {
      const qs = new URLSearchParams();
      if (params.time_range) qs.set('time_range', params.time_range);
      if (params.start_date) qs.set('start_date', params.start_date);
      if (params.end_date) qs.set('end_date', params.end_date);
      if (params.asset) qs.set('asset', params.asset);
      if (params.ablation_mode) qs.set('ablation_mode', params.ablation_mode);
      if (params.limit) qs.set('limit', String(params.limit));
      return request<ApiResponse>(`/signals/history?${qs.toString()}`).then(r => extractData<any[]>(r, 'signals'));
    },
    getById: (signalId: string) =>
      request<ApiResponse>(`/signals/${encodeURIComponent(signalId)}`).then(r => extractData<any>(r, 'signal')),
    live: () =>
      request<ApiResponse>('/signals/live').then(r => {
        if (Array.isArray(r)) return r;
        if (r && typeof r === 'object') {
          const obj = r as Record<string, any>;
          if (Array.isArray(obj.live_signals)) return obj.live_signals;
          if (Array.isArray(obj.live_qualified_signals)) return obj.live_qualified_signals;
          if (Array.isArray(obj.signals)) return obj.signals;
          if (Array.isArray(obj.data)) return obj.data;
        }
        return [];
      }),
    today: () =>
      request<ApiResponse>('/signals/today').then(r => extractData<any[]>(r, 'signals')),
    upcoming: () =>
      request<ApiResponse>('/signals/upcoming').then(r => extractData<any[]>(r, 'signals')),
    yesterday: () =>
      request<ApiResponse>('/signals/yesterday').then(r => extractData<any[]>(r, 'signals')),
    active: () =>
      request<ApiResponse>('/signals/active').then(r => extractData<any[]>(r, 'signals')),
    predict: (symbol: string, timeframe = '4H') =>
      request<ApiResponse>(`/signals/predict/${encodeURIComponent(symbol)}?timeframe=${timeframe}`).then(r => extractData<any>(r, 'prediction')),
    quality: () =>
      request<ApiResponse>('/signals/quality').then(r => extractData<any[]>(r, 'quality_scores')),
    validate: () =>
      request<ApiResponse>('/signals/validate').then(r => extractData<any[]>(r, 'validations')),
    scan: () =>
      request<ApiResponse>('/signals/scan', { method: 'POST' }),
    h4Intelligence: () =>
      request<any>('/signals/h4-intelligence'),
    holding: (strategyName: string, params: any) => {
      const qs = new URLSearchParams(params).toString();
      return request<ApiResponse>(`/signals/holding/${encodeURIComponent(strategyName)}?${qs}`).then(r => extractData<any>(r, 'decision'));
    },
  },

  forecasts: {
    history: (limit = 50) => request<ApiResponse>(`/forecast/predictions/current?limit=${limit}`).then(r => extractData<any[]>(r, 'data')),
  },

  execution: {
    orders: () => request<any>('/execution/orders').then(r => extractData<any[]>(r, 'orders')),
    positions: () => request<any>('/execution/positions').then(r => extractData<any[]>(r, 'positions')),
    balance: () => request<any>('/execution/balance'),
    cancelOrder: (id: string) => request<ApiResponse>(`/execution/cancel/${id}`, { method: 'POST' }),
  },

  journal: {
    trades: (limit = 100, offset = 0) =>
      request<any>(`/journal/trades?limit=${limit}&offset=${offset}`).then(r => extractData<any[]>(r, 'trades')),
    trade: (id: string) =>
      request<any>(`/journal/trades/${id}`).then(r => extractData<any>(r, 'trade')),
    statistics: () => request<any>('/journal/statistics'),
    reviewTrade: (id: string) => request<ApiResponse>(`/journal/trades/${id}/review`, { method: 'POST' }),
  },

  portfolio: {
    summary: () => request<any>('/portfolio/summary'),
    allocation: () => request<any>('/portfolio/allocation'),
  },

  risk: {
    limits: () => request<any>('/risk/limits').then(r => extractData<any>(r, 'data')),
    exposure: () => request<any>('/risk/exposure').then(r => extractData<any>(r, 'data')),
    stressTest: (scenario: string, portfolioValue = 100000) =>
      request<any>('/risk/stress-test', { method: 'POST', body: JSON.stringify({ scenario, portfolio_value: portfolioValue }) }),
    scenarios: () => request<any>('/risk/scenarios').then(r => extractData<any>(r, 'data')),
  },

  news: {
    latest: (limit = 20) =>
      request<ApiResponse>(`/news/latest?limit=${limit}`).then(r => extractData<any[]>(r, 'news')),
    bySymbol: (symbol: string, limit = 10) =>
      request<ApiResponse>(`/news/symbol/${encodeURIComponent(symbol)}?limit=${limit}`).then(r => extractData<any[]>(r, 'news')),
    sentiment: (symbol: string) =>
      request<ApiResponse>(`/news/sentiment/${encodeURIComponent(symbol)}`).then(r => extractData<any>(r, 'sentiment')),
  },

  memory: {
    search: (query: string, limit = 20) =>
      request<any>('/memory/search', { method: 'POST', body: JSON.stringify({ query, limit }) }),
    statistics: () => request<ApiResponse>('/memory/statistics').then(r => extractData<any>(r, 'data')),
    graph: () => request<ApiResponse>('/memory/graph').then(r => extractData<any>(r, 'data')),
    graphNode: (nodeId: string) => request<ApiResponse>(`/memory/graph/node/${nodeId}`),
  },

  analytics: {
    dashboard: () => request<ApiResponse>('/analytics/dashboard').then(r => extractData<any>(r)),
    performance: () => request<any>('/analytics/performance'),
    patterns: (symbol = 'EURUSD') => request<any>(`/analytics/patterns?symbol=${encodeURIComponent(symbol)}`),
    recommendations: () => request<any>('/analytics/recommendations'),
  },

  brokers: {
    status: () => request<ApiResponse>('/brokers/status'),
    sync: () => request<ApiResponse>('/brokers/sync', { method: 'POST' }),
  },

  backtest: {
    run: (symbol = 'EURUSD', timeframe = '1h', strategy = '', capital = 10000) =>
      request<ApiResponse>('/backtest/run', { method: 'POST', body: JSON.stringify({ symbol, timeframe, strategy, capital }) }),
    history: (limit = 20) => request<ApiResponse>(`/backtest/history?limit=${limit}`).then(r => extractData<any[]>(r, 'history')),
  },

  paper: {
    status: () => request<ApiResponse>('/paper/status').then(r => extractData<any>(r, 'data')),
    orders: () => request<ApiResponse>('/paper/orders'),
    statistics: () => request<ApiResponse>('/paper/statistics').then(r => extractData<any>(r, 'data')),
  },

  forecast: {
    providers: () => request<ApiResponse>('/forecast/providers').then(r => extractData<string[]>(r, 'providers')),
    forecasts: (symbol?: string, provider?: string) => {
      const qs = new URLSearchParams();
      if (symbol) qs.set('symbol', symbol);
      if (provider) qs.set('provider', provider);
      return request<ApiResponse>(`/forecast/forecasts?${qs}`).then(r => extractData<any[]>(r, 'forecasts'));
    },
  },

  qualification: {
    start: (mode: string, config?: any) => request<ApiResponse>('/qualification/start', { method: 'POST', body: JSON.stringify({ mode, config }) }),
    stop: () => request<ApiResponse>('/qualification/stop', { method: 'POST' }),
    status: () => request<any>('/qualification/status'),
    report: () => request<ApiResponse>('/qualification/report').then(r => extractData<any>(r, 'report')),
  },
};
