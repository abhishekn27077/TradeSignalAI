import React, { useEffect, useState } from 'react';
import {
  BookOpen, RefreshCw, CheckCircle2, XCircle, Clock, AlertTriangle,
  TrendingUp, TrendingDown, Minus, Filter, BarChart3,
} from 'lucide-react';

const API_BASE = '/api/v1';

const IST_TZ = 'Asia/Kolkata';
const toIST = (ts: any): string => {
  if (!ts) return '—';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', { timeZone: IST_TZ, hour12: false, month: 'short', day: 'numeric' });
};

const OutcomeBadge: React.FC<{ outcome: string }> = ({ outcome }) => {
  const styles: Record<string, string> = {
    TP_HIT: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    CORRECT: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    SL_HIT: 'bg-red-500/20 text-red-400 border-red-500/30',
    WRONG: 'bg-red-500/20 text-red-400 border-red-500/30',
    TIME_EXIT: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    AMBIGUOUS: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  const icons: Record<string, React.ReactNode> = {
    TP_HIT: <CheckCircle2 className="w-3 h-3" />,
    CORRECT: <CheckCircle2 className="w-3 h-3" />,
    SL_HIT: <XCircle className="w-3 h-3" />,
    WRONG: <XCircle className="w-3 h-3" />,
    TIME_EXIT: <Clock className="w-3 h-3" />,
    AMBIGUOUS: <AlertTriangle className="w-3 h-3" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold ${styles[outcome] || styles.AMBIGUOUS}`}>
      {icons[outcome] || icons.AMBIGUOUS} {outcome}
    </span>
  );
};

export const PredictionLedger: React.FC = () => {
  const [entries, setEntries] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);
  const [assetFilter, setAssetFilter] = useState('ALL');

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/forecasts/ledger?days=${days}`);
      const json = await res.json();
      setEntries(json?.entries || []);
      setPerformance(json?.performance || {});
    } catch { /* offline */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [days]);

  const assets = ['ALL', ...new Set(entries.map(e => e.asset))];
  const filtered = assetFilter === 'ALL' ? entries : entries.filter(e => e.asset === assetFilter);

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4" style={{ background: 'linear-gradient(135deg, #0a0e17 0%, #111827 50%, #0d1321 100%)' }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Prediction Ledger</h1>
            <p className="text-xs text-slate-400">Immutable forecast history with outcomes & P&L</p>
          </div>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-300 hover:bg-slate-700/60 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-6 gap-3">
        {[
          { label: 'Win Rate', value: `${performance.win_rate_pct?.toFixed(1) || 0}%`, color: (performance.win_rate_pct || 0) > 50 ? 'text-emerald-400' : 'text-red-400' },
          { label: 'Profit Factor', value: `${performance.profit_factor?.toFixed(2) || 0}`, color: (performance.profit_factor || 0) > 1 ? 'text-emerald-400' : 'text-red-400' },
          { label: 'Expectancy', value: `${performance.expectancy?.toFixed(5) || 0}`, color: (performance.expectancy || 0) > 0 ? 'text-emerald-400' : 'text-red-400' },
          { label: 'Avg R', value: `${performance.avg_r?.toFixed(2) || 0}R`, color: (performance.avg_r || 0) > 0 ? 'text-emerald-400' : 'text-red-400' },
          { label: 'Dir. Accuracy', value: `${performance.directional_accuracy_pct?.toFixed(1) || 0}%`, color: 'text-blue-400' },
          { label: 'Total', value: `${performance.resolved || 0}/${performance.total_forecasts || 0}`, color: 'text-slate-300' },
        ].map((s, i) => (
          <div key={i} className="bg-slate-900/60 border border-slate-800/50 rounded-lg p-2.5 text-center">
            <div className={`text-base font-bold ${s.color}`}>{s.value}</div>
            <div className="text-[10px] text-slate-500">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          {[3, 7, 14, 30].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-colors ${
                days === d ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-slate-800/40 text-slate-500 hover:text-slate-300 border border-transparent'
              }`}>
              {d}D
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          {assets.map(a => (
            <button key={a} onClick={() => setAssetFilter(a)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                assetFilter === a ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-800/40 text-slate-500 hover:text-slate-300'
              }`}>
              {a}
            </button>
          ))}
        </div>
      </div>

      {/* Ledger Table */}
      {loading && entries.length === 0 ? (
        <div className="flex items-center justify-center py-20 text-slate-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading ledger…
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800/50 rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800/50 text-slate-500">
                <th className="p-2.5 text-left font-medium">Date</th>
                <th className="p-2.5 text-left font-medium">Asset</th>
                <th className="p-2.5 text-center font-medium">Direction</th>
                <th className="p-2.5 text-center font-medium">Confidence</th>
                <th className="p-2.5 text-right font-medium">Entry</th>
                <th className="p-2.5 text-right font-medium">SL</th>
                <th className="p-2.5 text-right font-medium">TP</th>
                <th className="p-2.5 text-right font-medium">R:R</th>
                <th className="p-2.5 text-center font-medium">Outcome</th>
                <th className="p-2.5 text-right font-medium">Exit</th>
                <th className="p-2.5 text-right font-medium">Net P&L</th>
                <th className="p-2.5 text-right font-medium">R-Multiple</th>
                <th className="p-2.5 text-center font-medium">Type</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry: any, idx: number) => (
                <tr key={idx} className="border-b border-slate-800/30 hover:bg-slate-800/20 transition-colors">
                  <td className="p-2.5 text-slate-400 font-mono">{entry.date || '—'}</td>
                  <td className="p-2.5 text-white font-semibold">{entry.asset}</td>
                  <td className="p-2.5 text-center">
                    <span className={`inline-flex items-center gap-0.5 font-semibold ${
                      entry.direction === 'BUY' ? 'text-emerald-400' : entry.direction === 'SELL' ? 'text-red-400' : 'text-slate-400'
                    }`}>
                      {entry.direction === 'BUY' ? <TrendingUp className="w-3 h-3" /> : entry.direction === 'SELL' ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                      {entry.direction}
                    </span>
                  </td>
                  <td className="p-2.5 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${(entry.confidence || 0) >= 0.65 ? 'bg-emerald-400' : 'bg-amber-400'}`}
                          style={{ width: `${(entry.confidence || 0) * 100}%` }} />
                      </div>
                      <span className="text-slate-300 font-mono">{((entry.confidence || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="p-2.5 text-right text-slate-300 font-mono">{entry.entry_price?.toFixed(5) || '—'}</td>
                  <td className="p-2.5 text-right text-red-400/70 font-mono">{entry.stop_loss?.toFixed(5) || '—'}</td>
                  <td className="p-2.5 text-right text-emerald-400/70 font-mono">{entry.take_profit?.toFixed(5) || '—'}</td>
                  <td className="p-2.5 text-right text-slate-300 font-mono">{entry.risk_reward?.toFixed(1) || '—'}</td>
                  <td className="p-2.5 text-center"><OutcomeBadge outcome={entry.outcome || 'AMBIGUOUS'} /></td>
                  <td className="p-2.5 text-right text-slate-300 font-mono">{entry.exit_price?.toFixed(5) || '—'}</td>
                  <td className={`p-2.5 text-right font-mono font-bold ${(entry.net_pnl || 0) > 0 ? 'text-emerald-400' : (entry.net_pnl || 0) < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                    {entry.net_pnl != null ? entry.net_pnl.toFixed(5) : '—'}
                  </td>
                  <td className={`p-2.5 text-right font-mono font-bold ${(entry.r_multiple || 0) > 0 ? 'text-emerald-400' : (entry.r_multiple || 0) < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                    {entry.r_multiple != null ? `${entry.r_multiple.toFixed(2)}R` : '—'}
                  </td>
                  <td className="p-2.5 text-center">
                    {entry.is_trade_signal ? (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">TRADE</span>
                    ) : (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">FORECAST</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filtered.length === 0 && (
            <div className="text-center py-10 text-slate-500">
              <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
              No ledger entries for this period
            </div>
          )}
        </div>
      )}
    </div>
  );
};
