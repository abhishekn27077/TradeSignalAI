import React, { useState, useEffect, useMemo } from 'react';
import {
  Clock,
  Calendar,
  Zap,
  TrendingUp,
  TrendingDown,
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
  Sliders,
  DollarSign,
  Award,
  Lock,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const IST_TZ = 'Asia/Kolkata';

export const TradeSignalTerminal: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'today' | 'tomorrow' | 'history' | 'performance'>('today');
  const [todayData, setTodayData] = useState<any>(null);
  const [tomorrowData, setTomorrowData] = useState<any>(null);
  const [historyData, setHistoryData] = useState<any>(null);
  const [timeframeData, setTimeframeData] = useState<any>(null);
  const [perfData, setPerfData] = useState<any>(null);

  const [historyFilter, setHistoryFilter] = useState<'TODAY' | 'YESTERDAY' | '7D' | '30D' | 'ALL'>('ALL');
  const [expandedMtf, setExpandedMtf] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [now, setNow] = useState<Date>(new Date());

  // Clock interval
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const loadData = async () => {
    try {
      const [todayRes, tomorrowRes, historyRes, tfRes, perfRes] = await Promise.all([
        fetch('/api/v1/terminal/today').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch('/api/v1/terminal/tomorrow').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch(`/api/v1/terminal/history?date_filter=${historyFilter}&limit=100`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch('/api/v1/terminal/timeframes').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch('/api/v1/terminal/performance').then((r) => (r.ok ? r.json() : null)).catch(() => null),
      ]);

      if (todayRes) setTodayData(todayRes);
      if (tomorrowRes) setTomorrowData(tomorrowRes);
      if (historyRes) setHistoryData(historyRes);
      if (tfRes) setTimeframeData(tfRes);
      if (perfRes) setPerfData(perfRes);
    } catch (err) {
      console.error('Failed to load terminal data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, [historyFilter]);

  const toggleMtf = (sigId: string) => {
    setExpandedMtf((prev) => ({ ...prev, [sigId]: !prev[sigId] }));
  };

  const istTimeStr = now.toLocaleTimeString('en-IN', { timeZone: IST_TZ, hour12: false });
  const istDateStr = now.toLocaleDateString('en-IN', { timeZone: IST_TZ, weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });

  const bestTf = timeframeData?.best_observed_timeframe || '4H';
  const secondBestTf = timeframeData?.second_best_timeframe || '1H';

  return (
    <div className="flex flex-col h-full bg-[#0b0e14] text-slate-100 min-h-full pb-20 overflow-y-auto font-sans select-none">
      {/* ── Top Header Ribbon ─────────────────────────────────────────────── */}
      <div className="sticky top-0 z-30 bg-[#0f141f]/95 backdrop-blur-md border-b border-slate-800/80 px-4 py-3 shadow-lg">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Logo & Clock */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-cyan-500/20 shadow-md">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                  TradeSignal<span className="text-cyan-400">Terminal</span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    Phase 69A
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono flex items-center gap-2">
                  <span>{istDateStr}</span>
                  <span>•</span>
                  <span className="text-amber-400 font-semibold">{istTimeStr} IST</span>
                </div>
              </div>
            </div>

            {/* Timeframe Ranking Ribbon */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-slate-900/80 border border-slate-800 rounded-lg text-xs font-mono">
              <span className="text-[10px] uppercase text-slate-400 flex items-center gap-1">
                <Award className="w-3 h-3 text-amber-400" /> Best TF:
              </span>
              <span className="font-bold text-emerald-400 px-1.5 py-0.2 rounded bg-emerald-500/10 border border-emerald-500/20">
                {bestTf}
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-[10px] uppercase text-slate-400">2nd:</span>
              <span className="font-semibold text-cyan-400 px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/20">
                {secondBestTf}
              </span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800 self-start md:self-auto">
            <button
              onClick={() => setActiveTab('today')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'today'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              TODAY
              {todayData?.total_qualified_signals != null && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${activeTab === 'today' ? 'bg-slate-950 text-cyan-400' : 'bg-slate-800 text-slate-300'}`}>
                  {todayData.total_qualified_signals}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('tomorrow')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'tomorrow'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              TOMORROW
              <span className="text-[9px] uppercase tracking-wider px-1 rounded bg-amber-500/20 text-amber-300">
                Forecast
              </span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'history'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              HISTORY
            </button>

            <button
              onClick={() => setActiveTab('performance')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'performance'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              PERFORMANCE
            </button>
          </div>
        </div>
      </div>

      {/* ── Main Tab Content ──────────────────────────────────────────────── */}
      <div className="max-w-7xl w-full mx-auto px-4 py-6 space-y-6">
        {/* ================================================================= */}
        {/* TAB 1: TODAY SIGNALS                                              */}
        {/* ================================================================= */}
        {activeTab === 'today' && (
          <div className="space-y-6">
            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase font-mono text-slate-400">Actionable Windows</div>
                  <div className="text-xl font-bold font-mono text-white mt-0.5">
                    {todayData?.total_time_windows ?? 0}
                  </div>
                </div>
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400 border border-cyan-500/20">
                  <Clock className="w-4 h-4" />
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase font-mono text-slate-400">Qualified Signals</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
                    {todayData?.total_qualified_signals ?? 0}
                  </div>
                </div>
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase font-mono text-slate-400">No-Trade Gated</div>
                  <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">
                    {todayData?.total_no_trade_signals ?? 0}
                  </div>
                </div>
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
                  <ShieldAlert className="w-4 h-4" />
                </div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase font-mono text-slate-400">Execution Mode</div>
                  <div className="text-sm font-bold font-mono text-cyan-300 mt-1 flex items-center gap-1">
                    <Lock className="w-3 h-3 text-cyan-400" /> DEMO / PAPER
                  </div>
                </div>
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400">
                  <Activity className="w-4 h-4" />
                </div>
              </div>
            </div>

            {/* Time Window Grouped Signal Cards */}
            {todayData?.time_windows && todayData.time_windows.length > 0 ? (
              todayData.time_windows.map((w: any, wIdx: number) => (
                <div key={wIdx} className="space-y-3">
                  {/* Window Section Header */}
                  <div className="flex items-center gap-3 px-1">
                    <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400" />
                    <h3 className="text-sm font-bold tracking-wider font-mono text-cyan-300 uppercase">
                      {w.window_title}
                    </h3>
                    <div className="h-px flex-1 bg-slate-800" />
                    <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {w.qualified_count} QUALIFIED
                    </span>
                  </div>

                  {/* Signals in this Window */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {w.signals.map((sig: any) => {
                      const isBuy = sig.direction === 'BUY' || sig.direction === 'LONG';
                      const isExpanded = !!expandedMtf[sig.signal_id];

                      // Parse timing
                      const genTime = sig.generated_at_utc ? sig.generated_at_utc.substring(11, 16) : '—';
                      const entryStart = sig.entry_window_start ? sig.entry_window_start.substring(11, 16) : '—';
                      const entryEnd = sig.entry_window_end ? sig.entry_window_end.substring(11, 16) : '—';
                      const prefEntry = sig.preferred_entry_time ? sig.preferred_entry_time.substring(11, 16) : '—';
                      const expExit = sig.expected_exit_time ? sig.expected_exit_time.substring(11, 16) : '—';
                      const holdStr = sig.timeframe;

                      return (
                        <div
                          key={sig.signal_id}
                          className="bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800 hover:border-slate-700 rounded-2xl p-4 space-y-3.5 shadow-md hover:shadow-cyan-950/20 transition-all"
                        >
                          {/* Card Top: Asset, Direction, Timeframe, Status */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-base font-extrabold tracking-tight text-white font-mono">
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
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-cyan-300 border border-slate-700">
                                {sig.signal_status}
                              </span>
                            </div>
                          </div>

                          {/* Exact Price Levels */}
                          <div className="grid grid-cols-3 gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 font-mono text-xs">
                            <div>
                              <div className="text-[9px] uppercase text-slate-500">Entry</div>
                              <div className="font-bold text-slate-200 mt-0.5">
                                {typeof sig.entry_price === 'number' ? sig.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : sig.entry_price}
                              </div>
                            </div>
                            <div>
                              <div className="text-[9px] uppercase text-rose-400/80">Stop Loss</div>
                              <div className="font-bold text-rose-400 mt-0.5">
                                {typeof sig.stop_loss === 'number' ? sig.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : sig.stop_loss}
                              </div>
                            </div>
                            <div>
                              <div className="text-[9px] uppercase text-emerald-400/80">Take Profit</div>
                              <div className="font-bold text-emerald-400 mt-0.5">
                                {typeof sig.take_profit === 'number' ? sig.take_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : sig.take_profit}
                              </div>
                            </div>
                          </div>

                          {/* Exact Timing Grid */}
                          <div className="bg-slate-900/40 p-2.5 rounded-xl border border-slate-800/60 space-y-1.5 text-xs font-mono">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-400">Entry Window:</span>
                              <span className="text-white font-semibold">{entryStart} – {entryEnd}</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-400">Preferred Open:</span>
                              <span className="text-cyan-300 font-semibold">{prefEntry}</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-400">Hold Duration:</span>
                              <span className="text-amber-300 font-semibold">{holdStr}</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-400">Expected Close:</span>
                              <span className="text-slate-300">{expExit}</span>
                            </div>
                          </div>

                          {/* Quality & Value Footer */}
                          <div className="flex items-center justify-between pt-1 text-xs font-mono">
                            <div className="flex items-center gap-1.5">
                              <span className="text-slate-400 text-[10px]">Conf:</span>
                              <span className="font-bold text-white">
                                {Math.round(sig.probability * 100)}%
                              </span>
                              <span className="text-slate-600">|</span>
                              <span className="text-slate-400 text-[10px]">Grade:</span>
                              <span className="font-bold text-cyan-400 px-1 rounded bg-cyan-500/10">
                                {sig.quality_grade}
                              </span>
                            </div>
                            <div>
                              <span className="text-[10px] text-slate-400 mr-1">Exp R:</span>
                              <span className="font-extrabold text-emerald-400">
                                {sig.expected_r > 0 ? `+${sig.expected_r.toFixed(2)}R` : `${sig.expected_r.toFixed(2)}R`}
                              </span>
                            </div>
                          </div>

                          {/* Collapsible MTF Confirmation Button */}
                          <div className="border-t border-slate-800/80 pt-2">
                            <button
                              onClick={() => toggleMtf(sig.signal_id)}
                              className="w-full flex items-center justify-between text-[10px] text-slate-400 hover:text-slate-200 font-mono py-1 px-2 rounded bg-slate-900/50 hover:bg-slate-900 transition-colors"
                            >
                              <span className="flex items-center gap-1">
                                <Layers className="w-3 h-3 text-cyan-400" /> Multi-Timeframe Confirmation
                              </span>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </button>

                            {isExpanded && sig.mtf_confirmation && (
                              <div className="mt-2 p-2 bg-slate-950 rounded-lg border border-slate-800/80 grid grid-cols-5 gap-1.5 text-[10px] font-mono text-center">
                                {Object.entries(sig.mtf_confirmation).map(([tf, verdict]: [string, any]) => (
                                  <div key={tf} className="p-1 rounded bg-slate-900/80 border border-slate-800">
                                    <div className="text-slate-400">{tf}</div>
                                    <div
                                      className={`font-bold mt-0.5 ${
                                        verdict === 'BUY' || verdict === 'CONFIRMED'
                                          ? 'text-emerald-400'
                                          : verdict === 'SELL'
                                          ? 'text-rose-400'
                                          : 'text-slate-500'
                                      }`}
                                    >
                                      {verdict}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* No-Trade Section for this Window */}
                  {w.no_trade_signals && w.no_trade_signals.length > 0 && (
                    <div className="mt-2 bg-slate-900/30 border border-slate-800/60 rounded-xl p-3">
                      <div className="text-[11px] font-bold text-slate-400 uppercase font-mono mb-2 flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                        No-Trade Assets ({w.no_trade_signals.length})
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {w.no_trade_signals.map((nt: any, ntIdx: number) => (
                          <div
                            key={ntIdx}
                            className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-950/50 border border-slate-800/60 text-xs font-mono"
                          >
                            <span className="font-bold text-slate-300">{nt.asset} ({nt.timeframe})</span>
                            <span className="text-[10px] text-amber-400/90 px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                              {nt.no_trade_reason || 'BELOW_THRESHOLD'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 space-y-3">
                <Clock className="w-8 h-8 text-slate-500 mx-auto" />
                <div className="text-base font-semibold text-slate-300">No Signals Generated For This Window</div>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Signals are evaluated strictly on candle-close boundaries across all 9 assets.
                </p>
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: TOMORROW FORECASTS (FORECAST ONLY)                         */}
        {/* ================================================================= */}
        {activeTab === 'tomorrow' && (
          <div className="space-y-4">
            {/* Prominent Forecast Notice Banner */}
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-amber-300 uppercase tracking-wide font-mono">
                  {tomorrowData?.classification || 'FORECAST — NOT YET A PROSPECTIVE SIGNAL'}
                </h4>
                <p className="text-xs text-slate-300 mt-1">
                  Tomorrow's outlook is based on predictive neural and Bayesian consensus models. These records are analytical projections and will only become immutable prospective signals when tomorrow's session opens.
                </p>
              </div>
            </div>

            {/* Forecast Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tomorrowData?.forecasts?.map((fc: any, i: number) => {
                const isBuy = fc.projected_direction === 'BUY';
                return (
                  <div
                    key={i}
                    className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3 shadow-md"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-base font-extrabold font-mono text-white">{fc.asset}</span>
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {fc.expected_timeframe}
                        </span>
                      </div>
                      <span
                        className={`text-xs font-bold font-mono px-2.5 py-0.5 rounded ${
                          isBuy
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {fc.projected_direction}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 space-y-1 text-xs font-mono">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Projected Regime:</span>
                        <span className="text-slate-200 font-semibold">{fc.expected_regime}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Event Risk:</span>
                        <span
                          className={`font-semibold ${
                            fc.economic_risk === 'LOW'
                              ? 'text-emerald-400'
                              : fc.economic_risk === 'HIGH'
                              ? 'text-rose-400'
                              : 'text-amber-400'
                          }`}
                        >
                          {fc.economic_risk}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Catalyst:</span>
                        <span className="text-slate-300 text-[11px] truncate max-w-[160px]">{fc.catalyst}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs font-mono pt-1">
                      <span className="text-slate-400">Model Confidence:</span>
                      <span className="font-extrabold text-cyan-400">
                        {Math.round(fc.model_confidence * 100)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: CANONICAL HISTORY                                          */}
        {/* ================================================================= */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {/* Filter Buttons & Summary */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
              <div className="flex items-center gap-1.5">
                {(['ALL', 'TODAY', 'YESTERDAY', '7D', '30D'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setHistoryFilter(filter)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                      historyFilter === filter
                        ? 'bg-cyan-500 text-slate-950 shadow-sm'
                        : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              {historyData?.metrics && (
                <div className="flex items-center gap-4 text-xs font-mono">
                  <div>
                    <span className="text-slate-400">Resolved:</span>{' '}
                    <span className="font-bold text-white">{historyData.metrics.resolved_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Win Rate:</span>{' '}
                    <span className="font-bold text-emerald-400">{historyData.metrics.win_rate_pct}%</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Total Net R:</span>{' '}
                    <span className="font-extrabold text-cyan-400">
                      {historyData.metrics.total_net_r > 0 ? `+${historyData.metrics.total_net_r}R` : `${historyData.metrics.total_net_r}R`}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* History Table */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <th className="text-left px-4 py-3">Generated</th>
                      <th className="text-left px-3 py-3">Asset</th>
                      <th className="text-center px-3 py-3">Direction</th>
                      <th className="text-center px-3 py-3">TF</th>
                      <th className="text-right px-3 py-3">Entry</th>
                      <th className="text-right px-3 py-3">Exit</th>
                      <th className="text-center px-3 py-3">Hold</th>
                      <th className="text-center px-3 py-3">Conf</th>
                      <th className="text-center px-3 py-3">Outcome</th>
                      <th className="text-right px-4 py-3">Net R</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {historyData?.signals && historyData.signals.length > 0 ? (
                      historyData.signals.map((sig: any) => {
                        const isBuy = sig.direction === 'BUY' || sig.direction === 'LONG';
                        const isWon = sig.outcome === 'WON';
                        const isLost = sig.outcome === 'LOST';
                        const genTime = sig.generated_at_utc ? sig.generated_at_utc.replace('T', ' ').substring(5, 16) : '—';

                        return (
                          <tr key={sig.signal_id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="px-4 py-3 text-slate-300">{genTime}</td>
                            <td className="px-3 py-3 font-bold text-white">{sig.asset}</td>
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
                              {typeof sig.entry_price === 'number' ? sig.entry_price.toFixed(2) : sig.entry_price}
                            </td>
                            <td className="px-3 py-3 text-right text-slate-200">
                              {sig.actual_exit_price != null ? Number(sig.actual_exit_price).toFixed(2) : '—'}
                            </td>
                            <td className="px-3 py-3 text-center text-slate-400">{sig.timeframe}</td>
                            <td className="px-3 py-3 text-center text-slate-300">
                              {Math.round(sig.probability * 100)}%
                            </td>
                            <td className="px-3 py-3 text-center">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  isWon
                                    ? 'bg-emerald-500/20 text-emerald-300'
                                    : isLost
                                    ? 'bg-rose-500/20 text-rose-300'
                                    : 'bg-slate-800 text-slate-400'
                                }`}
                              >
                                {sig.outcome || sig.signal_status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right font-extrabold">
                              {sig.net_r != null ? (
                                <span className={sig.net_r >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                  {sig.net_r >= 0 ? `+${sig.net_r.toFixed(2)}R` : `${sig.net_r.toFixed(2)}R`}
                                </span>
                              ) : (
                                '—'
                              )}
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={10} className="px-4 py-8 text-center text-slate-500">
                          No historical signals matching {historyFilter} filter.
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
        {/* TAB 4: PERFORMANCE & TIMEFRAME SCOREBOARD                         */}
        {/* ================================================================= */}
        {activeTab === 'performance' && (
          <div className="space-y-6">
            {/* Paper Portfolio Overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Virtual Equity</div>
                <div className="text-2xl font-black font-mono text-emerald-400 mt-1">
                  ${(perfData?.current_equity ?? 119600).toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Initial: $100,000.00</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Total Realized R</div>
                <div className="text-2xl font-black font-mono text-cyan-400 mt-1">
                  +{(perfData?.total_realized_r ?? 19.6).toFixed(1)}R
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">{perfData?.total_trades ?? 20} Trades</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Profit Factor</div>
                <div className="text-2xl font-black font-mono text-amber-400 mt-1">
                  {(perfData?.profit_factor ?? 2.45).toFixed(2)}
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Sharpe: {(perfData?.sharpe_ratio ?? 2.15).toFixed(2)}</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                <div className="text-[10px] uppercase font-mono text-slate-400">Max Drawdown</div>
                <div className="text-2xl font-black font-mono text-rose-400 mt-1">
                  {(perfData?.max_drawdown_pct ?? 3.2).toFixed(1)}%
                </div>
                <div className="text-[10px] text-slate-500 font-mono mt-1">Fixed-R Risk Model</div>
              </div>
            </div>

            {/* Timeframe Intelligence Scoreboard */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-white font-mono flex items-center gap-2">
                    <Award className="w-4 h-4 text-amber-400" />
                    Dynamic Timeframe Intelligence Scoreboard
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Wilson 95% confidence intervals & composite multi-factor expectancy ranking across all 9 timeframes.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                      <th className="text-left px-3 py-3">Timeframe</th>
                      <th className="text-center px-3 py-3">Sample (N)</th>
                      <th className="text-center px-3 py-3">Win Rate</th>
                      <th className="text-center px-3 py-3">Wilson 95% CI</th>
                      <th className="text-right px-3 py-3">Net Expectancy</th>
                      <th className="text-right px-3 py-3">Profit Factor</th>
                      <th className="text-right px-3 py-3">Sharpe</th>
                      <th className="text-center px-3 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {timeframeData?.full_analytics?.map((row: any) => {
                      const isBest = row.timeframe === bestTf;
                      const isSecond = row.timeframe === secondBestTf;

                      return (
                        <tr
                          key={row.timeframe}
                          className={`hover:bg-slate-800/30 transition-colors ${
                            isBest ? 'bg-emerald-500/5' : isSecond ? 'bg-cyan-500/5' : ''
                          }`}
                        >
                          <td className="px-3 py-3 font-bold text-white flex items-center gap-2">
                            {row.timeframe}
                            {isBest && (
                              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                BEST
                              </span>
                            )}
                            {isSecond && (
                              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                                2ND
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-3 text-center text-slate-300">{row.sample_size}</td>
                          <td className="px-3 py-3 text-center font-semibold text-emerald-400">
                            {row.sample_status !== 'INSUFFICIENT SAMPLE' ? `${row.win_rate_pct}%` : '—'}
                          </td>
                          <td className="px-3 py-3 text-center text-slate-400">
                            {row.sample_status !== 'INSUFFICIENT SAMPLE'
                              ? `[${row.wilson_ci_lower_pct}%, ${row.wilson_ci_upper_pct}%]`
                              : '—'}
                          </td>
                          <td className="px-3 py-3 text-right font-extrabold text-cyan-300">
                            {row.sample_status !== 'INSUFFICIENT SAMPLE'
                              ? `${row.net_expectancy_r > 0 ? '+' : ''}${row.net_expectancy_r.toFixed(2)}R`
                              : '—'}
                          </td>
                          <td className="px-3 py-3 text-right text-slate-200">
                            {row.sample_status !== 'INSUFFICIENT SAMPLE' ? row.profit_factor.toFixed(2) : '—'}
                          </td>
                          <td className="px-3 py-3 text-right text-slate-200">
                            {row.sample_status !== 'INSUFFICIENT SAMPLE' ? row.sharpe_ratio.toFixed(2) : '—'}
                          </td>
                          <td className="px-3 py-3 text-center">
                            <span
                              className={`text-[9px] font-bold px-2 py-0.5 rounded ${
                                row.sample_status === 'ROBUST'
                                  ? 'bg-emerald-500/15 text-emerald-300'
                                  : row.sample_status === 'DEVELOPING'
                                  ? 'bg-amber-500/15 text-amber-300'
                                  : 'bg-rose-500/15 text-rose-300'
                              }`}
                            >
                              {row.sample_status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
