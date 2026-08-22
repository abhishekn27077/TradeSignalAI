import React, { useEffect, useState } from 'react';
import { Archive, RefreshCw, Search, CheckCircle2, XCircle, Clock, AlertTriangle, Filter } from 'lucide-react';
import { api } from '../../services/api-client';
import { SignalDetailPanel } from '../../components/signals/SignalDetailPanel';
import { DateSelector, type DateFilterValue } from '../../components/signals/DateSelector';
import { formatConfidence } from '../../utils/formatters';

const IST_TZ = 'Asia/Kolkata';
const toIST = (ts: any): string => {
  if (!ts) return '—';
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', { timeZone: IST_TZ, hour12: false });
};

export const SignalHistory: React.FC = () => {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dateFilter, setDateFilter] = useState<DateFilterValue>({ preset: 'all' });
  const [ablationMode, setAblationMode] = useState<string>('ALL');
  const [selected, setSelected] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.signals.historyWithFilter({
        time_range: dateFilter.preset !== 'custom' && dateFilter.preset !== 'all' ? dateFilter.preset : undefined,
        start_date: dateFilter.preset === 'custom' ? dateFilter.startDate : undefined,
        end_date: dateFilter.preset === 'custom' ? dateFilter.endDate : undefined,
        ablation_mode: ablationMode !== 'ALL' ? ablationMode : undefined,
        limit: 200,
      });
      setSignals(data || []);
    } catch {
      /* offline */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [dateFilter, ablationMode]);

  const filtered = signals.filter((s) => {
    if (!search) return true;
    const sym = (s.symbol || s.asset || '').toUpperCase();
    return sym.includes(search.toUpperCase());
  });

  const renderOutcome = (s: any) => {
    const outcome = (s.signal_state || s.outcome || s.status || '').toUpperCase();
    if (outcome === 'TP_HIT') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-profit/15 text-profit">
          <CheckCircle2 className="w-2.5 h-2.5" /> TP HIT
        </span>
      );
    }
    if (outcome === 'SL_HIT') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-loss/15 text-loss">
          <XCircle className="w-2.5 h-2.5" /> SL HIT
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
    if (outcome === 'ACTIVE') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-accent-gold/15 text-accent-gold">
          ACTIVE
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
      {/* Header */}
      <div className="shrink-0 px-5 py-4 border-b border-panel-border flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Archive className="w-4 h-4 text-text-secondary" />
            <h1 className="text-sm font-bold text-text-primary">Signal History & Outcome Ledger</h1>
            <span className="text-[10px] bg-trading-elevated text-text-muted px-2 py-0.5 rounded-full font-mono">
              {filtered.length}
            </span>
          </div>

          {/* Date Selector */}
          <DateSelector value={dateFilter} onChange={setDateFilter} />
        </div>

        <div className="flex items-center gap-2">
          {/* Ablation Mode Filter */}
          <div className="flex items-center gap-1 bg-trading-surface border border-panel-border rounded-lg px-2 py-1">
            <Filter className="w-3 h-3 text-text-muted" />
            <select
              value={ablationMode}
              onChange={(e) => setAblationMode(e.target.value)}
              className="bg-transparent text-[11px] text-text-primary focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-trading-dark">All Ablation Modes</option>
              <option value="MODE_A" className="bg-trading-dark">Mode A (Quant Only)</option>
              <option value="MODE_B" className="bg-trading-dark">Mode B (Ensemble)</option>
              <option value="MODE_C" className="bg-trading-dark">Mode C (Multi-Model + Risk)</option>
            </select>
          </div>

          {/* Search Asset */}
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-trading-surface border border-panel-border rounded-lg pl-7 pr-3 py-1.5 text-[11px] text-text-primary focus:outline-none focus:border-accent-blue/50 w-32 transition-colors"
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

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-72 text-text-muted px-4 text-center">
            <Archive className="w-9 h-9 mb-3 opacity-20 text-text-secondary" />
            <p className="text-sm font-semibold text-text-primary">
              {loading ? 'Loading historical signals...' : 'No historical signals found for selected filters.'}
            </p>
            <p className="text-xs text-text-muted max-w-md mt-1.5">
              Historical records are permanently preserved with complete mathematical trace and execution costs.
            </p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10 bg-trading-surface">
              <tr className="text-[10px] text-text-muted uppercase border-b border-panel-border">
                <th className="text-left px-4 py-2.5">Time (IST)</th>
                <th className="text-left px-4 py-2.5">Asset</th>
                <th className="text-left px-4 py-2.5">TF</th>
                <th className="text-left px-4 py-2.5">Direction</th>
                <th className="text-right px-4 py-2.5">Confidence</th>
                <th className="text-right px-4 py-2.5">Entry</th>
                <th className="text-right px-4 py-2.5">Stop Loss</th>
                <th className="text-right px-4 py-2.5">Take Profit</th>
                <th className="text-right px-4 py-2.5">R : R</th>
                <th className="text-left px-4 py-2.5">Outcome</th>
                <th className="text-right px-4 py-2.5">Exit Price</th>
                <th className="text-right px-4 py-2.5">Net P&L</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const dir = s.direction || s.prediction?.expected_direction || 'WAIT';
                const buy = dir === 'BUY' || dir === 'LONG';
                return (
                  <tr
                    key={s.signal_id || i}
                    onClick={() => setSelected(s)}
                    className="border-t border-panel-border/30 hover:bg-trading-hover/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-2.5 font-mono text-text-secondary">
                      {toIST(s.created_at || s.timestamp || s.prediction_timestamp)}
                    </td>
                    <td className="px-4 py-2.5 font-semibold text-text-primary">{s.symbol || s.asset || '—'}</td>
                    <td className="px-4 py-2.5 font-mono text-text-muted text-[11px]">{s.timeframe || 'H4'}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${buy ? 'badge-buy' : 'badge-sell'}`}>
                        {dir}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-primary font-medium">
                      {formatConfidence(s.confidence ?? s.prediction?.confidence)}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-primary">
                      {s.entry_price ?? s.current_price ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-loss">{s.stop_loss ?? '—'}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-profit">
                      {s.take_profit_1 ?? s.take_profit ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-secondary">
                      {s.risk_reward ? `1:${s.risk_reward}` : '—'}
                    </td>
                    <td className="px-4 py-2.5">{renderOutcome(s)}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-primary">
                      {s.exit_price ?? '—'}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono font-semibold">
                      {s.net_pnl !== null && s.net_pnl !== undefined ? (
                        <span className={s.net_pnl >= 0 ? 'text-profit' : 'text-loss'}>
                          {s.net_pnl >= 0 ? '+' : ''}
                          {s.net_pnl.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-text-muted">—</span>
                      )}
                    </td>
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
