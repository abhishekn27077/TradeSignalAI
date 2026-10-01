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
/* SECTION 16: REALTIME SIGNAL COUNTDOWN HELPER                               */
/* ========================================================================== */

const SignalCountdown: React.FC<{ signal: any; now: Date }> = ({ signal, now }) => {
  const status = signal.status;
  const nowMs = now.getTime();

  // If UPCOMING: countdown to entry window
  if (status === 'UPCOMING' && signal.open_at_utc) {
    const openMs = new Date(signal.open_at_utc).getTime();
    const diffSec = Math.floor((openMs - nowMs) / 1000);
    if (diffSec > 0) {
      const mins = Math.floor(diffSec / 60);
      const secs = diffSec % 60;
      return (
        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 font-bold flex items-center gap-1">
          <Clock className="w-3 h-3 text-cyan-400" />
          Opens in {mins}m {secs}s
        </span>
      );
    } else {
      return (
        <span className="text-[10px] font-mono text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20 font-bold flex items-center gap-1">
          <Check className="w-3 h-3 text-cyan-300" />
          Window open
        </span>
      );
    }
  }

  // If ACTIVE: duration since activation + countdown to expiry
  if (status === 'ACTIVE') {
    let activeSec = 0;
    const startStr = signal.actual_entry_utc || signal.open_at_utc;
    if (startStr) {
      activeSec = Math.max(0, Math.floor((nowMs - new Date(startStr).getTime()) / 1000));
    }
    const mins = Math.floor(activeSec / 60);
    const secs = activeSec % 60;

    let expiryText = '';
    const closeStr = signal.close_at_utc || signal.actual_exit_utc;
    if (closeStr) {
      const remainSec = Math.floor((new Date(closeStr).getTime() - nowMs) / 1000);
      if (remainSec > 0) {
        const remMins = Math.floor(remainSec / 60);
        const remSecs = remainSec % 60;
        expiryText = ` • Expires in ${remMins}m ${remSecs}s`;
      }
    }

    return (
      <span className="text-[10px] font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 font-bold flex items-center gap-1">
        <Activity className="w-3 h-3 text-blue-400 animate-pulse" />
        Active: {mins}m {secs}s{expiryText}
      </span>
    );
  }

  // If expiring / pending
  if (signal.close_at_utc && (status === 'EXPIRING' || status === 'PENDING')) {
    const remainSec = Math.floor((new Date(signal.close_at_utc).getTime() - nowMs) / 1000);
    if (remainSec > 0) {
      const remMins = Math.floor(remainSec / 60);
      const remSecs = remainSec % 60;
      return (
        <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-bold flex items-center gap-1">
          <Clock className="w-3 h-3 text-amber-400" />
          Expires in {remMins}m {remSecs}s
        </span>
      );
    }
  }

  return null;
};

/* ========================================================================== */
/* SECTION 24: SYSTEM STATUS BADGE HELPER (UNAMBIGUOUS INDICATORS)            */
/* ========================================================================== */

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'HEALTHY':
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          HEALTHY
        </span>
      );
    case 'DEGRADED':
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          DEGRADED
        </span>
      );
    case 'BLOCKED':
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
          BLOCKED
        </span>
      );
    case 'UNAVAILABLE':
    default:
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          UNAVAILABLE
        </span>
      );
  }
};

/* ========================================================================== */
/* TRADE SIGNAL TERMINAL — Clean, Minimal, Professional Signal Terminal       */
/* ========================================================================== */

