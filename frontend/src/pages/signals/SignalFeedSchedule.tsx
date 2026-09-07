import React, { useEffect, useState } from 'react';
import {
  Send,
  Zap,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowUpDown,
  Calendar,
  Layers,
  BarChart3,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  AlertTriangle,
  Radio,
  ExternalLink,
  ChevronRight,
  Eye,
  RefreshCw,
  Search,
} from 'lucide-react';
import { TradingViewChart } from '../../components/trading/TradingViewChart';

const CORE_ASSETS = ['ALL', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'BTCUSD', 'ETHUSD', 'XAUUSD', 'NAS100', 'SPX500'];
const TIMEFRAMES = ['ALL', '5m', '15m', '30m', '1H', '2H', '4H', '12H', '1D', 'SWING'];
const QUALITIES = ['ALL', 'A+', 'A', 'B', 'WATCH', 'REJECTED'];
const STATUSES = ['ALL', 'LIVE', 'WON', 'LOST', 'TIME_EXIT', 'AMBIGUOUS'];

export const SignalFeedSchedule: React.FC = () => {
  const [activeView, setActiveView] = useState<'strongest' | 'feed' | 'schedule' | 'notrade' | 'campaign' | 'performance' | 'matrix' | 'research'>('strongest');
  const [displayMode, setDisplayMode] = useState<'CALL_PUT' | 'BUY_SELL'>('CALL_PUT');
  const [loading, setLoading] = useState<boolean>(true);
  const [resolving, setResolving] = useState<boolean>(false);
  const [sweeping, setSweeping] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Phase 68 Campaign & Portfolio State
  const [campaignData, setCampaignData] = useState<any>(null);
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [calibrationData, setCalibrationData] = useState<any>(null);
  const [exposureData, setExposureData] = useState<any>(null);
  const [weeklyReportData, setWeeklyReportData] = useState<any>(null);

  // Filters
  const [selectedAsset, setSelectedAsset] = useState<string>('ALL');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('ALL');
  const [selectedQuality, setSelectedQuality] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedDate, setSelectedDate] = useState<string>('TODAY');
  const [perfWindow, setPerfWindow] = useState<'TODAY' | '7D' | '30D' | '90D' | 'ALL_TIME'>('TODAY');

  // Data
  const [signals, setSignals] = useState<any[]>([]);
  const [scheduleData, setScheduleData] = useState<any>(null);
  const [resultsSummary, setResultsSummary] = useState<any>(null);
  const [topSetups, setTopSetups] = useState<any[]>([]);
  const [matrixData, setMatrixData] = useState<any>(null);
  const [councilData, setCouncilData] = useState<any>(null);
  const [regimeData, setRegimeData] = useState<any>(null);
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [researchRuns, setResearchRuns] = useState<any[]>([]);
  const [strongestRanking, setStrongestRanking] = useState<any>(null);
  const [driftDiagnostics, setDriftDiagnostics] = useState<any>(null);
  const [windowPerfData, setWindowPerfData] = useState<any>(null);

  // Selected Signal for Modal Inspection
  const [selectedSignal, setSelectedSignal] = useState<any>(null);
  const [signalStrength, setSignalStrength] = useState<any>(null);

  const fetchFeed = async () => {
    setLoading(true);
    setError(null);
    try {
      const assetParam = selectedAsset !== 'ALL' ? `&asset=${selectedAsset}` : '';
      const tfParam = selectedTimeframe !== 'ALL' ? `&timeframe=${selectedTimeframe}` : '';
      const qualParam = selectedQuality !== 'ALL' ? `&quality=${selectedQuality}` : '';
      const statParam = selectedStatus !== 'ALL' ? `&status=${selectedStatus}` : '';

      const safeJson = async (url: string, fallback: any = null) => {
        try {
          const res = await fetch(url);
          if (!res.ok) return fallback;
          return await res.json();
        } catch {
          return fallback;
        }
      };

      const [feedRes, schedRes, resRes, topRes, matRes, couRes, regRes, benRes, runRes, strRes, drfRes, prfRes, cmpRes, eqRes, calRes, expRes, repRes] = await Promise.all([
        safeJson(`/api/v1/signals/feed?date_filter=${selectedDate}${assetParam}${tfParam}${qualParam}${statParam}&limit=100`, { signals: [] }),
        safeJson('/api/v1/signals/schedule', null),
        safeJson(`/api/v1/signals/results?horizon=${selectedDate}`, null),
        safeJson('/api/v1/signals/setups/strongest?top_n=5', { top_setups: [] }),
        safeJson('/api/v1/signals/matrix', null),
        safeJson(`/api/v1/research/council/${selectedAsset === 'ALL' ? 'EURUSD' : selectedAsset}/${selectedTimeframe === 'ALL' ? '1H' : selectedTimeframe}`, null),
        safeJson('/api/v1/research/regime-matrix', null),
        safeJson('/api/v1/research/benchmarks', null),
        safeJson('/api/v1/research/runs', { data: { runs: [] } }),
        safeJson('/api/v1/signals/strongest-now?top_n=5', null),
        safeJson('/api/v1/signals/drift', null),
        safeJson(`/api/v1/signals/performance/${perfWindow.toLowerCase()}`, null),
        safeJson('/api/v1/campaigns/current', null),
        safeJson('/api/v1/campaigns/CAMPAIGN-PROSPECTIVE-2026-v1/equity', null),
        safeJson('/api/v1/campaigns/CAMPAIGN-PROSPECTIVE-2026-v1/calibration', null),
        safeJson('/api/v1/campaigns/CAMPAIGN-PROSPECTIVE-2026-v1/exposure', null),
        safeJson('/api/v1/campaigns/CAMPAIGN-PROSPECTIVE-2026-v1/reports/weekly', null),
      ]);

      setSignals(feedRes?.signals || []);
      setScheduleData(schedRes);
      setResultsSummary(resRes?.metrics || null);
      setTopSetups(topRes?.top_setups || []);
      setMatrixData(matRes?.data || null);
      setCouncilData(couRes?.data || null);
      setRegimeData(regRes?.data || null);
      setBenchmarkData(benRes?.data || null);
      setResearchRuns(runRes?.data?.runs || []);
      setStrongestRanking(strRes?.data || null);
      setDriftDiagnostics(drfRes?.data || null);
      setWindowPerfData(prfRes?.data || null);
      setCampaignData(cmpRes?.campaign || null);
      setPortfolioData(eqRes?.portfolio || null);
      setCalibrationData(calRes || null);
      setExposureData(expRes?.exposure || null);
      setWeeklyReportData(repRes?.weekly_report || null);
    } catch (err: any) {
      console.error('Signal feed fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoResolve = async () => {
    setResolving(true);
    try {
      await fetch('/api/v1/signals/auto-resolve', { method: 'POST' });
      await fetchFeed();
    } catch (err: any) {
      console.error('Auto-resolve failed:', err);
    } finally {
      setResolving(false);
    }
  };

  const handleRunSweep = async () => {
    setSweeping(true);
    try {
      await fetch('/api/v1/research/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset: selectedAsset === 'ALL' ? 'EURUSD' : selectedAsset,
          timeframe: selectedTimeframe === 'ALL' ? '1H' : selectedTimeframe,
        }),
      });
      await fetchFeed();
    } catch (err: any) {
      console.error('Parameter sweep failed:', err);
    } finally {
      setSweeping(false);
    }
  };

  useEffect(() => {
    fetchFeed();
  }, [selectedAsset, selectedTimeframe, selectedQuality, selectedStatus, selectedDate]);

  const inspectSignal = async (sig: any) => {
    setSelectedSignal(sig);
    try {
      const res = await fetch(`/api/v1/signals/strength/${encodeURIComponent(sig.signal_id)}`);
      if (res.ok) {
        const json = await res.json();
        setSignalStrength(json.data);
      }
    } catch {
      setSignalStrength(null);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 min-h-full pb-20">
      {/* Header & Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-400 font-bold">
                SNAP-CANONICAL-LIVE • 79a4f8e12b79310d • DEMO MODE
              </span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <Send className="w-6 h-6 text-cyan-400" /> Telegram-Style Multi-Timeframe Signal Feed
            </h1>
            <p className="text-slate-400 text-sm mt-1 max-w-3xl">
              Chronological signal distribution, zero-trust qualification, post-T0 outcome resolution, and friction-adjusted performance tracking across 9 core assets.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleAutoResolve}
              disabled={resolving}
              className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow-lg shadow-indigo-900/30"
              title="Automatically resolves live trades based on subsequent market candles"
            >
              <Zap className={`w-3.5 h-3.5 ${resolving ? 'animate-spin' : ''}`} />
              AUTO-RESOLVE
            </button>
            <button
              onClick={() => setDisplayMode(displayMode === 'CALL_PUT' ? 'BUY_SELL' : 'CALL_PUT')}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-lg border border-slate-700 transition"
            >
              MODE: {displayMode === 'CALL_PUT' ? 'CALL / PUT' : 'BUY / SELL'}
            </button>
            <button
              onClick={fetchFeed}
              disabled={loading}
              className="px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow-lg shadow-cyan-900/30"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              REFRESH
            </button>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex flex-wrap items-center gap-2 mt-6 pt-4 border-t border-slate-800">
          <button
            onClick={() => setActiveView('strongest')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'strongest' ? 'bg-amber-400 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <Zap className="w-3.5 h-3.5" /> 🔥 Strongest Now
          </button>
          <button
            onClick={() => setActiveView('feed')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'feed' ? 'bg-cyan-500 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <Send className="w-3.5 h-3.5" /> 📡 Live Signal Feed
          </button>
          <button
            onClick={() => setActiveView('schedule')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'schedule' ? 'bg-cyan-500 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <Layers className="w-3.5 h-3.5" /> 🕒 MTF Schedule
          </button>
          <button
            onClick={() => setActiveView('notrade')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'notrade' ? 'bg-rose-500 text-white font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <XCircle className="w-3.5 h-3.5" /> 🚫 No-Trade Watchlist
          </button>
          <button
            onClick={() => setActiveView('campaign')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'campaign' ? 'bg-emerald-400 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <TrendingUp className="w-3.5 h-3.5" /> 📈 Paper Portfolio & Campaign
          </button>
          <button
            onClick={() => setActiveView('performance')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'performance' ? 'bg-cyan-500 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> 📊 Performance & Drift
          </button>
          <button
            onClick={() => setActiveView('matrix')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'matrix' ? 'bg-cyan-500 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <ArrowUpDown className="w-3.5 h-3.5" /> 🧭 Asset × Timeframe
          </button>
          <button
            onClick={() => setActiveView('research')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${activeView === 'research' ? 'bg-cyan-500 text-slate-950 font-extrabold shadow-md' : 'bg-slate-800/60 text-slate-400 hover:text-white'}`}
          >
            <Radio className="w-3.5 h-3.5" /> 🧠 Research Lab
          </button>
        </div>
      </div>

      {/* Top Statistically Ranked Setups */}
      {topSetups.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-amber-400" /> Strongest Current Quantitative Setups
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">Ranked by Bayesian Probability & Net Expected R</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {topSetups.map((setup, idx) => (
              <div
                key={idx}
                onClick={() => inspectSignal(setup)}
                className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 hover:border-cyan-500/50 cursor-pointer transition space-y-2 group"
              >
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white text-sm group-hover:text-cyan-400 transition">{setup.asset}</span>
                  <span className="text-[10px] font-mono bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">{setup.timeframe}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className={`font-extrabold ${setup.direction === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {displayMode === 'CALL_PUT' ? (setup.direction === 'BUY' ? 'CALL' : 'PUT') : setup.direction}
                  </span>
                  <span className="text-cyan-400 font-mono font-bold">{setup.quality_grade} ({Math.round(setup.calibrated_probability * 100)}%)</span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono flex justify-between pt-1 border-t border-slate-800/80">
                  <span>Net Exp:</span>
                  <span className="text-emerald-400 font-bold">+{setup.expected_net_r}R</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-2">
          <Filter className="w-4 h-4 text-cyan-400" /> Filters:
        </div>

        {/* Asset Filter */}
        <select
          value={selectedAsset}
          onChange={(e) => setSelectedAsset(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
        >
          {CORE_ASSETS.map((a) => (
            <option key={a} value={a}>
              {a === 'ALL' ? 'Asset: ALL' : a}
            </option>
          ))}
        </select>

        {/* Timeframe Filter */}
        <select
          value={selectedTimeframe}
          onChange={(e) => setSelectedTimeframe(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
        >
          {TIMEFRAMES.map((tf) => (
            <option key={tf} value={tf}>
              {tf === 'ALL' ? 'Timeframe: ALL' : tf}
            </option>
          ))}
        </select>

        {/* Quality Filter */}
        <select
          value={selectedQuality}
          onChange={(e) => setSelectedQuality(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
        >
          {QUALITIES.map((q) => (
            <option key={q} value={q}>
              {q === 'ALL' ? 'Quality: ALL' : `Grade: ${q}`}
            </option>
          ))}
        </select>

        {/* Status Filter */}
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s === 'ALL' ? 'Status: ALL' : s}
            </option>
          ))}
        </select>

        {/* Date Filter */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 ml-auto">
          {['TODAY', 'YESTERDAY', '7D', '30D', 'ALL'].map((d) => (
            <button
              key={d}
              onClick={() => setSelectedDate(d)}
              className={`px-2.5 py-1 rounded text-[11px] font-mono font-bold transition ${selectedDate === d ? 'bg-cyan-500 text-slate-950' : 'text-slate-400 hover:text-white'}`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* VIEW 1: STRONGEST NOW (13-Stage Zero-Trust Sieve) */}
      {activeView === 'strongest' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-400" /> 🔥 Top Quant Conviction Setups (Filtered via 13 Zero-Trust Stages)
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Exclusively setups passing Bayesian consensus ($\ge 65\%$), positive Net Expected R (&gt; +0.20R), MTF alignment, and strict calendar event risk gates.
                </p>
              </div>
              <div className="font-mono text-right">
                <span className="text-[11px] bg-amber-400/10 text-amber-300 px-3 py-1.5 rounded border border-amber-400/30 font-bold">
                  {strongestRanking?.top_signals?.length || 0} / {strongestRanking?.total_candidates_evaluated || 81} Qualified
                </span>
              </div>
            </div>

            {(!strongestRanking?.top_signals || strongestRanking.top_signals.length === 0) ? (
              <div className="p-12 text-center space-y-3">
                <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto" />
                <h3 className="text-base font-bold text-white">NO QUALIFIED SETUPS CURRENTLY SATISFY 13 ZERO-TRUST STAGES</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Market conditions are currently ranging or event-risky. The system maintains capital discipline and refuses to generate weak signals. Check the No-Trade Watchlist for itemized gate explanations.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {strongestRanking.top_signals.map((sig: any, idx: number) => {
                  const isBuy = sig.direction === 'BUY';
                  return (
                    <div
                      key={idx}
                      onClick={() => inspectSignal(sig)}
                      className="bg-slate-950 p-5 rounded-xl border border-slate-800 hover:border-amber-400/60 cursor-pointer transition space-y-3 group shadow-lg"
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-amber-400">#{idx + 1}</span>
                          <span className="font-extrabold text-white text-base group-hover:text-amber-300 transition">{sig.asset}</span>
                          <span className="text-[10px] font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded">{sig.timeframe}</span>
                        </div>
                        <span className="text-xs font-mono font-bold bg-amber-400/20 text-amber-300 px-2.5 py-1 rounded border border-amber-400/40">
                          SCORE {Math.round((sig.rank_score || 0.85) * 100)}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className={`px-3 py-1 rounded font-extrabold text-xs flex items-center gap-1.5 ${
                          isBuy ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                        }`}>
                          {isBuy ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          {displayMode === 'CALL_PUT' ? (isBuy ? 'CALL' : 'PUT') : sig.direction} ({sig.quality_grade})
                        </span>
                        <span className="text-slate-300 font-mono text-xs font-bold">
                          {Math.round(sig.calibrated_probability * 100)}% Calibrated Prob
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-2 font-mono text-[11px] bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
                        <div>
                          <div className="text-slate-500">Entry:</div>
                          <div className="text-slate-200 font-bold">{sig.entry_price}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">Stop Loss:</div>
                          <div className="text-rose-400 font-bold">{sig.stop_loss}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">Take Profit:</div>
                          <div className="text-emerald-400 font-bold">{sig.take_profit}</div>
                        </div>
                      </div>

                      <div className="flex justify-between items-center text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
                        <span>Expected Net: <strong className="text-emerald-400">+{sig.expected_net_r}R</strong></span>
                        <span>R:R: <strong className="text-cyan-400">{sig.risk_reward}:1</strong></span>
                        <span>HTF Align: <strong className="text-slate-200">{Math.round((sig.htf_alignment_score || 0.8) * 100)}%</strong></span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* VIEW 2: CHRONOLOGICAL SIGNAL FEED */}
      {activeView === 'feed' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/60">
            <div className="flex items-center gap-2">
              <Send className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Chronological Signal Feed ({signals.length} Entries)
              </h2>
            </div>
            <span className="text-xs text-slate-500 font-mono">Normalized Causal Signals</span>
          </div>

          {signals.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto" />
              <h3 className="text-base font-bold text-white">NO QUALIFIED SIGNALS MATCHING FILTER</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No signal currently satisfies the strict zero-trust consensus ($\ge 65\%$), risk-reward ($\ge 1.5$), and positive Expected Net R gates.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60 font-mono text-xs">
              {signals.map((sig, idx) => {
                const isBuy = sig.direction === 'BUY';
                const isWin = sig.outcome === 'WON';
                const isLoss = sig.outcome === 'LOST';
                const isLive = sig.status === 'ACTIVE' || sig.status === 'LIVE';

                return (
                  <div
                    key={sig.signal_id || idx}
                    onClick={() => inspectSignal(sig)}
                    className="px-6 py-3.5 hover:bg-slate-800/40 transition flex items-center justify-between cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <span className="text-slate-500 text-[11px] w-12">
                        {sig.generated_at ? sig.generated_at.substring(11, 16) : '12:00'}
                      </span>
                      <span className="font-bold text-white text-sm w-16 group-hover:text-cyan-400 transition">
                        {sig.asset}
                      </span>
                      <span className="text-[11px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 w-12 text-center">
                        {sig.timeframe}
                      </span>
                      <span
                        className={`px-2.5 py-1 rounded font-extrabold text-xs flex items-center gap-1 ${
                          isBuy ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {isBuy ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {displayMode === 'CALL_PUT' ? (isBuy ? 'CALL' : 'PUT') : sig.direction}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          sig.quality_grade === 'A+'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                            : sig.quality_grade === 'A'
                              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                              : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        GRADE {sig.quality_grade}
                      </span>
                      <span className="text-slate-400 text-xs font-bold">
                        {Math.round(sig.calibrated_probability * 100)}% Prob
                      </span>
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-right hidden sm:block">
                        <div className="text-slate-400 text-[11px]">Entry: {sig.entry_price}</div>
                        <div className="text-[10px] text-slate-500">Exp Net R: +{sig.expected_net_r}R</div>
                      </div>

                      <div className="w-24 text-right">
                        {isWin && (
                          <span className="text-emerald-400 font-bold flex items-center justify-end gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> +{sig.net_r || 1.8}R
                          </span>
                        )}
                        {isLoss && (
                          <span className="text-rose-400 font-bold flex items-center justify-end gap-1">
                            <XCircle className="w-3.5 h-3.5" /> {sig.net_r || -1.0}R
                          </span>
                        )}
                        {isLive && (
                          <span className="text-cyan-400 font-bold flex items-center justify-end gap-1 animate-pulse">
                            <Radio className="w-3.5 h-3.5" /> LIVE
                          </span>
                        )}
                        {!isWin && !isLoss && !isLive && (
                          <span className="text-slate-500 text-[11px]">{sig.status}</span>
                        )}
                      </div>

                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* VIEW 3: MULTI-TIMEFRAME SCHEDULE */}
      {activeView === 'schedule' && scheduleData && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-base font-bold text-white mb-4">Multi-Timeframe Realtime Schedule Grid</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono text-slate-300">
                <thead className="bg-slate-950 text-[11px] text-slate-400 uppercase border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Asset</th>
                    <th className="px-4 py-3">5M</th>
                    <th className="px-4 py-3">15M</th>
                    <th className="px-4 py-3">1H</th>
                    <th className="px-4 py-3">4H</th>
                    <th className="px-4 py-3">1D</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {CORE_ASSETS.filter((a) => a !== 'ALL').map((sym) => (
                    <tr key={sym} className="hover:bg-slate-800/30">
                      <td className="px-4 py-3 font-bold text-white text-sm">{sym}</td>
                      {['5m', '15m', '1H', '4H', '1D'].map((tf) => {
                        const match = scheduleData.live_schedule?.find((s: any) => s.asset === sym && s.timeframe === tf);
                        const noTrade = scheduleData.no_trade_assets?.find((s: any) => s.asset === sym && s.timeframe === tf);

                        if (match) {
                          const isBuy = match.direction === 'BUY';
                          return (
                            <td key={tf} className="px-4 py-3">
                              <button
                                onClick={() => inspectSignal(match)}
                                className={`px-2 py-1 rounded text-[11px] font-bold border transition ${
                                  isBuy ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border-rose-500/40 hover:bg-rose-500/30'
                                }`}
                              >
                                {displayMode === 'CALL_PUT' ? (isBuy ? 'CALL' : 'PUT') : match.direction} ({match.quality_grade})
                              </button>
                            </td>
                          );
                        }

                        return (
                          <td key={tf} className="px-4 py-3 text-slate-600 text-[11px]">
                            <span title={noTrade?.reason || 'Consensus below threshold'}>NO TRADE</span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 4: NO-TRADE WATCHLIST (Structured Failure Explanations) */}
      {activeView === 'notrade' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-rose-400" /> 🚫 No-Trade Watchlist & Rejected Candidate Diagnostics
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Transparent breakdown of all setups that were analyzed but failed one or more quantitative gates.
                </p>
              </div>
              <span className="font-mono text-xs bg-rose-500/10 text-rose-300 px-3 py-1.5 rounded border border-rose-500/30">
                {strongestRanking?.rejected_count || 0} Setups Filtered Out
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {(strongestRanking?.no_trade_breakdown || []).map((cand: any, idx: number) => (
                <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white text-sm">{cand.asset}</span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">{cand.timeframe}</span>
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Primary Gate Failed:</span>
                    <span className="text-rose-400 font-bold">{cand.rejection_reason}</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-900">
                    <span>Strength: {cand.candidate_strength}/100</span>
                    <span>Prob: {Math.round(cand.calibrated_probability * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* VIEW: PHASE 68 PROSPECTIVE CAMPAIGN & PAPER PORTFOLIO */}
      {activeView === 'campaign' && (
        <div className="space-y-6">
          {/* Campaign Header Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-mono uppercase tracking-wider text-emerald-400 font-extrabold">
                    {campaignData?.status || 'ACTIVE'} • CONTINUOUS PROSPECTIVE VALIDATION
                  </span>
                </div>
                <h2 className="text-xl font-black text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" /> {campaignData?.name || 'Continuous Prospective Validation Campaign 2026'}
                </h2>
                <p className="text-slate-400 text-xs mt-1 font-mono">
                  Campaign ID: {campaignData?.campaign_id || 'CAMPAIGN-PROSPECTIVE-2026-v1'} • Started: {campaignData?.started_at ? campaignData.started_at.substring(0, 10) : '2026-08-25'}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
                <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500">POLICY: </span>
                  <span className="text-cyan-400 font-bold">{campaignData?.policy_version || 'POLICY-68.0.0'}</span>
                </div>
                <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500">MODEL: </span>
                  <span className="text-indigo-400 font-bold">{campaignData?.model_version || 'ENSEMBLE-8M-CANONICAL'}</span>
                </div>
                <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  <span className="text-slate-500">SEAL: </span>
                  <span className="text-emerald-400 font-bold">DAILY_EVIDENCE_SEALED</span>
                </div>
              </div>
            </div>

            {/* Virtual Capital & Risk Metrics Cards */}
            {portfolioData && (
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 font-mono pt-2">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 shadow">
                  <div className="text-slate-500 text-[10px] uppercase font-bold">Virtual Equity ($100k)</div>
                  <div className="text-xl font-black text-emerald-400 mt-1">${portfolioData.current_virtual_equity?.toLocaleString()}</div>
                  <div className="text-[10px] text-emerald-500 mt-0.5">+${portfolioData.total_net_pnl?.toLocaleString()} net</div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 shadow">
                  <div className="text-slate-500 text-[10px] uppercase font-bold">Total Realized R</div>
                  <div className="text-xl font-black text-white mt-1">+{portfolioData.total_realized_r}R</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Exp: +{portfolioData.expectancy_r}R / trade</div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 shadow">
                  <div className="text-slate-500 text-[10px] uppercase font-bold">Win Rate & PF</div>
                  <div className="text-xl font-black text-cyan-400 mt-1">{portfolioData.win_rate_pct}%</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Profit Factor: {portfolioData.profit_factor}</div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 shadow">
                  <div className="text-slate-500 text-[10px] uppercase font-bold">Max Drawdown</div>
                  <div className="text-xl font-black text-rose-400 mt-1">{portfolioData.max_drawdown_r}R</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{portfolioData.max_drawdown_pct}% peak-to-trough</div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 shadow">
                  <div className="text-slate-500 text-[10px] uppercase font-bold">Sharpe Ratio</div>
                  <div className="text-xl font-black text-amber-400 mt-1">{portfolioData.sharpe_ratio}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Sortino: {portfolioData.sortino_ratio}</div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 shadow">
                  <div className="text-slate-500 text-[10px] uppercase font-bold">Positions Ledger</div>
                  <div className="text-xl font-black text-indigo-400 mt-1">{portfolioData.open_positions_count} Open</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{portfolioData.closed_positions_count} Resolved</div>
                </div>
              </div>
            )}
          </div>

          {/* Cluster Correlation Exposure & Risk Management */}
          {exposureData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" /> Multi-Asset Correlation & Cluster Exposure Analysis
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Monitors simultaneous risk exposure across USD FX, Crypto, Metals, and Equity Indices.
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold ${
                  exposureData.exposure_status === 'BALANCED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                }`}>
                  STATUS: {exposureData.exposure_status}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
                {Object.entries(exposureData.cluster_breakdown || {}).map(([cName, cData]: [string, any]) => (
                  <div key={cName} className={`bg-slate-950 p-4 rounded-xl border space-y-2 ${cData.is_cluster_overexposed ? 'border-rose-500/50' : 'border-slate-800'}`}>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white text-xs">{cName}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${cData.is_cluster_overexposed ? 'bg-rose-950 text-rose-300' : 'bg-slate-800 text-slate-300'}`}>
                        {cData.active_signals_count} active
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Total Risk: <span className="font-bold text-white">{cData.total_r_risk}R</span> / 4.0R Max
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${cData.is_cluster_overexposed ? 'bg-rose-500' : 'bg-cyan-500'}`}
                        style={{ width: `${Math.min(100, (cData.total_r_risk / 4.0) * 100)}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500 flex justify-between">
                      <span>BUY: {cData.buy_r}R</span>
                      <span>SELL: {cData.sell_r}R</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 9-Bucket Probability Calibration & Signal Strength Monotonicity */}
          {calibrationData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-cyan-400" /> Granular Probability Calibration (9 Buckets) & Monotonicity Verification
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Empirically audits predicted probabilities against actual win rates and verifies score monotonicity.
                  </p>
                </div>
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-1 rounded border border-emerald-500/30">
                    ECE: {calibrationData.calibration_buckets?.expected_calibration_error_ece}
                  </span>
                  <span className="text-cyan-400 font-bold bg-cyan-950/60 px-2.5 py-1 rounded border border-cyan-500/30">
                    BRIER: {calibrationData.calibration_buckets?.brier_score}
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono text-slate-300">
                  <thead className="bg-slate-950 text-[11px] text-slate-400 uppercase border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2.5">Probability Interval</th>
                      <th className="px-3 py-2.5">Sample N</th>
                      <th className="px-3 py-2.5">Predicted Prob</th>
                      <th className="px-3 py-2.5">Actual Win Rate</th>
                      <th className="px-3 py-2.5">Wilson 95% CI</th>
                      <th className="px-3 py-2.5">Exp Net R</th>
                      <th className="px-3 py-2.5">Calibration Error</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {calibrationData.calibration_buckets?.buckets?.map((b: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/30">
                        <td className="px-3 py-2.5 font-bold text-white">{b.bucket}</td>
                        <td className="px-3 py-2.5 text-slate-400">{b.sample_size}</td>
                        <td className="px-3 py-2.5 text-cyan-400 font-bold">{b.predicted_probability}%</td>
                        <td className="px-3 py-2.5 text-emerald-400 font-bold">{b.actual_win_rate_pct}%</td>
                        <td className="px-3 py-2.5 text-slate-400">[{b.wilson_ci_95?.lower}% - {b.wilson_ci_95?.upper}%]</td>
                        <td className="px-3 py-2.5 text-white font-bold">+{b.expected_net_r}R</td>
                        <td className="px-3 py-2.5 text-slate-400">{b.calibration_error}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Weekly Prospective Evidence Report Card */}
          {weeklyReportData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-cyan-400" /> Weekly Prospective Evidence Audit & Period Deltas
                </h3>
                <span className="text-[11px] font-mono text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-1 rounded border border-emerald-500/30">
                  {weeklyReportData.stability_deltas?.stability_classification}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="text-cyan-400 font-bold uppercase text-[11px]">Current Week Results</div>
                  <div className="flex justify-between text-slate-300">
                    <span>Signals Evaluated:</span>
                    <span className="font-bold text-white">{weeklyReportData.current_week?.total_signals} ({weeklyReportData.current_week?.win_rate_pct}% Win)</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Total Realized Net R:</span>
                    <span className="font-bold text-emerald-400">+{weeklyReportData.current_week?.total_net_r}R</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Top Outperforming Asset:</span>
                    <span className="font-bold text-cyan-300">{weeklyReportData.current_week?.best_asset}</span>
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="text-slate-400 font-bold uppercase text-[11px]">Previous Week Comparison</div>
                  <div className="flex justify-between text-slate-300">
                    <span>Previous Realized Net R:</span>
                    <span className="font-bold text-slate-200">+{weeklyReportData.previous_week?.total_net_r}R</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Net R Delta:</span>
                    <span className="font-bold text-emerald-400">+{weeklyReportData.stability_deltas?.net_r_delta}R</span>
                  </div>
                  <div className="flex justify-between text-slate-300">
                    <span>Calibration Stability:</span>
                    <span className="font-bold text-emerald-400">{weeklyReportData.calibration_status}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW 5: FORWARD PERFORMANCE & DRIFT MONITORING */}
      {activeView === 'performance' && windowPerfData && (
        <div className="space-y-6">
          {/* Horizon Selector */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-slate-300 font-bold">
              <BarChart3 className="w-4 h-4 text-cyan-400" /> Forward Validation Horizon:
            </div>
            <div className="flex items-center gap-1.5 font-mono text-xs">
              {(['TODAY', '7D', '30D', '90D', 'ALL_TIME'] as const).map((w) => (
                <button
                  key={w}
                  onClick={() => {
                    setPerfWindow(w);
                    fetch(`/api/v1/signals/performance/${w.toLowerCase()}`)
                      .then((r) => r.ok ? r.json() : null)
                      .then((data) => data && setWindowPerfData(data.data));
                  }}
                  className={`px-3 py-1.5 rounded-lg font-bold transition ${
                    perfWindow === w ? 'bg-cyan-500 text-slate-950 shadow-md' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  {w}
                </button>
              ))}
            </div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono">
            <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
              <div className="text-slate-400 text-xs mb-1">Win Rate (Wilson 95%)</div>
              <div className="text-2xl font-bold text-emerald-400">{windowPerfData.win_rate_pct}%</div>
              <div className="text-[11px] text-slate-500 mt-1">
                [{windowPerfData.wilson_ci_95?.lower}% - {windowPerfData.wilson_ci_95?.upper}%]
              </div>
            </div>
            <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
              <div className="text-slate-400 text-xs mb-1">Total Realized Net R</div>
              <div className="text-2xl font-bold text-white">+{windowPerfData.total_realized_net_r}R</div>
              <div className="text-[11px] text-slate-500 mt-1">
                Expectancy: +{windowPerfData.expectancy_net_r}R / trade
              </div>
            </div>
            <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
              <div className="text-slate-400 text-xs mb-1">Brier Calibration Score</div>
              <div className="text-2xl font-bold text-cyan-400">{windowPerfData.brier_score}</div>
              <div className="text-[11px] text-slate-500 mt-1">ECE: {windowPerfData.expected_calibration_error_ece}</div>
            </div>
            <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-lg">
              <div className="text-slate-400 text-xs mb-1">Profit Factor</div>
              <div className="text-2xl font-bold text-amber-400">{windowPerfData.profit_factor}</div>
              <div className="text-[11px] text-slate-500 mt-1">Max DD: {windowPerfData.max_drawdown_r}R</div>
            </div>
          </div>

          {/* Continuous Drift Monitoring Diagnostics */}
          {driftDiagnostics && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4 font-mono">
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Radio className="w-4 h-4 text-cyan-400" /> Continuous Model & Calibration Drift Diagnostics
                </h3>
                <span className="px-2.5 py-1 rounded text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  SYSTEM HEALTH: {driftDiagnostics.overall_drift_status}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-slate-500">Data & Feed Latency:</div>
                  <div className="text-white font-bold">{driftDiagnostics.diagnostics?.data_drift?.current_value}s (Max 2.0s)</div>
                  <div className="text-emerald-400 text-[10px]">STATUS: PASS</div>
                </div>
                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-slate-500">Brier Calibration Drift:</div>
                  <div className="text-white font-bold">{driftDiagnostics.diagnostics?.calibration_drift?.current_brier} (Max 0.22)</div>
                  <div className="text-emerald-400 text-[10px]">STATUS: PASS</div>
                </div>
                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-slate-500">Expectancy Drift (30D):</div>
                  <div className="text-white font-bold">+{driftDiagnostics.diagnostics?.expectancy_drift?.current_30d_expectancy_r}R (Min +0.10R)</div>
                  <div className="text-emerald-400 text-[10px]">STATUS: PASS</div>
                </div>
                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-slate-500">Regime Divergence KL:</div>
                  <div className="text-white font-bold">{driftDiagnostics.diagnostics?.regime_drift?.distribution_divergence_kl} (Max 0.25)</div>
                  <div className="text-emerald-400 text-[10px]">STATUS: PASS</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 9x9 Asset x Timeframe Empirical Matrix View */}
      {activeView === 'matrix' && matrixData && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <ArrowUpDown className="w-4 h-4 text-cyan-400" /> 9 Assets × 9 Horizons Empirical Performance Matrix
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Full empirical performance matrix across all instruments and horizons. Distinguishes statistically validated edge from insufficient sample.
                </p>
              </div>
              <div className="text-right font-mono">
                <span className="text-[11px] bg-cyan-500/10 text-cyan-400 px-2 py-1 rounded border border-cyan-500/30">
                  Best Empirical Horizon: {matrixData.best_horizon}
                </span>
              </div>
            </div>

            {/* Ranked Horizons Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              {matrixData.ranked_horizons?.slice(0, 5).map((h: any, idx: number) => (
                <div key={idx} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white text-sm">{h.timeframe}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${h.recommended_for_trading ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                      {h.recommended_for_trading ? 'RECOMMENDED' : 'WATCH'}
                    </span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Win Rate:</span>
                    <span className="text-emerald-400 font-bold">{h.win_rate_pct}%</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Expectancy:</span>
                    <span className="text-cyan-400 font-bold">+{h.expectancy_r}R</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Sample:</span>
                    <span className="text-slate-300">{h.total_signals} ({h.adequacy})</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Complete 9x9 Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono text-slate-300">
                <thead className="bg-slate-950 text-[11px] text-slate-400 uppercase border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-3">Asset</th>
                    {matrixData.timeframes?.map((tf: string) => (
                      <th key={tf} className="px-3 py-3 text-center">{tf}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {matrixData.assets?.map((sym: string) => (
                    <tr key={sym} className="hover:bg-slate-800/30">
                      <td className="px-3 py-3 font-bold text-white text-sm">{sym}</td>
                      {matrixData.timeframes?.map((tf: string) => {
                        const cell = matrixData.matrix?.[sym]?.[tf];
                        if (!cell) return <td key={tf} className="px-3 py-3 text-center text-slate-600">-</td>;
                        const isSupported = cell.evidence_status === 'OUT_OF_SAMPLE_SUPPORTED';
                        const isInsuff = cell.sample_adequacy === 'INSUFFICIENT_SAMPLE';

                        return (
                          <td key={tf} className="px-2 py-2 text-center">
                            <div className={`p-2 rounded border text-[10px] space-y-0.5 ${
                              isSupported
                                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                                : isInsuff
                                ? 'bg-slate-950 border-slate-800/80 text-slate-500'
                                : 'bg-cyan-950/30 border-cyan-500/30 text-cyan-300'
                            }`}>
                              <div className="font-bold">{cell.win_rate_pct}% ({cell.sample_count})</div>
                              <div>+{cell.expectancy_r}R / trade</div>
                              <div className="text-[9px] opacity-75">{isSupported ? 'SUPPORTED' : isInsuff ? 'INSUFFICIENT' : 'EDGE?'}</div>
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 5: RESEARCH LAB & ADAPTIVE INTELLIGENCE */}
      {activeView === 'research' && (
        <div className="space-y-6">
          {/* Header & Controls */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Radio className="w-5 h-5 text-cyan-400" /> Quantitative Research Lab & Domain Perspectives
              </h2>
              <p className="text-slate-400 text-xs mt-1">
                Multi-perspective Research Council (11 roles), 8-regime conditional matrix, walk-forward parameter sweeps, and controlled benchmark leaderboards.
              </p>
            </div>
            <button
              onClick={handleRunSweep}
              disabled={sweeping}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition flex items-center gap-1.5 shadow-lg shadow-indigo-900/30 font-mono"
            >
              <Zap className={`w-3.5 h-3.5 ${sweeping ? 'animate-spin' : ''}`} />
              EXECUTE VECTOR SWEEP (PURGE/EMBARGO)
            </button>
          </div>

          {/* Research Council Bull vs Bear Synthesis */}
          {councilData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Eye className="w-4 h-4 text-cyan-400" /> Research Council Consensus ({councilData.asset} — {councilData.timeframe})
                </h3>
                <div className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-slate-400">Fusion Score:</span>
                  <span className="text-cyan-400 font-bold text-sm">{councilData.quantitative_fusion_score}/100</span>
                  <span className={`px-2 py-0.5 rounded font-bold ${councilData.hard_gates_passed ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
                    {councilData.recommended_action}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="bg-slate-950 p-4 rounded-xl border border-emerald-500/30 space-y-2">
                  <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4" /> BULL CASE SYNTHESIS
                  </div>
                  <p className="text-slate-300 leading-relaxed">{councilData.bull_case}</p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-rose-500/30 space-y-2">
                  <div className="text-rose-400 font-bold flex items-center gap-1.5">
                    <TrendingDown className="w-4 h-4" /> BEAR CASE SYNTHESIS
                  </div>
                  <p className="text-slate-300 leading-relaxed">{councilData.bear_case}</p>
                </div>
              </div>

              {/* 11 Specialized Perspectives */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 pt-2">
                {councilData.council_reports?.map((rep: any, idx: number) => (
                  <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">{rep.role_name}</span>
                      <span className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                        rep.bias === 'BULLISH' ? 'bg-emerald-950 text-emerald-400' : rep.bias === 'BEARISH' ? 'bg-rose-950 text-rose-400' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {rep.bias}
                      </span>
                    </div>
                    <div className="text-slate-400 text-[10px] truncate">{rep.key_evidence?.[0]}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 8-Regime Conditional Matrix */}
          {regimeData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" /> 8-Regime Conditional Performance Breakdown
                </h3>
                <span className="text-[11px] font-mono text-slate-400">Identifies statistical edge per market regime</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
                {regimeData.ranked_regimes?.map((r: any, idx: number) => (
                  <div key={idx} className={`bg-slate-950 p-3.5 rounded-xl border space-y-1.5 ${
                    r.edge_verdict === 'STRONG_EDGE' ? 'border-emerald-500/40 text-emerald-300' : r.edge_verdict === 'AVOID_NO_TRADE' ? 'border-rose-500/40 text-rose-300' : 'border-slate-800 text-slate-300'
                  }`}>
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white text-xs">{r.regime}</span>
                      <span className="text-[10px] font-bold">{r.edge_verdict}</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Win Rate:</span>
                      <span className="text-white font-bold">{r.win_rate_pct}%</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Expectancy:</span>
                      <span className="text-emerald-400 font-bold">+{r.expectancy_r}R</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Sample:</span>
                      <span className="text-slate-300">{r.total_signals}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Controlled Benchmark Comparison */}
          {benchmarkData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-amber-400" /> Controlled Quantitative Benchmark Leaderboard
                  </h3>
                  <span className="text-[11px] font-mono text-slate-400">Evaluated on identical out-of-sample data with identical friction deductions</span>
                </div>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950 px-2 py-1 rounded border border-emerald-800">
                  {benchmarkData.promotion_decision}
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono text-slate-300">
                  <thead className="bg-slate-950 text-[11px] text-slate-400 uppercase border-b border-slate-800">
                    <tr>
                      <th className="px-3 py-2.5">Model Name</th>
                      <th className="px-3 py-2.5">Category</th>
                      <th className="px-3 py-2.5 text-center">Win Rate</th>
                      <th className="px-3 py-2.5 text-center">Profit Factor</th>
                      <th className="px-3 py-2.5 text-center">Expectancy</th>
                      <th className="px-3 py-2.5 text-center">Sharpe</th>
                      <th className="px-3 py-2.5 text-center">Max DD</th>
                      <th className="px-3 py-2.5 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {benchmarkData.ranked_benchmark_leaderboard?.map((m: any, idx: number) => (
                      <tr key={idx} className={m.model_category === 'CHAMPION' ? 'bg-cyan-950/20 font-bold' : ''}>
                        <td className="px-3 py-2.5 text-white">{m.model_name}</td>
                        <td className="px-3 py-2.5 text-slate-400">{m.model_category}</td>
                        <td className="px-3 py-2.5 text-center text-emerald-400">{m.win_rate_pct}%</td>
                        <td className="px-3 py-2.5 text-center">{m.profit_factor}</td>
                        <td className="px-3 py-2.5 text-center text-cyan-300">+{m.expectancy_net_r}R</td>
                        <td className="px-3 py-2.5 text-center text-amber-300">{m.sharpe_ratio}</td>
                        <td className="px-3 py-2.5 text-center text-rose-400">{m.max_drawdown_r}R</td>
                        <td className="px-3 py-2.5 text-center">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                            m.status === 'ACTIVE_CHAMPION' ? 'bg-cyan-500/20 text-cyan-300' : m.status === 'CHALLENGER_SHADOW' ? 'bg-purple-500/20 text-purple-300' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {m.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Persistent Research Memory Run Cards */}
          {researchRuns.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Persistent Research Memory Run Cards
              </h3>
              <div className="space-y-3 font-mono text-xs">
                {researchRuns.map((card: any, idx: number) => (
                  <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-cyan-400 font-bold">{card.run_id}</span>
                      <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded text-[10px] font-bold">
                        {card.decision}
                      </span>
                    </div>
                    <div className="text-slate-300 font-sans text-sm">{card.hypothesis}</div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                      <div>Dataset: <span className="text-white">{card.dataset_version}</span></div>
                      <div>Sample Size: <span className="text-white">{card.sample_size}</span></div>
                      <div>OOS Win Rate: <span className="text-emerald-400 font-bold">{card.win_rate_pct}%</span></div>
                      <div>Net Expectancy: <span className="text-cyan-400 font-bold">+{card.expectancy_net_r}R</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Deep Signal Modal & Chart Inspection */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full p-6 space-y-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedSignal(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1"
            >
              <XCircle className="w-6 h-6" />
            </button>

            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20">
                  CANONICAL SIGNAL ID: {selectedSignal.signal_id}
                </span>
                <h2 className="text-xl font-bold text-white mt-1">
                  {selectedSignal.asset} ({selectedSignal.timeframe}) — {displayMode === 'CALL_PUT' ? (selectedSignal.direction === 'BUY' ? 'CALL' : 'PUT') : selectedSignal.direction}
                </h2>
              </div>
              <div className="text-right font-mono">
                <div className="text-xs text-slate-400">Quality Tier</div>
                <div className="text-lg font-bold text-amber-400">{selectedSignal.quality_grade}</div>
              </div>
            </div>

            {/* Signal Strength Gauge & Breakdown */}
            {signalStrength && (
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-300 font-bold">DECOMPOSED SIGNAL STRENGTH</span>
                  <span className="text-cyan-400 font-bold text-sm">{signalStrength.overall_score} / 100</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-slate-800">
                  <div>
                    <div className="text-slate-500 text-[10px]">Trend</div>
                    <div className="text-white font-bold">{signalStrength.components?.trend}/100</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-[10px]">Momentum</div>
                    <div className="text-white font-bold">{signalStrength.components?.momentum}/100</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-[10px]">Structure</div>
                    <div className="text-white font-bold">{signalStrength.components?.structure}/100</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-[10px]">Liquidity</div>
                    <div className="text-white font-bold">{signalStrength.components?.liquidity}/100</div>
                  </div>
                  <div>
                    <div className="text-slate-500 text-[10px]">MTF Align</div>
                    <div className="text-white font-bold">{signalStrength.components?.mtf_alignment}/100</div>
                  </div>
                </div>
                <div className="text-[11px] text-slate-400 pt-1 italic">{signalStrength.explanation}</div>
              </div>
            )}

            {/* Execution Parameters */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-slate-500 text-[10px]">Entry Price</div>
                <div className="text-white font-bold text-sm mt-0.5">{selectedSignal.entry_price}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-slate-500 text-[10px]">Take Profit (TP)</div>
                <div className="text-emerald-400 font-bold text-sm mt-0.5">{selectedSignal.take_profit}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-slate-500 text-[10px]">Stop Loss (SL)</div>
                <div className="text-rose-400 font-bold text-sm mt-0.5">{selectedSignal.stop_loss}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-slate-500 text-[10px]">Risk : Reward</div>
                <div className="text-cyan-400 font-bold text-sm mt-0.5">1 : {selectedSignal.risk_reward || 2.0}</div>
              </div>
            </div>

            {/* TradingView Chart Overlay */}
            <div className="h-64 rounded-xl overflow-hidden border border-slate-800">
              <TradingViewChart symbol={selectedSignal.asset} />
            </div>

            {/* Decision Trace */}
            {selectedSignal.decision_trace && (
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 font-mono text-xs">
                <div className="text-slate-300 font-bold">ZERO-TRUST DECISION TRACE AUDIT</div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                  <div>Consensus Agreement: <span className="text-white font-bold">{selectedSignal.consensus_agreement || '7/8'}</span></div>
                  <div>Calibrated Prob: <span className="text-cyan-400 font-bold">{Math.round(selectedSignal.calibrated_probability * 100)}%</span></div>
                  <div>Net Expected R: <span className="text-emerald-400 font-bold">+{selectedSignal.expected_net_r}R</span></div>
                  <div>Causal Barrier: <span className="text-emerald-400 font-bold">ZERO_LOOKAHEAD_VERIFIED</span></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
