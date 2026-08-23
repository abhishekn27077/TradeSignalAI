import React, { useEffect, useState } from 'react';
import {
  Zap,
  Search,
  RefreshCw,
  ArrowUpDown,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Flame,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Activity,
  Check,
} from 'lucide-react';
import { api } from '../../services/api-client';
import { SignalDetailPanel } from '../../components/signals/SignalDetailPanel';
import { formatConfidence } from '../../utils/formatters';

const IST_TZ = 'Asia/Kolkata';
const toIST = (ts: any): string => {
  if (!ts) return '—';
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleTimeString('en-IN', { timeZone: IST_TZ, hour12: false });
};

type ViewTab = 'today' | 'yesterday' | 'actionable';
type SortKey = 'time' | 'asset' | 'confidence' | 'direction';

export const TodaysSignals: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ViewTab>('today');
  const [signals, setSignals] = useState<any[]>([]);
  const [yesterdaySignals, setYesterdaySignals] = useState<any[]>([]);
  const [actionableSignals, setActionableSignals] = useState<any[]>([]);
  const [nextSetup, setNextSetup] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [revalidating, setRevalidating] = useState(false);
  const [revalidationMsg, setRevalidationMsg] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [dirFilter, setDirFilter] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');
  const [sortKey, setSortKey] = useState<SortKey>('time');
  const [sortAsc, setSortAsc] = useState(false);
  const [selected, setSelected] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [marketStatuses, setMarketStatuses] = useState<any[]>([]);
  const [todayForecasts, setTodayForecasts] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'SIGNALS' | 'FORECASTS'>('SIGNALS');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [tData, yData, liveToday, nextRes, actRes, mktRes] = await Promise.all([
        api.signals.today().catch(() => null),
        api.signals.yesterday().catch(() => null),
        fetch('/api/v1/live/today').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch('/api/v1/signals/next-setup').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch('/api/v1/signals/actionable?include_expired=true').then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch('/api/v1/market/status').then((r) => (r.ok ? r.json() : null)).catch(() => null),
      ]);

      const tSignals = Array.isArray(tData) ? tData : ((tData as any)?.signals || []);
      setSignals(tSignals);
      setYesterdaySignals(Array.isArray(yData) ? yData : ((yData as any)?.signals || []));

      if (liveToday?.forecasts) {
        setTodayForecasts(liveToday.forecasts);
      }

      if (mktRes?.statuses) {
        setMarketStatuses(mktRes.statuses);
      }

      if (nextRes?.has_setup && nextRes?.next_setup) {
        setNextSetup(nextRes.next_setup);
      } else {
        setNextSetup(null);
      }

      if (actRes?.actionable_opportunities) {
        setActionableSignals(actRes.actionable_opportunities);
      }
    } catch (err: any) {
      setError(err?.message || 'Backend connection offline on http://127.0.0.1:8000');
    } finally {
      setLoading(false);
    }
  };

  const handleRevalidateNow = async () => {
    if (!nextSetup?.signal_id) return;
    setRevalidating(true);
    setRevalidationMsg(null);
    try {
      const res = await fetch(`/api/v1/signals/${encodeURIComponent(nextSetup.signal_id)}/revalidate`, {
        method: 'POST',
      });
      const data = await res.json();
      if (data.success) {
        setRevalidationMsg(`Revalidated: ${data.revalidation_outcome || 'Up to date'}`);
        if (data.updated_signal) {
          setNextSetup(data.updated_signal);
        }
        await loadData();
      } else {
        setRevalidationMsg(`Revalidation failed: ${data.error || 'Unknown error'}`);
      }
    } catch (e: any) {
      setRevalidationMsg(`Error: ${e.message}`);
    } finally {
      setRevalidating(false);
      setTimeout(() => setRevalidationMsg(null), 6000);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const currentDataset =
    activeTab === 'today'
      ? signals
      : activeTab === 'actionable'
      ? actionableSignals
      : activeTab === 'forecasts'
      ? todayForecasts
      : yesterdaySignals;

  // Filter + Sort
  const filtered = currentDataset
    .filter((s: any) => {
      const sym = (s.symbol || s.asset || '').toUpperCase();
      if (search && !sym.includes(search.toUpperCase())) return false;
      const dir = s.direction || s.prediction?.expected_direction || '';
      if (dirFilter !== 'ALL' && dir !== dirFilter) return false;
      return true;
    })
    .sort((a: any, b: any) => {
      let cmp = 0;
      switch (sortKey) {
        case 'time':
          cmp =
            new Date(a.created_at || a.timestamp || a.forecast_generated_at_utc || 0).getTime() -
            new Date(b.created_at || b.timestamp || b.forecast_generated_at_utc || 0).getTime();
          break;
        case 'asset':
          cmp = (a.symbol || a.asset || '').localeCompare(b.symbol || b.asset || '');
          break;
        case 'confidence':
          cmp =
            (a.confidence ?? a.prediction?.confidence ?? 0) -
            (b.confidence ?? b.prediction?.confidence ?? 0);
          break;
        case 'direction':
          cmp = (a.direction || '').localeCompare(b.direction || '');
          break;
      }
      return sortAsc ? cmp : -cmp;
    });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const SortIcon: React.FC<{ col: SortKey }> = ({ col }) => (
    <ArrowUpDown
      className={`w-3 h-3 inline ml-1 ${
        sortKey === col ? 'text-accent-blue' : 'text-text-muted opacity-40'
      }`}
    />
  );

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'ENTER NOW':
        return 'bg-profit/20 text-profit border-profit/40 animate-pulse';
      case 'HOLD':
        return 'bg-accent-gold/20 text-accent-gold border-accent-gold/40';
      case 'WAIT':
        return 'bg-accent-blue/20 text-accent-blue border-accent-blue/40';
      case 'CLOSE':
        return 'bg-warning/20 text-warning border-warning/40';
      case 'EXPIRED':
        return 'bg-text-muted/20 text-text-muted border-text-muted/40';
      default:
        return 'bg-loss/20 text-loss border-loss/40';
    }
  };

  const renderOutcome = (s: any) => {
    const outcome = (s.signal_state || s.outcome || s.status || '').toUpperCase();
    if (outcome === 'TP_HIT') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-profit/15 text-profit">
          <CheckCircle2 className="w-2.5 h-2.5" /> TP HIT{' '}
          {s.net_r !== undefined ? `(+${s.net_r}R)` : ''}
        </span>
      );
    }
    if (outcome === 'SL_HIT') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-loss/15 text-loss">
          <XCircle className="w-2.5 h-2.5" /> SL HIT{' '}
          {s.net_r !== undefined ? `(${s.net_r}R)` : ''}
        </span>
      );
    }
    if (outcome === 'TIME_EXIT') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-accent-blue/15 text-accent-blue">
          <Clock className="w-2.5 h-2.5" /> TIME EXIT
        </span>
      );
    }
    if (outcome === 'AMBIGUOUS') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-warning/15 text-warning">
          <AlertTriangle className="w-2.5 h-2.5" /> AMBIGUOUS
        </span>
      );
    }
    if (outcome === 'ACTIVE' || outcome === 'ENTER_NOW') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-profit/15 text-profit">
          ACTIONABLE
        </span>
      );
    }
    return (
      <span className="text-[10px] font-mono text-text-muted">
        {s.signal_state || s.status || 'UNRESOLVED'}
      </span>
    );
  };

  return (
    <div className="h-full flex flex-col bg-trading-dark">
      {/* ── Top Command Center: Next Actionable Setup ──────────────────────── */}
      {nextSetup && (
        <div className="shrink-0 m-4 p-4 rounded-xl bg-gradient-to-r from-trading-surface via-trading-surface to-trading-elevated border border-panel-border/80 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-panel-border/40">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-accent-gold/10 border border-accent-gold/20 text-accent-gold">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold tracking-wider text-text-muted uppercase">
                    Next Actionable Setup (Phase 50)
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-trading-dark text-accent-blue">
                    v{nextSetup.version || 1}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      nextSetup.data_freshness_status === 'FRESH'
                        ? 'bg-profit/10 text-profit border-profit/30'
                        : 'bg-loss/10 text-loss border-loss/30'
                    }`}
                  >
                    {nextSetup.data_freshness_status || 'FRESH'} DATA
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <h2 className="text-lg font-extrabold text-text-primary tracking-wide">
                    {nextSetup.asset} ({nextSetup.timeframe})
                  </h2>
                  <span
                    className={`text-xs font-black px-2 py-0.5 rounded ${
                      nextSetup.direction === 'BUY'
                        ? 'bg-profit/20 text-profit'
                        : 'bg-loss/20 text-loss'
                    }`}
                  >
                    {nextSetup.direction}
                  </span>
                  <span className="text-xs font-mono text-text-muted">
                    Confidence: {(nextSetup.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Action Badge & Revalidation Button */}
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-[10px] font-mono text-text-muted uppercase">Action Required</div>
                <div
                  className={`text-xs font-black px-3 py-1 rounded-lg border mt-0.5 ${getActionBadgeColor(
                    nextSetup.primary_action || 'WAIT'
                  )}`}
                >
                  {nextSetup.primary_action || 'WAIT'}
                </div>
              </div>

              <button
                onClick={handleRevalidateNow}
                disabled={revalidating}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-accent-blue/15 hover:bg-accent-blue/25 text-accent-blue border border-accent-blue/40 text-xs font-bold transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${revalidating ? 'animate-spin' : ''}`} />
                {revalidating ? 'Revalidating...' : 'Revalidate Now'}
              </button>
            </div>
          </div>

          {revalidationMsg && (
            <div className="mt-2 text-xs font-mono px-3 py-1.5 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
              {revalidationMsg}
            </div>
          )}

          {/* Temporal Envelope Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mt-3 text-xs font-mono">
            <div className="bg-trading-dark/60 p-2 rounded-lg border border-panel-border/30">
              <div className="text-[10px] text-text-muted">TARGET TIME (IST)</div>
              <div className="text-text-primary font-bold text-[11px] truncate">
                {nextSetup.target_time_ist || '—'}
              </div>
            </div>

            <div className="bg-trading-dark/60 p-2 rounded-lg border border-panel-border/30">
              <div className="text-[10px] text-text-muted">ENTRY WINDOW</div>
              <div className="text-accent-blue font-bold text-[11px] truncate">
                {toIST(nextSetup.entry_window_start_utc)} → {toIST(nextSetup.entry_window_end_utc)}
              </div>
            </div>

            <div className="bg-trading-dark/60 p-2 rounded-lg border border-panel-border/30">
              <div className="text-[10px] text-text-muted">PREFERRED ENTRY</div>
              <div className="text-accent-gold font-bold text-[11px] truncate">
                {toIST(nextSetup.preferred_entry_time_utc)}
              </div>
            </div>

            <div className="bg-trading-dark/60 p-2 rounded-lg border border-panel-border/30">
              <div className="text-[10px] text-text-muted">VALID UNTIL</div>
              <div className="text-loss font-bold text-[11px] truncate">
                {toIST(nextSetup.signal_expiry_time_utc)}
              </div>
            </div>

            <div className="bg-trading-dark/60 p-2 rounded-lg border border-panel-border/30">
              <div className="text-[10px] text-text-muted">EXPECTED HOLD</div>
              <div className="text-text-primary font-bold text-[11px]">
                {nextSetup.expected_holding_formatted || '2–4 hours'}
              </div>
            </div>

            <div className="bg-trading-dark/60 p-2 rounded-lg border border-panel-border/30">
              <div className="text-[10px] text-text-muted">MAX HOLD LIMIT</div>
              <div className="text-warning font-bold text-[11px]">
                {nextSetup.maximum_hold_hours ? `${nextSetup.maximum_hold_hours}h` : '6h'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Navigation Header & Filters ────────────────────────────────────── */}
      <div className="shrink-0 px-5 py-3 border-b border-panel-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-gold" />
            <h1 className="text-sm font-bold text-text-primary">
              {activeTab === 'today'
                ? "Today's Qualified Signals"
                : activeTab === 'actionable'
                ? 'Actionable Trade Timing'
                : activeTab === 'forecasts'
                ? "Today's Analytical Forecasts"
                : "Yesterday's Results"}
            </h1>
            <span className="text-[10px] bg-trading-elevated text-text-muted px-2 py-0.5 rounded-full font-mono">
              {filtered.length}
            </span>
          </div>

          {/* Tab Switcher */}
          <div className="flex bg-trading-surface border border-panel-border rounded-lg p-0.5 ml-2">
            <button
              onClick={() => setActiveTab('today')}
              className={`px-3 py-1 text-[11px] font-medium rounded-md transition-colors ${
                activeTab === 'today'
                  ? 'bg-accent-blue/15 text-accent-blue font-semibold'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Qualified Signals ({signals.length})
            </button>
            <button
              onClick={() => setActiveTab('forecasts')}
              className={`px-3 py-1 text-[11px] font-medium rounded-md transition-colors ${
                activeTab === 'forecasts'
                  ? 'bg-purple-500/15 text-purple-400 font-semibold'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Analytical Forecasts ({todayForecasts.length})
            </button>
            <button
              onClick={() => setActiveTab('actionable')}
              className={`px-3 py-1 text-[11px] font-medium rounded-md transition-colors ${
                activeTab === 'actionable'
                  ? 'bg-accent-gold/15 text-accent-gold font-semibold'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Actionable Lifecycle ({actionableSignals.length})
            </button>
            <button
              onClick={() => setActiveTab('yesterday')}
              className={`px-3 py-1 text-[11px] font-medium rounded-md transition-colors ${
                activeTab === 'yesterday'
                  ? 'bg-accent-blue/15 text-accent-blue font-semibold'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Yesterday's Results ({yesterdaySignals.length})
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Direction Filter */}
          <div className="flex bg-trading-surface border border-panel-border rounded-lg overflow-hidden">
            {(['ALL', 'BUY', 'SELL'] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDirFilter(d)}
                className={`px-3 py-1 text-[10px] font-semibold transition-colors ${
                  dirFilter === d
                    ? d === 'BUY'
                      ? 'bg-profit/15 text-profit'
                      : d === 'SELL'
                      ? 'bg-loss/15 text-loss'
                      : 'bg-accent-blue/15 text-accent-blue'
                    : 'text-text-muted hover:text-text-secondary'
                }`}
              >
                {d}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search asset..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-trading-surface border border-panel-border rounded-lg pl-7 pr-3 py-1.5 text-[11px] text-text-primary focus:outline-none focus:border-accent-blue/50 w-36 transition-colors"
            />
          </div>

          <button
            onClick={loadData}
            className="p-1.5 rounded-lg bg-trading-surface border border-panel-border text-text-muted hover:text-text-primary transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ── Table Content ──────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-72 text-text-muted px-4 text-center">
            <Zap className="w-9 h-9 mb-3 opacity-20 text-accent-gold" />
            <p className="text-sm font-semibold text-text-primary">
              {loading
                ? 'Loading signals...'
                : activeTab === 'today'
                ? 'No valid setups generated today.'
                : activeTab === 'actionable'
                ? 'No active actionable trade opportunities found.'
                : 'No signals were generated yesterday.'}
            </p>
            <p className="text-xs text-text-muted max-w-md mt-1.5">
              Zero-Trust Engine actively monitors H4 and Swing timeframes. A signal is only dispatched
              when multi-model consensus, SMC structure, and risk gates align.
            </p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10 bg-trading-surface">
              <tr className="text-[10px] text-text-muted uppercase border-b border-panel-border">
                <th
                  className="text-left px-4 py-2.5 cursor-pointer select-none"
                  onClick={() => toggleSort('time')}
                >
                  Time (IST) <SortIcon col="time" />
                </th>
                <th
                  className="text-left px-4 py-2.5 cursor-pointer select-none"
                  onClick={() => toggleSort('asset')}
                >
                  Asset <SortIcon col="asset" />
                </th>
                <th className="text-left px-4 py-2.5">TF</th>
                <th
                  className="text-left px-4 py-2.5 cursor-pointer select-none"
                  onClick={() => toggleSort('direction')}
                >
                  Direction <SortIcon col="direction" />
                </th>
                <th
                  className="text-right px-4 py-2.5 cursor-pointer select-none"
                  onClick={() => toggleSort('confidence')}
                >
                  Confidence <SortIcon col="confidence" />
                </th>
                <th className="text-right px-4 py-2.5">Entry</th>
                <th className="text-right px-4 py-2.5">Stop Loss</th>
                <th className="text-right px-4 py-2.5">Take Profit</th>
                <th className="text-right px-4 py-2.5">R : R</th>
                <th className="text-left px-4 py-2.5">Action</th>
                <th className="text-left px-4 py-2.5">Decision</th>
                <th className="text-right px-4 py-2.5">Outcome / Net P&L</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s: any, idx: number) => {
                const dir = s.direction || s.prediction?.expected_direction || 'WAIT';
                const isBuy = dir === 'BUY' || dir === 'LONG';
                const conf = s.confidence ?? s.prediction?.confidence ?? 0;
                return (
                  <tr
                    key={s.signal_id || idx}
                    onClick={() => setSelected(s)}
                    className="border-t border-panel-border/30 hover:bg-trading-hover/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-2.5 font-mono text-text-secondary">
                      {toIST(
                        s.created_at ||
                          s.timestamp ||
                          s.forecast_generated_at_utc ||
                          s.prediction_timestamp
                      )}
                    </td>
                    <td className="px-4 py-2.5 font-semibold text-text-primary">
                      {s.symbol || s.asset || '—'}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-text-muted text-[11px]">
                      {s.timeframe || 'H4'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          isBuy ? 'badge-buy' : 'badge-sell'
                        }`}
                      >
                        {dir}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-primary font-medium">
                      {formatConfidence(conf)}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-primary font-medium">
                      {s.entry_price ?? s.current_price ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-loss">
                      {s.stop_loss ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-profit">
                      {s.take_profit_1 ?? s.take_profit ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-secondary">
                      {s.risk_reward ? `1:${s.risk_reward}` : '—'}
                    </td>
                    <td className="px-4 py-2.5 font-bold text-[11px]">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${getActionBadgeColor(
                          s.primary_action || 'WAIT'
                        )}`}
                      >
                        {s.primary_action || 'WAIT'}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-accent-blue/15 text-accent-blue">
                        {s.status === 'ACTIVE' || s.status === 'COMPLETED'
                          ? 'APPROVED'
                          : s.status || 'NO_TRADE'}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-medium">{renderOutcome(s)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {selected && <SignalDetailPanel signal={selected} onClose={() => setSelected(null)} />}
    </div>
  );
};