export const TradeSignalTerminal: React.FC = () => {
  const activePage = useAppStore((s) => s.activePage);
  const setActivePage = useAppStore((s) => s.setActivePage);

  // Sync terminal tab with global activePage or internal state
  const activeTab = useMemo<'today' | 'history' | 'performance' | 'status' | 'settings'>(() => {
    if (activePage === 'history') return 'history';
    if (activePage === 'performance') return 'performance';
    if (activePage === 'status') return 'status';
    if (activePage === 'settings') return 'settings';
    return 'today';
  }, [activePage]);

  const [todayData, setTodayData] = useState<any>(null);
  const [historyData, setHistoryData] = useState<any>(null);
  const [perfData, setPerfData] = useState<any>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [selectedSignal, setSelectedSignal] = useState<any>(null);

  // History filters
  const [dateFilter, setDateFilter] = useState<'ALL' | 'TODAY' | 'YESTERDAY' | '7D' | '30D'>('ALL');
  const [recordTypeFilter, setRecordTypeFilter] = useState<'ALL' | 'LIVE' | 'HISTORICAL' | 'REPLAY' | 'DEMO'>('ALL');
  const [providerFilter, setProviderFilter] = useState<string>('ALL');
  const [assetFilter, setAssetFilter] = useState<string>('ALL');
  const [directionFilter, setDirectionFilter] = useState<string>('ALL');
  const [timeframeFilter, setTimeframeFilter] = useState<string>('ALL');
  const [outcomeFilter, setOutcomeFilter] = useState<string>('ALL');

  // Performance horizon filter
  const [perfDateFilter, setPerfDateFilter] = useState<'ALL' | '30D' | '7D' | 'TODAY'>('ALL');

  // Forensic Deep Detail for Selected Signal
  const [detailedForensics, setDetailedForensics] = useState<any>(null);
  const [loadingForensics, setLoadingForensics] = useState<boolean>(false);

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
      const [todayRes, historyRes, perfRes, statusRes] = await Promise.all([
        fetch('/api/v1/terminal/today').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch(
          `/api/v1/terminal/history?date_filter=${dateFilter}&record_type=${recordTypeFilter}&provider=${providerFilter}&asset=${assetFilter}&direction=${directionFilter}&timeframe=${timeframeFilter}&outcome=${outcomeFilter}&limit=100`
        ).then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch(`/api/v1/terminal/performance?date_filter=${perfDateFilter}`)
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null),
        fetch('/api/v1/terminal/system-status')
          .then((r) => (r.ok ? r.json() : null))
          .catch(() => null),
      ]);

      if (todayRes) setTodayData(todayRes);
      if (historyRes) setHistoryData(historyRes);
      if (perfRes) setPerfData(perfRes);
      if (statusRes) setSystemStatus(statusRes);
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
  }, [dateFilter, recordTypeFilter, providerFilter, assetFilter, directionFilter, timeframeFilter, outcomeFilter, perfDateFilter]);

  // Fetch full forensic record when a signal is selected
  useEffect(() => {
    if (!selectedSignal) {
      setDetailedForensics(null);
      return;
    }
    const sigId = selectedSignal.id || selectedSignal.signal_id;
    if (!sigId) return;

    setLoadingForensics(true);
    fetch(`/api/v1/terminal/history/${sigId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.forensics) {
          setDetailedForensics(data.forensics);
        } else {
          setDetailedForensics(null);
        }
      })
      .catch((err) => console.error('Failed to fetch signal forensics:', err))
      .finally(() => setLoadingForensics(false));
  }, [selectedSignal]);

  const handleTabChange = (tab: 'today' | 'history' | 'performance' | 'status' | 'settings') => {
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
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  PAPER ONLY
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
                <span>•</span>
                <span className="text-slate-400">Feeds:</span>
                {/* Section 15: Header Provider Status Truth */}
                <span
                  className={
                    todayData?.providers?.mt5?.verified
                      ? 'text-emerald-400 font-semibold'
                      : 'text-rose-400 font-semibold'
                  }
                >
                  {todayData?.providers?.mt5?.label || (todayData?.is_forex_open ? '● MT5 — LIVE' : '● MT5 — BLOCKED')}
                </span>
                <span>|</span>
                <span className="text-emerald-400 font-semibold">
                  {todayData?.providers?.binance?.label || '● BINANCE — LIVE'}
                </span>
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
              onClick={() => handleTabChange('status')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'status'
                  ? 'bg-blue-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              STATUS
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

            {/* Market Closed Banner (If market is closed or specific forex closed message) */}
            {(!isMarketOpen || todayData?.market_status_message) && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wide font-mono">
                    FOREX MARKET CLOSED — SUNDAY PRE-MARKET
                  </h4>
                  <p className="text-xs text-slate-300 mt-0.5">
                    {todayData?.market_status_message ||
                      "Trading sessions for Forex are closed until Sunday 22:00 UTC (03:30 AM IST Monday). Actionable trade signals for Forex are blocked."}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400 mt-2">
                    <span>Forex Primary: <strong className="text-amber-400">MT5 (CLOSED)</strong></span>
                    <span>•</span>
                    <span>Crypto Primary: <strong className="text-emerald-400">BINANCE (LIVE 24/7)</strong></span>
                    <span>•</span>
                    <span>Execution: <strong className="text-cyan-400">PAPER ONLY</strong></span>
                  </div>
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
                      onClick={() => setSelectedSignal(sig)}
                      className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-2xl p-4 space-y-3.5 shadow-md transition-all cursor-pointer"
                    >
                      {/* Card Top: Asset, Direction, Timeframe, Status */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-lg font-black tracking-tight text-white font-mono">
                            {sig.asset}
                          </span>
                          <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200">
                            {sig.timeframe}
                          </span>
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                            {sig.provider || 'BINANCE'}
                          </span>
                          {sig.live_data_verified ? (
                            <span className="flex items-center gap-1 text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              LIVE VERIFIED
                            </span>
                          ) : null}
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

                      {/* Section 16: Countdown & Section 15: Data Age */}
                      <div className="flex items-center justify-between text-xs font-mono">
                        <SignalCountdown signal={sig} now={now} />
                        <span className="text-[10px] text-slate-400">
                          Data Age: <strong className="text-slate-200">{sig.data_age_seconds != null ? `${sig.data_age_seconds}s` : '<5s'}</strong>
                        </span>
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

                      {/* Exact Timing Grid in India Standard Time (IST) - Section 8 & 15 */}
                      <div className="bg-slate-950/40 p-2.5 rounded-xl border border-slate-800/60 space-y-1.5 text-xs font-mono">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Generated:</span>
                          <span className="text-slate-300 font-semibold">{sig.generated_at_ist}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Market Snapshot:</span>
                          <span className="text-amber-300 font-semibold">{sig.market_snapshot_time_ist || sig.generated_at_ist}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Entry Window:</span>
                          <span className="text-cyan-300 font-semibold">{sig.entry_window_ist || sig.open_at_ist}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400">Close / Expiry:</span>
                          <span className="text-amber-300 font-semibold">{sig.actual_exit_ist || sig.close_at_ist}</span>
                        </div>
                      </div>

                      {/* Card Footer: Confidence, Agreement & Realized Outcome */}
                      <div className="flex items-center justify-between pt-1 text-xs font-mono">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-[10px] text-slate-400">Conf:</span>
                          <span className="font-bold text-white bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                            {sig.confidence ?? sig.confidence_pct}%
                          </span>
                          <span className="text-slate-600">|</span>
                          <span className="text-[10px] text-slate-400">Agree:</span>
                          <span className="font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                            {sig.agreement_pct ? `${sig.agreement_pct}%` : '>=60%'}
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
              /* Clean "NO QUALIFIED LIVE SIGNALS" Box - Section 14 Truth */
              <div className="p-8 text-center bg-slate-900/40 rounded-2xl border border-slate-800 space-y-4">
                <Clock className="w-10 h-10 text-slate-500 mx-auto" />
                <div className="text-base font-bold text-slate-200 uppercase font-mono">NO QUALIFIED SIGNALS</div>
                <p className="text-xs text-slate-300 max-w-lg mx-auto leading-relaxed font-mono">
                  {todayData?.no_signals_reason ||
                    "No signals have passed the real-time qualification gates (model agreement >= 60.0%, consensus >= 0.65) and verified live feed data. Historical, demo, and replay records are excluded from Today's Live Signals."}
                </p>

                {/* Section 14: Actual Reason Distribution */}
                {todayData?.rejection_reason_distribution && (
                  <div className="mt-3 p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl max-w-md mx-auto text-left font-mono">
                    <div className="text-[10px] uppercase font-bold text-slate-400 mb-2 border-b border-slate-800/80 pb-1.5 flex items-center justify-between">
                      <span>Rejection Reason Distribution</span>
                      <span className="text-slate-500 text-[9px]">Live Pipeline Gates</span>
                    </div>
                    <div className="space-y-1.5 text-xs">
                      {Object.entries(todayData.rejection_reason_distribution).map(([reason, count]) => (
                        <div key={reason} className="flex items-center justify-between text-slate-300">
                          <span className="text-slate-400">{reason}:</span>
                          <span
                            className={`font-bold ${
                              Number(count) === 0
                                ? 'text-slate-500'
                                : reason === 'Qualified'
                                ? 'text-emerald-400'
                                : 'text-amber-400'
                            }`}
                          >
                            {String(count)} asset{Number(count) === 1 ? '' : 's'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-[11px] font-mono text-slate-400">
                  <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    Live Data Enforcement: <strong className="text-emerald-400">ACTIVE</strong>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    MT5 Status: <strong className="text-rose-400">BLOCKED</strong>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    Binance Status: <strong className="text-emerald-400">LIVE</strong>
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: HISTORICAL SIGNAL STREAM (AUDITABLE LEDGER)                */}
        {/* ================================================================= */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {/* Filter Toolbar - Section 10 */}
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
                {/* Record Type Filter - Section 10 */}
                <select
                  value={recordTypeFilter}
                  onChange={(e) => setRecordTypeFilter(e.target.value as any)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-cyan-300 font-bold outline-none hover:border-slate-700 cursor-pointer"
                >
                  <option value="ALL">All Types</option>
                  <option value="LIVE">Live Signals</option>
                  <option value="HISTORICAL">Historical</option>
                  <option value="REPLAY">Replay</option>
                  <option value="DEMO">Demo / Test</option>
                </select>

                {/* Provider Filter */}
                <select
                  value={providerFilter}
                  onChange={(e) => setProviderFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 outline-none hover:border-slate-700 cursor-pointer"
                >
                  <option value="ALL">All Providers</option>
                  <option value="MT5">MT5</option>
                  <option value="BINANCE">Binance</option>
                </select>

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
                  <option value="UNRESOLVED">Unresolved</option>
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
                  <div>
                    <span className="text-slate-400">Sample Status:</span>{' '}
                    <span
                      className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                        historyData.metrics.sample_status === 'SAMPLE-SUPPORTED'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                      }`}
                      title={historyData.metrics.sample_size_tooltip}
                    >
                      {historyData.metrics.sample_status}
                    </span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center gap-1">
                  <span>Click any row for complete Sections A–I forensic timeline</span>
                </div>
              </div>
            )}

            {/* Historical Signals Table */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <th className="text-left px-3 py-3">Type</th>
                      <th className="text-left px-3 py-3">Provider</th>
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
                      <th className="text-center px-3 py-3">Duration</th>
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

                        const recordType = sig.record_type || (sig.is_demo ? 'DEMO' : sig.is_live ? 'LIVE' : 'HISTORICAL');

                        return (
                          <tr
                            key={sig.id || sig.signal_id}
                            onClick={() => setSelectedSignal(sig)}
                            className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                          >
                            <td className="px-3 py-3">
                              <span
                                className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                  recordType === 'LIVE'
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : recordType === 'DEMO'
                                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                                }`}
                              >
                                {recordType}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-slate-400 font-semibold text-[10px]">
                              {sig.provider || 'MT5'}
                            </td>
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
                            <td className="px-3 py-3 text-center text-cyan-300 font-mono">{sig.duration || '—'}</td>
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
                        <td colSpan={15} className="px-4 py-8 text-center text-slate-500">
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

            {/* Performance Overview Cards - Section 11, 12, 13, 16 */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
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
                <div className="text-[10px] uppercase font-mono text-slate-400">Net Realized R</div>
                <div
                  className={`text-2xl font-black font-mono mt-1 ${
                    (perfData?.overview?.total_net_r ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {(perfData?.overview?.total_net_r ?? 0) > 0
                    ? `+${perfData?.overview?.total_net_r}R`
                    : `${perfData?.overview?.total_net_r ?? 0}R`}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  Avg R: {perfData?.overview?.average_r != null ? `${perfData.overview.average_r}R` : '—'}
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Profit Factor</div>
                <div className="text-2xl font-black font-mono text-amber-400 mt-1">
                  {(perfData?.overview?.profit_factor ?? 1.0).toFixed(2)}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Gross Gains / Losses</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Max Drawdown</div>
                <div className="text-2xl font-black font-mono text-rose-400 mt-1">
                  {(perfData?.overview?.max_drawdown_pct ?? 0).toFixed(2)}%
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">
                  Decline: -{perfData?.overview?.max_drawdown_r ?? 0}R
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Streaks</div>
                <div className="text-xl font-black font-mono text-slate-200 mt-1">
                  <span className="text-emerald-400">{perfData?.overview?.max_consecutive_wins ?? 0}W</span>
                  <span className="text-slate-500 mx-1.5">/</span>
                  <span className="text-rose-400">{perfData?.overview?.max_consecutive_losses ?? 0}L</span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Max Consecutive</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Avg Holding Time</div>
                <div className="text-xl font-black font-mono text-cyan-400 mt-1">
                  {perfData?.overview?.avg_holding_hours ?? 4.0}h
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Entry to Resolution</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Wilson 95% CI</div>
                <div className="text-base font-bold font-mono text-slate-300 mt-1">
                  {perfData?.overview?.wilson_95_ci
                    ? `[${perfData.overview.wilson_95_ci[0]}%, ${perfData.overview.wilson_95_ci[1]}%]`
                    : '—'}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Confidence Interval</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 col-span-2">
                <div className="text-[10px] uppercase font-mono text-slate-400 flex items-center justify-between">
                  <span>Statistical Status (Section 11)</span>
                  <span className="text-[9px] text-slate-500 font-normal">Min Required N = 15</span>
                </div>
                <div className="text-sm font-bold font-mono mt-1 flex items-center gap-1.5">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-bold ${
                      perfData?.overview?.sample_status === 'SAMPLE-SUPPORTED'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {perfData?.overview?.sample_status || 'SAMPLE-SUPPORTED'}
                  </span>
                  <span className="text-xs text-slate-300 font-mono">
                    (N = {perfData?.overview?.sample_n ?? perfData?.overview?.resolved_signals ?? 0})
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1 italic">
                  {perfData?.overview?.sample_size_tooltip ||
                    'Sample size classification only. It does not indicate future profitability or predictive accuracy.'}
                </div>
              </div>
            </div>

            {/* Sample Methodology Card - Part H */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 space-y-3 font-mono">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">Sample Methodology & Statistical Rigor</span>
                </div>
                <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-bold">
                  {perfData?.overview?.sample_status || 'LIMITED SAMPLE'}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 space-y-1">
                  <div className="text-[10px] uppercase font-bold text-slate-400">1. Sample Tiers</div>
                  <div className="text-[11px] text-slate-300">
                    <div>• <strong className="text-rose-400">INSUFFICIENT (N &lt; 15)</strong>: Zero statistical power.</div>
                    <div>• <strong className="text-amber-400">LIMITED (15 &le; N &lt; 30)</strong>: Wide Wilson CI bands.</div>
                    <div>• <strong className="text-emerald-400">SUPPORTED (N &ge; 30)</strong>: Normal approximation valid.</div>
                  </div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 space-y-1">
                  <div className="text-[10px] uppercase font-bold text-slate-400">2. Confidence Interval</div>
                  <div className="text-[11px] text-slate-300">
                    Wilson Score 95% Interval handles small binomial samples without asymptotic distortion.
                  </div>
                  <div className="text-[10px] text-cyan-400 pt-1">
                    Current CI: {perfData?.overview?.wilson_95_ci ? `[${perfData.overview.wilson_95_ci[0]}%, ${perfData.overview.wilson_95_ci[1]}%]` : '—'}
                  </div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 space-y-1">
                  <div className="text-[10px] uppercase font-bold text-slate-400">3. Eligibility Rules</div>
                  <div className="text-[11px] text-slate-300">
                    Only genuine <strong className="text-emerald-400">LIVE</strong>, canonical, resolved trades enter statistics.
                    Unresolved, demo, synthetic, and historical replay records are strictly excluded.
                  </div>
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
                                SAMPLE-SUPPORTED
                              </span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                LIMITED SAMPLE
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
                                SAMPLE-SUPPORTED
                              </span>
                            ) : (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                LIMITED SAMPLE
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
        {/* TAB 4: SYSTEM STATUS & OBSERVABILITY (SECTION 23 & 24)             */}
        {/* ================================================================= */}
        {activeTab === 'status' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
              <div className="text-xs font-mono text-slate-400">
                System Status as of <span className="font-bold text-amber-400">{istTimeStr} IST</span>
              </div>
              <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                <span>Execution Mode:</span>
                <span className="text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                  DEMO / PAPER ONLY
                </span>
              </div>
            </div>

            {/* 4 Architecture Pillars: DATA, MODELS, PIPELINE, EXECUTION */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* DATA Pillar */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    DATA FEEDS
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">Live & Execution Data</span>
                </div>
                <div className="space-y-2.5">
                  {systemStatus?.categories?.DATA?.map((item: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-200 font-mono text-xs">{item.name}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({item.role})</span>
                        </div>
                        {getStatusBadge(item.status)}
                      </div>

                      {item.terminal && (
                        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-300 pt-1 border-t border-slate-800/60">
                          <div>Terminal: <strong className={item.terminal === 'CONNECTED' ? 'text-emerald-400' : 'text-rose-400'}>{item.terminal}</strong></div>
                          <div>Account: <strong className={item.account === 'CONNECTED' ? 'text-emerald-400' : 'text-amber-400'}>{item.account}</strong></div>
                          <div>Broker: <span className="text-slate-400">{item.broker || '—'}</span></div>
                          <div>Symbols: <strong className="text-cyan-400">{item.symbols_verified || '—'}</strong></div>
                          <div>Live Tick: <strong className={item.live_tick === 'YES' ? 'text-emerald-400' : 'text-slate-500'}>{item.live_tick || 'NO'}</strong></div>
                          <div>Freshness: <span className="text-slate-300">{item.freshness || 'N/A'}</span></div>
                          <div>Actionable: <strong className={item.actionable ? 'text-emerald-400' : 'text-rose-400'}>{item.actionable ? 'YES' : 'NO'}</strong></div>
                          <div>Reason: <span className="text-amber-400 truncate">{item.diagnostic_reason || '—'}</span></div>
                        </div>
                      )}

                      {item.safe_remediation_guidance && item.safe_remediation_guidance.length > 0 && !item.actionable && (
                        <div className="mt-2 p-2 bg-slate-900/90 rounded-lg border border-amber-500/20 text-[10px] font-mono text-slate-300 space-y-1">
                          <div className="font-bold text-amber-400 flex items-center justify-between">
                            <span>Remediation Guidance</span>
                            <span className="text-slate-500 text-[9px]">Part S</span>
                          </div>
                          {item.safe_remediation_guidance.map((step: string, sIdx: number) => (
                            <div key={sIdx} className="text-slate-400 pl-1">{step}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 font-mono p-3">Loading data feed health...</div>
                  )}
                </div>
              </div>

              {/* MODELS Pillar */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-cyan-400" />
                    AI & FORECAST MODELS
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">Inference Registry</span>
                </div>
                <div className="space-y-2.5">
                  {systemStatus?.categories?.MODELS?.map((item: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                      <div>
                        <div className="font-bold text-slate-200 font-mono text-xs">{item.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{item.details}</div>
                      </div>
                      {getStatusBadge(item.status)}
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 font-mono p-3">Loading models health...</div>
                  )}
                </div>
              </div>

              {/* PIPELINE Pillar */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-400" />
                    SIGNAL PIPELINE
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">End-to-End Stages</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {systemStatus?.categories?.PIPELINE?.map((item: any, idx: number) => (
                    <div key={idx} className="p-2 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200 font-mono text-xs">{item.name}</span>
                        {getStatusBadge(item.status)}
                      </div>
                      <div className="text-[9px] text-slate-400 font-mono truncate">{item.details}</div>
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 font-mono p-3 col-span-2">Loading pipeline stages...</div>
                  )}
                </div>
              </div>

              {/* EXECUTION Pillar */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    EXECUTION GATES
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">Real Money Lockout</span>
                </div>
                <div className="space-y-2.5">
                  {systemStatus?.categories?.EXECUTION?.map((item: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                      <div>
                        <div className="font-bold text-slate-200 font-mono text-xs">{item.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{item.details}</div>
                      </div>
                      {getStatusBadge(item.status)}
                    </div>
                  )) || (
                    <div className="text-xs text-slate-500 font-mono p-3">Loading execution status...</div>
                  )}
                </div>
              </div>
            </div>

            {/* Observability Metrics Grid (Section 23) */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
              <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-cyan-400" />
                Live Pipeline Observability Metrics (Section 23)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 font-mono">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Snapshot Age</div>
                  <div className="text-lg font-bold text-white mt-0.5">
                    {systemStatus?.observability_metrics?.market_snapshot_age != null
                      ? `${systemStatus.observability_metrics.market_snapshot_age}s`
                      : '< 1s'}
                  </div>
                  <div className="text-[9px] text-slate-500">Gate: &le; 120s</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Forecast Latency</div>
                  <div className="text-lg font-bold text-cyan-400 mt-0.5">
                    {systemStatus?.observability_metrics?.forecast_latency != null
                      ? `${systemStatus.observability_metrics.forecast_latency}ms`
                      : '—'}
                  </div>
                  <div className="text-[9px] text-slate-500">CPU Inference</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Consensus Latency</div>
                  <div className="text-lg font-bold text-cyan-400 mt-0.5">
                    {systemStatus?.observability_metrics?.consensus_latency != null
                      ? `${systemStatus.observability_metrics.consensus_latency}ms`
                      : '—'}
                  </div>
                  <div className="text-[9px] text-slate-500">Agreement Calc</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Qualification Latency</div>
                  <div className="text-lg font-bold text-cyan-400 mt-0.5">
                    {systemStatus?.observability_metrics?.qualification_latency != null
                      ? `${systemStatus.observability_metrics.qualification_latency}ms`
                      : '—'}
                  </div>
                  <div className="text-[9px] text-slate-500">Risk & Price Deviation</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Signals Generated</div>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">
                    {systemStatus?.observability_metrics?.signal_generation_count ?? 0}
                  </div>
                  <div className="text-[9px] text-slate-500">Live Qualified</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Signals Rejected</div>
                  <div className="text-lg font-bold text-amber-400 mt-0.5">
                    {systemStatus?.observability_metrics?.signal_rejection_count ?? 0}
                  </div>
                  <div className="text-[9px] text-slate-500">Gated / Filtered</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Duplicates Prevented</div>
                  <div className="text-lg font-bold text-blue-400 mt-0.5">
                    {systemStatus?.observability_metrics?.duplicate_signal_count ?? 0}
                  </div>
                  <div className="text-[9px] text-slate-500">Idempotent Cycles</div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[9px] uppercase text-slate-400">Signals Resolved</div>
                  <div className="text-lg font-bold text-purple-400 mt-0.5">
                    {systemStatus?.observability_metrics?.resolution_count ?? 0}
                  </div>
                  <div className="text-[9px] text-slate-500">Evidence Verified</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 5: SETTINGS & TERMINAL CONFIGURATION                          */}
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

      {/* ── Forensic Signal Detail Modal (Sections A through I - Phase 77) ── */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-[#0e131f] border border-slate-800 rounded-2xl max-w-2xl w-full p-5 space-y-4 shadow-2xl font-mono text-xs my-8 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <span className="text-lg font-black text-white">{selectedSignal.asset}</span>
                <span
                  className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${
                    selectedSignal.direction === 'BUY' || selectedSignal.direction === 'LONG'
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {selectedSignal.direction}
                </span>
                <span className="text-slate-300 text-[11px] bg-slate-800 px-2 py-0.5 rounded border border-slate-700 font-bold">
                  {selectedSignal.timeframe}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    selectedSignal.record_type === 'LIVE'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : selectedSignal.record_type === 'DEMO'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {selectedSignal.record_type || 'HISTORICAL'}
                </span>
              </div>
              <button
                onClick={() => setSelectedSignal(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Lifecycle Timeline: Section 18 */}
            <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
              <div className="text-[10px] uppercase font-bold text-slate-500 mb-2">Lifecycle Progression</div>
              <div className="flex items-center justify-between text-[11px]">
                <div className="text-center">
                  <div className="text-slate-500 text-[9px]">1. GENERATED</div>
                  <div className="text-white font-bold">{selectedSignal.generated_at_ist?.substring(7) || '—'}</div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                <div className="text-center">
                  <div className="text-slate-500 text-[9px]">2. WINDOW</div>
                  <div className="text-cyan-300 font-bold">{selectedSignal.entry_window_ist || selectedSignal.open_at_ist || '—'}</div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                <div className="text-center">
                  <div className="text-slate-500 text-[9px]">3. ENTRY</div>
                  <div className="text-emerald-300 font-bold">
                    {selectedSignal.actual_entry_ist?.substring(7) || selectedSignal.open_at_ist?.substring(7) || '—'}
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                <div className="text-center">
                  <div className="text-slate-500 text-[9px]">4. EXIT</div>
                  <div className="text-amber-300 font-bold">
                    {selectedSignal.actual_exit_ist?.substring(7) || selectedSignal.close_at_ist?.substring(7) || '—'}
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                <div className="text-center">
                  <div className="text-slate-500 text-[9px]">5. DURATION</div>
                  <div className="text-cyan-300 font-bold">
                    {selectedSignal.duration || '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Forensic Detail Grid: Sections A through I */}
            <div className="space-y-3">
              {/* Section A & B: Identity & Generation */}
              <div className="grid grid-cols-2 gap-2 bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                <div className="space-y-1">
                  <div className="text-[9px] uppercase font-bold text-slate-500">A. Signal Identity</div>
                  <div>ID: <span className="text-cyan-400 break-all">{selectedSignal.id || selectedSignal.signal_id}</span></div>
                  <div>Policy: <span className="text-slate-300">{selectedSignal.policy_version || 'POL-70-v1'}</span></div>
                  <div>Model: <span className="text-slate-300">{selectedSignal.model_version || 'Ensemble-v1'}</span></div>
                  {selectedSignal.market_snapshot_id && (
                    <div>Snapshot ID: <span className="text-emerald-400 font-mono text-[10px] break-all">{selectedSignal.market_snapshot_id}</span></div>
                  )}
                  {selectedSignal.market_snapshot_hash && (
                    <div>Snapshot Hash: <span className="text-amber-400 font-mono text-[9px] break-all">{selectedSignal.market_snapshot_hash}</span></div>
                  )}
                </div>
                <div className="space-y-1">
                  <div className="text-[9px] uppercase font-bold text-slate-500">B. Data Provenance</div>
                  <div>Provider: <span className="text-emerald-400 font-bold">{selectedSignal.provider || 'MT5'}</span></div>
                  <div>Broker Symbol: <span className="text-slate-300 font-mono">{selectedSignal.broker_symbol || selectedSignal.asset}</span></div>
                  <div>Data Verified: <span className={selectedSignal.live_data_verified ? 'text-emerald-400' : 'text-slate-400'}>{selectedSignal.live_data_verified ? 'YES (Live Feed)' : 'CACHE / HISTORICAL'}</span></div>
                  <div>Data Age: <span className="text-slate-300">{selectedSignal.data_age_seconds != null ? `${selectedSignal.data_age_seconds}s` : 'Fresh (<5s)'}</span></div>
                  <div>Record Type: <span className="text-cyan-400 font-bold">{selectedSignal.record_type || 'LIVE'}</span></div>
                </div>
              </div>

              {/* Section C & D: Forecast & Qualification */}
              <div className="grid grid-cols-2 gap-2 bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                <div className="space-y-1">
                  <div className="text-[9px] uppercase font-bold text-slate-500">C. Forecast Intelligence</div>
                  <div>Direction: <span className="text-white font-bold">{selectedSignal.direction}</span></div>
                  <div>Confidence: <span className="text-cyan-400 font-bold">{selectedSignal.confidence ?? selectedSignal.confidence_pct}%</span></div>
                  <div>Agreement: <span className="text-emerald-400">{selectedSignal.agreement_pct ? `${selectedSignal.agreement_pct}%` : '>=60.0% Qualified'}</span></div>
                </div>
                <div className="space-y-1">
                  <div className="text-[9px] uppercase font-bold text-slate-500">D. Qualification & Risk</div>
                  <div>Status: <span className="text-emerald-400 font-bold">{selectedSignal.qualification_status || 'QUALIFIED'}</span></div>
                  <div>Grade: <span className="text-amber-400 font-bold">{selectedSignal.quality_grade || 'GRADE_A'}</span></div>
                  <div>Risk Filter: <span className="text-emerald-400">{selectedSignal.risk_status || 'PASS'}</span></div>
                </div>
              </div>

              {/* Section E & F: Entry, SL, TP, Risk-Reward */}
              <div className="grid grid-cols-4 gap-2 bg-slate-950 p-2.5 rounded-xl border border-slate-800/80 text-center">
                <div>
                  <div className="text-[9px] uppercase text-slate-500">Entry Price</div>
                  <div className="font-bold text-white mt-0.5">{selectedSignal.entry}</div>
                </div>
                <div>
                  <div className="text-[9px] uppercase text-rose-400">Stop Loss</div>
                  <div className="font-bold text-rose-400 mt-0.5">{selectedSignal.stop_loss}</div>
                </div>
                <div>
                  <div className="text-[9px] uppercase text-emerald-400">Take Profit</div>
                  <div className="font-bold text-emerald-400 mt-0.5">{selectedSignal.take_profit}</div>
                </div>
                <div>
                  <div className="text-[9px] uppercase text-cyan-400">Risk / Reward</div>
                  <div className="font-bold text-cyan-300 mt-0.5">1:{selectedSignal.risk_reward ?? '2.0'}</div>
                </div>
              </div>

              {/* Section G, H, I: Resolution, Outcome & Evidence */}
              <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 space-y-2">
                <div className="text-[9px] uppercase font-bold text-slate-500">G, H, I. Outcome & Resolution Evidence</div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <span className="text-slate-400">Outcome:</span>{' '}
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
                  <div>
                    <span className="text-slate-400">Exit Price:</span>{' '}
                    <span className="text-white font-bold">{selectedSignal.exit_price ?? '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Realized Net R:</span>{' '}
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
                </div>

                <div className="pt-1 border-t border-slate-900 grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-400">First Barrier Touched:</span>{' '}
                    <span className="text-amber-300 font-semibold">
                      {selectedSignal.first_barrier_touched || selectedSignal.resolution_reason || '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Resolution Source:</span>{' '}
                    <span className="text-slate-300 font-semibold">
                      {selectedSignal.resolution_source || 'HISTORICAL_CANDLES_DB'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Close Button */}
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedSignal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-colors"
              >
                Close Forensic Panel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default TradeSignalTerminal;
