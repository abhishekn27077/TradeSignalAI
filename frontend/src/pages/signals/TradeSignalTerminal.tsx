import React, { useState, useEffect, useMemo } from 'react';
import {
  Clock,
  Zap,
  TrendingUp,
  TrendingDown,
  Shield,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Layers,
  ArrowRight,
  Filter,
  BarChart2,
  RefreshCw,
  Lock,
  X,
  Calendar,
  Check,
  Award,
  Settings as SettingsIcon,
  HelpCircle,
  Info,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const IST_TZ = 'Asia/Kolkata';

/* ========================================================================== */
/* TRADE SIGNAL TERMINAL — Clean, Minimal, Professional Signal Terminal       */
/* ========================================================================== */

export const TradeSignalTerminal: React.FC = () => {
  const activePage = useAppStore((s) => s.activePage);
  const setActivePage = useAppStore((s) => s.setActivePage);

  // Sync terminal tab with global activePage or internal state
  const activeTab = useMemo<'today' | 'history' | 'performance' | 'settings'>(() => {
    if (activePage === 'history') return 'history';
    if (activePage === 'performance') return 'performance';
    if (activePage === 'settings') return 'settings';
    return 'today';
  }, [activePage]);

  const [todayData, setTodayData] = useState<any>(null);
  const [historyData, setHistoryData] = useState<any>(null);
  const [perfData, setPerfData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [selectedSignal, setSelectedSignal] = useState<any>(null);

  // History filters
  const [dateFilter, setDateFilter] = useState<'ALL' | 'TODAY' | 'YESTERDAY' | '7D' | '30D'>('ALL');
  const [assetFilter, setAssetFilter] = useState<string>('ALL');
  const [directionFilter, setDirectionFilter] = useState<string>('ALL');
  const [timeframeFilter, setTimeframeFilter] = useState<string>('ALL');
  const [outcomeFilter, setOutcomeFilter] = useState<string>('ALL');

  // Performance horizon filter
  const [perfDateFilter, setPerfDateFilter] = useState<'ALL' | '30D' | '7D' | 'TODAY'>('ALL');

  // Realtime clock
  const [now, setNow] = useState<Date>(new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const istTimeStr = now.toLocaleTimeString('en-IN', { timeZone: IST_TZ, hour12: false });
  const istDateStr = now.toLocaleDateString('en-IN', {
    timeZone: IST_TZ,
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });

  // Load Data
  const loadData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [todayRes, historyRes, perfRes] = await Promise.all([
        fetch('/api/v1/terminal/today').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch(
          `/api/v1/terminal/history?date_filter=${dateFilter}&asset=${assetFilter}&direction=${directionFilter}&timeframe=${timeframeFilter}&outcome=${outcomeFilter}&limit=100`
        ).then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch(`/api/v1/terminal/performance?date_filter=${perfDateFilter}`)
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null),
      ]);

      if (todayRes) setTodayData(todayRes);
      if (historyRes) setHistoryData(historyRes);
      if (perfRes) setPerfData(perfRes);
    } catch (err) {
      console.error('Failed to load terminal data:', err);
    } finally {
      setLoading(false);
      if (isManual) setTimeout(() => setRefreshing(false), 500);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(false), 8000);
    return () => clearInterval(interval);
  }, [dateFilter, assetFilter, directionFilter, timeframeFilter, outcomeFilter, perfDateFilter]);

  const handleTabChange = (tab: 'today' | 'history' | 'performance' | 'settings') => {
    setActivePage(tab);
  };

  const isMarketOpen = todayData?.is_market_open ?? true;
  const marketSession = todayData?.market_session || 'Global Session';
  const todaySummary = todayData?.today_summary || {
    total_signals: 0,
    resolved_signals: 0,
    wins: 0,
    losses: 0,
    win_rate_pct: null,
    net_r: 0,
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0d14] text-slate-100 min-h-full pb-20 overflow-y-auto select-none font-sans">
      {/* ── Top Header Bar ─────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-[#0e131f]/95 backdrop-blur-md border-b border-slate-800/80 px-4 py-2.5 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Brand + IST Clock + Market Status */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
              <Zap className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
                TradeSignal <span className="text-emerald-400">Terminal</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {marketSession}
                </span>
                {isMarketOpen ? (
                  <span className="flex items-center gap-1 text-[10px] font-semibold font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    OPEN
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] font-semibold font-mono text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    MARKET CLOSED
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
                <span>{istDateStr}</span>
                <span>•</span>
                <span className="text-amber-400 font-semibold">{istTimeStr} IST</span>
              </div>
            </div>
          </div>

          {/* Tab Switcher */}
          <div className="flex items-center gap-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => handleTabChange('today')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'today'
                  ? 'bg-emerald-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              TODAY
              {todaySummary.total_signals > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                    activeTab === 'today' ? 'bg-slate-950 text-emerald-400' : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {todaySummary.total_signals}
                </span>
              )}
            </button>

            <button
              onClick={() => handleTabChange('history')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'history'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              HISTORY
            </button>

            <button
              onClick={() => handleTabChange('performance')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'performance'
                  ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              PERFORMANCE
            </button>

            <button
              onClick={() => handleTabChange('settings')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'settings'
                  ? 'bg-slate-200 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <SettingsIcon className="w-3.5 h-3.5" />
              SETTINGS
            </button>

            <button
              onClick={() => loadData(true)}
              disabled={refreshing}
              title="Refresh Data"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-1"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Terminal Body ────────────────────────────────────────── */}
      <main className="max-w-7xl w-full mx-auto px-4 py-5 space-y-6">
        {/* ================================================================= */}
        {/* TAB 1: TODAY'S OFFICIAL SIGNALS                                   */}
        {/* ================================================================= */}
        {activeTab === 'today' && (
          <div className="space-y-5">
            {/* Today's Summary Strip (Strictly Resolved Signals Counted in Win Rate) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
              <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-3">
                <div className="text-[10px] uppercase font-mono text-slate-400">Today's Signals</div>
                <div className="text-xl font-black font-mono text-white mt-0.5">
                  {todaySummary.total_signals}
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-3">
                <div className="text-[10px] uppercase font-mono text-slate-400">Resolved</div>
                <div className="text-xl font-black font-mono text-cyan-400 mt-0.5">
                  {todaySummary.resolved_signals}
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-3">
                <div className="text-[10px] uppercase font-mono text-slate-400">Wins</div>
                <div className="text-xl font-black font-mono text-emerald-400 mt-0.5">
                  {todaySummary.wins}
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-3">
                <div className="text-[10px] uppercase font-mono text-slate-400">Losses</div>
                <div className="text-xl font-black font-mono text-rose-400 mt-0.5">
                  {todaySummary.losses}
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-3">
                <div className="text-[10px] uppercase font-mono text-slate-400">Win Rate</div>
                <div className="text-xl font-black font-mono text-emerald-400 mt-0.5">
                  {todaySummary.win_rate_pct != null ? `${todaySummary.win_rate_pct}%` : '—'}
                </div>
                <div className="text-[9px] text-slate-500 font-mono">Resolved only</div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800/90 rounded-xl p-3">
                <div className="text-[10px] uppercase font-mono text-slate-400">Net Realized R</div>
                <div
                  className={`text-xl font-black font-mono mt-0.5 ${
                    todaySummary.net_r >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {todaySummary.net_r > 0 ? `+${todaySummary.net_r}R` : `${todaySummary.net_r}R`}
                </div>
              </div>
            </div>

            {/* Market Closed Banner (If market is closed) */}
            {!isMarketOpen && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wide font-mono">
                    MARKET CLOSED — LIVE GENERATION PAUSED
                  </h4>
                  <p className="text-xs text-slate-300 mt-0.5">
                    Trading sessions for Forex/Commodities are closed for the weekend/holiday. The terminal displays
                    today's qualified signals and verified session results without fabricating hypothetical predictions.
                  </p>
                </div>
              </div>
            )}

            {/* Today's Official Signal Cards */}
            {todayData?.signals && todayData.signals.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {todayData.signals.map((sig: any) => {
                  const isBuy = sig.direction === 'BUY' || sig.direction === 'LONG';
                  const isWon = sig.outcome === 'WON' || sig.status === 'TP HIT';
                  const isLost = sig.outcome === 'LOST' || sig.status === 'SL HIT';
                  const isUpcoming = sig.status === 'UPCOMING';
                  const isActive = sig.status === 'ACTIVE';

                  return (
                    <div
                      key={sig.id || sig.signal_id}
                      className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-4 space-y-3.5 shadow-md transition-all"
                    >
                      {/* Card Top: Asset, Direction, Timeframe, Status */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-black tracking-tight text-white font-mono">
                            {sig.asset}
                          </span>
                          <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200">
                            {sig.timeframe}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs font-black font-mono px-2.5 py-1 rounded-lg flex items-center gap-1 shadow-sm ${
                              isBuy
                                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            }`}
                          >
                            {isBuy ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                            {sig.direction}
                          </span>

                          <span
                            className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded border ${
                              isWon
                                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                                : isLost
                                ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                                : isActive
                                ? 'bg-blue-500/20 text-blue-400 border-blue-500/40 animate-pulse'
                                : isUpcoming
                                ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {sig.status}
                          </span>
                        </div>
                      </div>

                      {/* Exact Monospace Price Levels Grid */}
                      <div className="grid grid-cols-3 gap-2 bg-slate-950/80 p-2.5 rounded-xl border border-slate-800/80 font-mono text-xs">
                        <div>
                          <div className="text-[9px] uppercase text-slate-500">Entry</div>
                          <div className="font-bold text-slate-200 mt-0.5">
                            {typeof sig.entry === 'number'
                              ? sig.entry.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })
                              : sig.entry}
                          </div>
                        </div>
                        <div>
                          <div className="text-[9px] uppercase text-rose-400/80">Stop Loss</div>
                          <div className="font-bold text-rose-400 mt-0.5">
                            {typeof sig.stop_loss === 'number'
                              ? sig.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })
                              : sig.stop_loss}
                          </div>
                        </div>
                        <div>
                          <div className="text-[9px] uppercase text-emerald-400/80">Take Profit</div>
                          <div className="font-bold text-emerald-400 mt-0.5">
                            {typeof sig.take_profit === 'number'
                              ? sig.take_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 })
                              : sig.take_profit}
                          </div>
                        </div>
                      </div>

                      {/* Exact Timing Grid in India Standard Time (IST) */}
                      <div className="bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/60 space-y-1.5 text-xs font-mono">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Generated:</span>
                          <span className="text-slate-300 font-semibold">{sig.generated_at_ist}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Open Window:</span>
                          <span className="text-cyan-300 font-semibold">{sig.open_at_ist}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Close / Expiry:</span>
                          <span className="text-amber-300 font-semibold">{sig.close_at_ist}</span>
                        </div>
                      </div>

                      {/* Card Footer: Confidence & Realized Outcome */}
                      <div className="flex items-center justify-between pt-1 text-xs font-mono">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-400">Confidence:</span>
                          <span className="font-bold text-white bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                            {sig.confidence ?? sig.confidence_pct}%
                          </span>
                          <span className="text-slate-600">|</span>
                          <span className="text-[10px] text-slate-400">R:R</span>
                          <span className="font-bold text-slate-300">1:{sig.risk_reward ?? '2.0'}</span>
                        </div>

                        {sig.realized_r != null && (
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] text-slate-400">Result:</span>
                            <span
                              className={`font-black ${
                                sig.realized_r >= 0 ? 'text-emerald-400' : 'text-rose-400'
                              }`}
                            >
                              {sig.realized_r >= 0 ? `+${sig.realized_r}R` : `${sig.realized_r}R`}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              /* Clean "NO QUALIFIED SIGNAL" Box */
              <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
                <Clock className="w-9 h-9 text-slate-500 mx-auto" />
                <div className="text-base font-bold text-slate-200">NO QUALIFIED SIGNAL</div>
                <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                  No signals have passed the production quality gates, risk constraints, and walk-forward verification for
                  this session. TradeSignal AI does not emit low-conviction signals merely to fill the screen.
                </p>
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: HISTORICAL SIGNAL STREAM (AUDITABLE LEDGER)                */}
        {/* ================================================================= */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {/* Filter Toolbar */}
            <div className="bg-slate-900/70 p-3 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-3">
              {/* Date Filters */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
                {(['ALL', 'TODAY', 'YESTERDAY', '7D', '30D'] as const).map((df) => (
                  <button
                    key={df}
                    onClick={() => setDateFilter(df)}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      dateFilter === df
                        ? 'bg-cyan-500 text-slate-950 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {df}
                  </button>
                ))}
              </div>

              {/* Parametric Filters */}
              <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                {/* Asset */}
                <select
                  value={assetFilter}
                  onChange={(e) => setAssetFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 outline-none hover:border-slate-700 cursor-pointer"
                >
                  <option value="ALL">All Assets</option>
                  <option value="USDJPY">USDJPY</option>
                  <option value="EURUSD">EURUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                  <option value="BTCUSD">BTCUSD</option>
                  <option value="ETHUSD">ETHUSD</option>
                  <option value="XAUUSD">XAUUSD</option>
                  <option value="AUDUSD">AUDUSD</option>
                  <option value="NZDUSD">NZDUSD</option>
                  <option value="USDCAD">USDCAD</option>
                </select>

                {/* Direction */}
                <select
                  value={directionFilter}
                  onChange={(e) => setDirectionFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 outline-none hover:border-slate-700 cursor-pointer"
                >
                  <option value="ALL">All Directions</option>
                  <option value="BUY">BUY Only</option>
                  <option value="SELL">SELL Only</option>
                </select>

                {/* Timeframe */}
                <select
                  value={timeframeFilter}
                  onChange={(e) => setTimeframeFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 outline-none hover:border-slate-700 cursor-pointer"
                >
                  <option value="ALL">All Timeframes</option>
                  <option value="5m">5m</option>
                  <option value="15m">15m</option>
                  <option value="1H">1H</option>
                  <option value="4H">4H</option>
                  <option value="1D">1D</option>
                </select>

                {/* Outcome */}
                <select
                  value={outcomeFilter}
                  onChange={(e) => setOutcomeFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 outline-none hover:border-slate-700 cursor-pointer"
                >
                  <option value="ALL">All Outcomes</option>
                  <option value="WIN">WIN (TP Hit)</option>
                  <option value="LOSS">LOSS (SL Hit)</option>
                  <option value="TIME_EXIT">Expired</option>
                </select>
              </div>
            </div>

            {/* Filtered Summary Bar */}
            {historyData?.metrics && (
              <div className="flex flex-wrap items-center justify-between gap-3 px-3 py-2 bg-slate-900/40 rounded-xl border border-slate-800/60 text-xs font-mono">
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-slate-400">Total:</span>{' '}
                    <span className="font-bold text-white">{historyData.metrics.total_signals}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Resolved:</span>{' '}
                    <span className="font-bold text-cyan-400">{historyData.metrics.resolved_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Win Rate:</span>{' '}
                    <span className="font-bold text-emerald-400">
                      {historyData.metrics.win_rate_pct != null ? `${historyData.metrics.win_rate_pct}%` : '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Total Net R:</span>{' '}
                    <span
                      className={`font-black ${
                        historyData.metrics.total_net_r >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {historyData.metrics.total_net_r > 0
                        ? `+${historyData.metrics.total_net_r}R`
                        : `${historyData.metrics.total_net_r}R`}
                    </span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center gap-1">
                  <span>Click any row to inspect forensic resolution evidence</span>
                </div>
              </div>
            )}

            {/* Historical Signals Table */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <th className="text-left px-3 py-3">Date</th>
                      <th className="text-left px-3 py-3">Time (IST)</th>
                      <th className="text-left px-3 py-3">Asset</th>
                      <th className="text-center px-3 py-3">Direction</th>
                      <th className="text-center px-3 py-3">TF</th>
                      <th className="text-right px-3 py-3">Entry</th>
                      <th className="text-right px-3 py-3">SL</th>
                      <th className="text-right px-3 py-3">TP</th>
                      <th className="text-center px-3 py-3">Open (IST)</th>
                      <th className="text-center px-3 py-3">Close (IST)</th>
                      <th className="text-center px-3 py-3">Conf</th>
                      <th className="text-center px-3 py-3">Outcome</th>
                      <th className="text-right px-4 py-3">Realized R</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {historyData?.signals && historyData.signals.length > 0 ? (
                      historyData.signals.map((sig: any) => {
                        const isBuy = sig.direction === 'BUY' || sig.direction === 'LONG';
                        const isWon = sig.outcome === 'WON' || sig.status === 'TP HIT';
                        const isLost = sig.outcome === 'LOST' || sig.status === 'SL HIT';

                        // Parse Date & Time from IST
                        const datePart = sig.generated_at_ist ? sig.generated_at_ist.substring(0, 6) : '—';
                        const timePart = sig.generated_at_ist ? sig.generated_at_ist.substring(7) : '—';

                        return (
                          <tr
                            key={sig.id || sig.signal_id}
                            onClick={() => setSelectedSignal(sig)}
                            className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                          >
                            <td className="px-3 py-3 text-slate-300 font-semibold">{datePart}</td>
                            <td className="px-3 py-3 text-slate-400">{timePart}</td>
                            <td className="px-3 py-3 font-bold text-white group-hover:text-cyan-300 transition-colors">
                              {sig.asset}
                            </td>
                            <td className="px-3 py-3 text-center">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  isBuy ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                                }`}
                              >
                                {sig.direction}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-center text-slate-300">{sig.timeframe}</td>
                            <td className="px-3 py-3 text-right text-slate-200">
                              {typeof sig.entry === 'number' ? sig.entry.toFixed(2) : sig.entry}
                            </td>
                            <td className="px-3 py-3 text-right text-rose-400/90">
                              {typeof sig.stop_loss === 'number' ? sig.stop_loss.toFixed(2) : sig.stop_loss}
                            </td>
                            <td className="px-3 py-3 text-right text-emerald-400/90">
                              {typeof sig.take_profit === 'number' ? sig.take_profit.toFixed(2) : sig.take_profit}
                            </td>
                            <td className="px-3 py-3 text-center text-slate-300">{sig.open_at_ist}</td>
                            <td className="px-3 py-3 text-center text-slate-300">{sig.close_at_ist}</td>
                            <td className="px-3 py-3 text-center text-slate-300">
                              {sig.confidence ?? sig.confidence_pct}%
                            </td>
                            <td className="px-3 py-3 text-center">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  isWon
                                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                    : isLost
                                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                    : 'bg-slate-800 text-slate-400'
                                }`}
                              >
                                {isWon ? 'WIN' : isLost ? 'LOSS' : sig.status || 'PENDING'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right font-black">
                              {sig.realized_r != null ? (
                                <span className={sig.realized_r >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                  {sig.realized_r >= 0 ? `+${sig.realized_r.toFixed(2)}R` : `${sig.realized_r.toFixed(2)}R`}
                                </span>
                              ) : (
                                <span className="text-slate-500">—</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={13} className="px-4 py-8 text-center text-slate-500">
                          No historical signals matching the selected criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: PERFORMANCE (STRICTLY SAMPLE-GATED)                        */}
        {/* ================================================================= */}
        {activeTab === 'performance' && (
          <div className="space-y-6">
            {/* Horizon Selector */}
            <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
              <div className="text-xs font-mono text-slate-400">
                Evaluation Window:{' '}
                <span className="font-bold text-white uppercase">{perfDateFilter}</span>
              </div>
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
                {(['ALL', '30D', '7D', 'TODAY'] as const).map((hf) => (
                  <button
                    key={hf}
                    onClick={() => setPerfDateFilter(hf)}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      perfDateFilter === hf
                        ? 'bg-amber-500 text-slate-950 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {hf}
                  </button>
                ))}
              </div>
            </div>

            {/* Performance Overview Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Total Signals</div>
                <div className="text-2xl font-black font-mono text-white mt-1">
                  {perfData?.overview?.total_signals ?? 0}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  Resolved: {perfData?.overview?.resolved_signals ?? 0}
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Win Rate</div>
                <div className="text-2xl font-black font-mono text-emerald-400 mt-1">
                  {perfData?.overview?.win_rate_pct != null ? `${perfData.overview.win_rate_pct}%` : '—'}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  {perfData?.overview?.wins ?? 0}W / {perfData?.overview?.losses ?? 0}L
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Total Net R</div>
                <div
                  className={`text-2xl font-black font-mono mt-1 ${
                    (perfData?.overview?.total_net_r ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {(perfData?.overview?.total_net_r ?? 0) > 0
                    ? `+${perfData?.overview?.total_net_r}R`
                    : `${perfData?.overview?.total_net_r ?? 0}R`}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Realized Net Multiples</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Profit Factor</div>
                <div className="text-2xl font-black font-mono text-amber-400 mt-1">
                  {(perfData?.overview?.profit_factor ?? 1.0).toFixed(2)}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Gross Gains / Losses</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Average R (Expectancy)</div>
                <div className="text-2xl font-black font-mono text-cyan-400 mt-1">
                  {perfData?.overview?.average_r != null
                    ? `${perfData.overview.average_r > 0 ? '+' : ''}${perfData.overview.average_r}R`
                    : '—'}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Per Completed Trade</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Max Drawdown</div>
                <div className="text-2xl font-black font-mono text-rose-400 mt-1">
                  {(perfData?.overview?.max_drawdown_pct ?? 0).toFixed(1)}%
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Peak-to-Trough</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Wilson 95% CI</div>
                <div className="text-lg font-bold font-mono text-slate-300 mt-1">
                  {perfData?.overview?.wilson_95_ci
                    ? `[${perfData.overview.wilson_95_ci[0]}%, ${perfData.overview.wilson_95_ci[1]}%]`
                    : '—'}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Confidence Interval</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Sample Reliability</div>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  {perfData?.overview?.sample_status || 'ROBUST'}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  N = {perfData?.overview?.sample_size ?? 0}
                </div>
              </div>
            </div>

            {/* Performance by Asset */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold tracking-tight text-white font-mono flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Performance by Asset
                </h3>
                <span className="text-[11px] font-mono text-slate-400">
                  Minimum N = 15 required for statistical claim
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <th className="text-left px-3 py-2.5">Asset</th>
                      <th className="text-center px-3 py-2.5">Sample (N)</th>
                      <th className="text-center px-3 py-2.5">Win Rate</th>
                      <th className="text-right px-3 py-2.5">Net Realized R</th>
                      <th className="text-right px-3 py-2.5">Profit Factor</th>
                      <th className="text-right px-3 py-2.5">Expectancy R</th>
                      <th className="text-center px-3 py-2.5">Sample Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {perfData?.by_asset && perfData.by_asset.length > 0 ? (
                      perfData.by_asset.map((item: any) => (
                        <tr key={item.asset} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-3 py-2.5 font-bold text-white">{item.asset}</td>
                          <td className="px-3 py-2.5 text-center text-slate-300">N = {item.sample_size}</td>
                          <td className="px-3 py-2.5 text-center font-bold text-emerald-400">
                            {item.win_rate_pct != null ? `${item.win_rate_pct}%` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-cyan-400">
                            {item.total_net_r > 0 ? `+${item.total_net_r}R` : `${item.total_net_r}R`}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-200">
                            {item.profit_factor ? item.profit_factor.toFixed(2) : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-300">
                            {item.expectancy_r > 0 ? `+${item.expectancy_r}R` : `${item.expectancy_r}R`}
                          </td>
                          <td className="px-3 py-2.5 text-center">
                            {item.is_sufficient ? (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                ROBUST SAMPLE
                              </span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                INSUFFICIENT SAMPLE
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                          No asset performance records available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Performance by Timeframe */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold tracking-tight text-white font-mono flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-400" />
                  Performance by Timeframe
                </h3>
                <span className="text-[11px] font-mono text-slate-400">
                  Strictly avoids premature ranking without sample support
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <th className="text-left px-3 py-2.5">Timeframe</th>
                      <th className="text-center px-3 py-2.5">Sample (N)</th>
                      <th className="text-center px-3 py-2.5">Win Rate</th>
                      <th className="text-right px-3 py-2.5">Net Realized R</th>
                      <th className="text-right px-3 py-2.5">Profit Factor</th>
                      <th className="text-right px-3 py-2.5">Expectancy R</th>
                      <th className="text-center px-3 py-2.5">Sample Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {perfData?.by_timeframe && perfData.by_timeframe.length > 0 ? (
                      perfData.by_timeframe.map((item: any) => (
                        <tr key={item.timeframe} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-3 py-2.5 font-bold text-white">{item.timeframe}</td>
                          <td className="px-3 py-2.5 text-center text-slate-300">N = {item.sample_size}</td>
                          <td className="px-3 py-2.5 text-center font-bold text-emerald-400">
                            {item.win_rate_pct != null ? `${item.win_rate_pct}%` : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-right font-bold text-cyan-400">
                            {item.total_net_r > 0 ? `+${item.total_net_r}R` : `${item.total_net_r}R`}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-200">
                            {item.profit_factor ? item.profit_factor.toFixed(2) : '—'}
                          </td>
                          <td className="px-3 py-2.5 text-right text-slate-300">
                            {item.expectancy_r > 0 ? `+${item.expectancy_r}R` : `${item.expectancy_r}R`}
                          </td>
                          <td className="px-3 py-2.5 text-center">
                            {item.is_sufficient ? (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                ROBUST SAMPLE
                              </span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                INSUFFICIENT SAMPLE
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                          No timeframe performance records available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 4: SETTINGS & TERMINAL CONFIGURATION                          */}
        {/* ================================================================= */}
        {activeTab === 'settings' && (
          <div className="max-w-3xl mx-auto space-y-5">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <SettingsIcon className="w-4 h-4 text-cyan-400" />
                Terminal Display & Timezone Configuration
              </h3>

              <div className="space-y-3 text-xs font-mono">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div>
                    <div className="font-bold text-slate-200">Display Timezone</div>
                    <div className="text-[11px] text-slate-400">
                      Standardized for presentation across all signal cards and history.
                    </div>
                  </div>
                  <span className="font-bold text-emerald-400 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20">
                    Asia/Kolkata (IST)
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div>
                    <div className="font-bold text-slate-200">Execution Safety State</div>
                    <div className="text-[11px] text-slate-400">
                      Real money execution safety lockout enforced at system boot.
                    </div>
                  </div>
                  <span className="font-bold text-cyan-400 px-2.5 py-1 rounded bg-cyan-500/10 border border-cyan-500/20 flex items-center gap-1">
                    <Lock className="w-3 h-3 text-cyan-400" /> DEMO / PAPER ONLY
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div>
                    <div className="font-bold text-slate-200">Signal Deduplication</div>
                    <div className="text-[11px] text-slate-400">
                      SignalIdentityGuard ensures zero duplicate setups are emitted.
                    </div>
                  </div>
                  <span className="font-bold text-emerald-400 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-1">
                    <Check className="w-3 h-3" /> ACTIVE (SSOT)
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div>
                    <div className="font-bold text-slate-200">Outcome Resolution Engine</div>
                    <div className="text-[11px] text-slate-400">
                      Evaluates expired signals against verified historical candle data.
                    </div>
                  </div>
                  <span className="font-bold text-slate-300 px-2.5 py-1 rounded bg-slate-900 border border-slate-700">
                    Conservative Intra-Candle (SL First)
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div>
                    <div className="font-bold text-slate-200">Alert Architecture</div>
                    <div className="text-[11px] text-slate-400">
                      Webhook and notification hooks for upcoming, active, and resolved events.
                    </div>
                  </div>
                  <span className="font-bold text-slate-400 px-2.5 py-1 rounded bg-slate-900 border border-slate-700">
                    Ready for Telegram / Email
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── Forensic Signal Detail Modal ───────────────────────────────── */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f141f] border border-slate-800 rounded-2xl max-w-lg w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-base font-extrabold text-white">{selectedSignal.asset}</span>
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                    selectedSignal.direction === 'BUY'
                      ? 'bg-emerald-500/15 text-emerald-400'
                      : 'bg-rose-500/15 text-rose-400'
                  }`}
                >
                  {selectedSignal.direction}
                </span>
                <span className="text-slate-400 text-[11px] bg-slate-800 px-1.5 py-0.5 rounded">
                  {selectedSignal.timeframe}
                </span>
              </div>
              <button
                onClick={() => setSelectedSignal(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5">
              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 space-y-1">
                <div className="text-[10px] text-slate-500 uppercase">Signal ID</div>
                <div className="text-[11px] text-cyan-400 break-all">{selectedSignal.id || selectedSignal.signal_id}</div>
              </div>

              <div className="grid grid-cols-3 gap-2 bg-slate-950 p-2.5 rounded-xl border border-slate-800/80">
                <div>
                  <div className="text-[9px] uppercase text-slate-500">Entry</div>
                  <div className="font-bold text-white mt-0.5">{selectedSignal.entry}</div>
                </div>
                <div>
                  <div className="text-[9px] uppercase text-rose-400/80">Stop Loss</div>
                  <div className="font-bold text-rose-400 mt-0.5">{selectedSignal.stop_loss}</div>
                </div>
                <div>
                  <div className="text-[9px] uppercase text-emerald-400/80">Take Profit</div>
                  <div className="font-bold text-emerald-400 mt-0.5">{selectedSignal.take_profit}</div>
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Generated (IST):</span>
                  <span className="text-slate-200 font-semibold">{selectedSignal.generated_at_ist}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Open Window (IST):</span>
                  <span className="text-cyan-300 font-semibold">{selectedSignal.open_at_ist}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Close / Expiry (IST):</span>
                  <span className="text-amber-300 font-semibold">{selectedSignal.close_at_ist}</span>
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Outcome:</span>
                  <span
                    className={`font-bold ${
                      selectedSignal.outcome === 'WON'
                        ? 'text-emerald-400'
                        : selectedSignal.outcome === 'LOST'
                        ? 'text-rose-400'
                        : 'text-slate-400'
                    }`}
                  >
                    {selectedSignal.outcome || selectedSignal.status || 'UNRESOLVED'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Actual Exit Price:</span>
                  <span className="text-slate-200 font-semibold">{selectedSignal.exit_price ?? '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Realized R:</span>
                  <span
                    className={`font-black ${
                      (selectedSignal.realized_r ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {selectedSignal.realized_r != null
                      ? `${selectedSignal.realized_r >= 0 ? '+' : ''}${selectedSignal.realized_r}R`
                      : '—'}
                  </span>
                </div>
                {selectedSignal.resolution_reason && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Resolution Reason:</span>
                    <span className="text-amber-300 font-semibold">{selectedSignal.resolution_reason}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedSignal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default TradeSignalTerminal;
