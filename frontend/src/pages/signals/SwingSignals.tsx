import React, { useEffect, useState } from 'react';
import { TrendingUp, RefreshCw, Search } from 'lucide-react';
import { api } from '../../services/api-client';
import { SignalDetailPanel } from '../../components/signals/SignalDetailPanel';
import { formatConfidence } from '../../utils/formatters';

const IST_TZ = 'Asia/Kolkata';
const toIST = (ts: any): string => {
  if (!ts) return '—';
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', { timeZone: IST_TZ, hour12: false });
};

export const SwingSignals: React.FC = () => {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      const live = await api.signals.live();
      // Swing = hold time > 24 hours or daily/weekly timeframe
      const swing = (live || []).filter((ls: any) => {
        const s = ls.signal || ls || ({} as any);
        const tf = (s.timeframe || s.signal_timeframe || '').toUpperCase();
        const holdH = ls.prediction?.expected_holding_hours ?? s.expected_hold_hours ?? 0;
        return holdH >= 24 || tf === 'D1' || tf === 'W1' || tf === 'DAILY' || tf === 'WEEKLY' || tf === '1D' || tf === '1W';
      });
      setSignals(swing);
    } catch { /* offline */ }
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 20000);
    return () => clearInterval(interval);
  }, []);

  const filtered = signals.filter(ls => {
    if (!search) return true;
    const s = ls.signal || ls || ({} as any);
    return (s.symbol || s.asset || '').toUpperCase().includes(search.toUpperCase());
  });

  return (
    <div className="h-full flex flex-col bg-trading-dark">
      {/* Header */}
      <div className="shrink-0 px-5 py-4 border-b border-panel-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-accent-emerald" />
          <h1 className="text-sm font-bold text-text-primary">Swing Signals</h1>
          <span className="text-[10px] bg-trading-elevated text-text-muted px-2 py-0.5 rounded-full font-mono">{filtered.length}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)}
              className="bg-trading-surface border border-panel-border rounded-lg pl-7 pr-3 py-1.5 text-[11px] text-text-primary focus:outline-none focus:border-accent-blue/50 w-36 transition-colors" />
          </div>
          <button onClick={load} className="p-1.5 rounded-lg bg-trading-surface border border-panel-border text-text-muted hover:text-text-primary transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-text-muted">
            <TrendingUp className="w-8 h-8 mb-3 opacity-20" />
            <p className="text-xs">{loading ? 'Scanning for swing trades...' : 'No valid swing setups currently meet the trading criteria'}</p>
            <p className="text-[11px] text-text-muted mt-1">Zero-Trust: Daily (1D) and Weekly (1W) macro momentum must exceed 65% consensus</p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="sticky top-0 z-10 bg-trading-surface">
              <tr className="text-[10px] text-text-muted uppercase border-b border-panel-border">
                <th className="text-left px-4 py-2.5">Asset</th>
                <th className="text-left px-4 py-2.5">Direction</th>
                <th className="text-right px-4 py-2.5">Confidence</th>
                <th className="text-left px-4 py-2.5">Entry Time</th>
                <th className="text-right px-4 py-2.5">Hold Time</th>
                <th className="text-left px-4 py-2.5">Expected Exit</th>
                <th className="text-right px-4 py-2.5">Target</th>
                <th className="text-right px-4 py-2.5">Stop</th>
                <th className="text-right px-4 py-2.5">Risk Reward</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((ls, i) => {
                const s = ls.signal || ls || ({} as any);
                const p = ls.prediction || ({} as any);
                const dir = s.direction || p.expected_direction || 'WAIT';
                const buy = dir === 'BUY' || dir === 'LONG';
                const holdH = p.expected_holding_hours ?? s.expected_hold_hours ?? 24;
                const rawTime = s.timestamp || s.created_at;
                const exitTime = holdH && rawTime
                  ? toIST(new Date((typeof rawTime === 'number' ? rawTime : new Date(rawTime).getTime()) + holdH * 3600000))
                  : '—';
                return (
                  <tr key={i} onClick={() => setSelected(ls.signal ? ls : { signal: ls })}
                    className="border-t border-panel-border/30 hover:bg-trading-hover/50 transition-colors cursor-pointer">
                    <td className="px-4 py-2.5 font-semibold text-text-primary">{s.symbol || s.asset || '—'}</td>
                    <td className="px-4 py-2.5">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${buy ? 'badge-buy' : 'badge-sell'}`}>{dir}</span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-primary">{formatConfidence(p.confidence ?? s.confidence)}</td>
                    <td className="px-4 py-2.5 font-mono text-text-secondary">{toIST(rawTime)}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-text-secondary">{holdH ? `${holdH}h` : '—'}</td>
                    <td className="px-4 py-2.5 font-mono text-text-secondary">{exitTime}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-profit">{s.take_profit ?? s.take_profit_1 ?? '—'}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-loss">{s.stop_loss ?? '—'}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-accent-blue">{s.risk_reward ? `1:${typeof s.risk_reward === 'number' ? s.risk_reward.toFixed(2) : s.risk_reward}` : '—'}</td>
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
