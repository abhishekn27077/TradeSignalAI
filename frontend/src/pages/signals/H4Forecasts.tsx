import React, { useEffect, useState } from 'react';
import { Clock, RefreshCw, Search, ShieldAlert, Cpu, Activity, BarChart2 } from 'lucide-react';
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

export const H4ForecastsPage: React.FC = () => {
  const [forecasts, setForecasts] = useState<any[]>([]);
  const [intelData, setIntelData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch H4 multi-model intelligence scan matrix & canonical validated signals
      const intel = await api.signals.h4Intelligence();
      if (intel && intel.success) {
        setIntelData(intel);
        setForecasts(intel.validated_signals || []);
      } else {
        // Fallback to active canonical signals
        const live = await api.signals.live();
        const h4 = (live || []).filter((ls: any) => {
          const s = ls.signal || ls || ({} as any);
          const tf = (s.timeframe || s.signal_timeframe || '').toUpperCase();
          const holdH = ls.prediction?.expected_holding_hours ?? s.expected_hold_hours ?? 0;
          return tf === '4H' || tf === 'H4' || (holdH >= 3 && holdH <= 6);
        });
        setForecasts(h4);
      }
    } catch (err: any) {
      setError(err?.message || 'Backend connection offline on http://127.0.0.1:8000');
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const matrix = (intelData?.matrix || []).filter((m: any) => {
    if (!search) return true;
    return m.asset.toUpperCase().includes(search.toUpperCase());
  });

  const nextEvaluation = intelData?.candle_boundary?.current_candle_close_ist || intelData?.next_evaluation || '—';

  return (
    <div className="h-full flex flex-col bg-trading-dark overflow-y-auto">
      {/* Header */}
      <div className="shrink-0 px-5 py-4 border-b border-panel-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-accent-cyan" />
          <h1 className="text-sm font-bold text-text-primary">H4 Forecasts & Multi-Model Intelligence</h1>
          <span className="text-[10px] bg-trading-elevated text-text-muted px-2 py-0.5 rounded-full font-mono">
            {forecasts.length} Actionable / {intelData?.assets_scanned ?? 9} Monitored
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="text" placeholder="Search asset..." value={search} onChange={e => setSearch(e.target.value)}
              className="bg-trading-surface border border-panel-border rounded-lg pl-7 pr-3 py-1.5 text-[11px] text-text-primary focus:outline-none focus:border-accent-blue/50 w-36 transition-colors" />
          </div>
          <button onClick={load} className="p-1.5 rounded-lg bg-trading-surface border border-panel-border text-text-muted hover:text-text-primary transition-colors">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Observability Status Banner */}
      <div className="px-5 py-3 bg-trading-surface/60 border-b border-panel-border/50 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Assets Scanned:</span>
            <span className="font-bold text-text-primary font-mono">{intelData?.assets_scanned ?? 9}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Valid Setups:</span>
            <span className="font-bold text-accent-cyan font-mono">{forecasts.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-text-muted">Next H4 Evaluation:</span>
            <span className="font-bold text-accent-gold font-mono">{nextEvaluation}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-text-muted font-mono">
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse"></span>
          <span>Consensus & Risk Engine Active</span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-5 space-y-6">
        
        {/* 1. Actionable H4 Signals (If Any) */}
        {forecasts.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-accent-emerald" /> Actionable Setups ({forecasts.length})
            </h2>
            <div className="overflow-x-auto border border-panel-border rounded-lg bg-trading-surface">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[10px] text-text-muted uppercase border-b border-panel-border bg-trading-elevated">
                    <th className="text-left px-4 py-2.5">Asset</th>
                    <th className="text-left px-4 py-2.5">Direction</th>
                    <th className="text-right px-4 py-2.5">Confidence</th>
                    <th className="text-left px-4 py-2.5">Entry Time</th>
                    <th className="text-right px-4 py-2.5">Hold Time</th>
                    <th className="text-right px-4 py-2.5">Target</th>
                    <th className="text-right px-4 py-2.5">Stop</th>
                    <th className="text-left px-4 py-2.5">Strategy</th>
                    <th className="text-right px-4 py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {forecasts.map((ls, i) => {
                    const s = ls.signal || ls || ({} as any);
                    const p = ls.prediction || ({} as any);
                    const dir = s.direction || p.expected_direction || 'WAIT';
                    const buy = dir === 'BUY' || dir === 'LONG';
                    const confVal = s.confidence ?? p.confidence ?? (s.consensus_pct ? s.consensus_pct / 100 : 0);
                    const tpVal = s.take_profit ?? s.take_profit_1 ?? s.target ?? p.expected_price_range?.[1] ?? '—';
                    const slVal = s.stop_loss ?? p.expected_price_range?.[0] ?? '—';
                    const stratVal = s.strategy_name ?? s.winning_strategy ?? s.strategy ?? 'Consensus Ensemble';
                    const statusVal = s.status ?? 'ACTIVE';

                    return (
                      <tr key={s.signal_id || i} onClick={() => setSelected(s)}
                        className="border-t border-panel-border/30 hover:bg-trading-hover/50 transition-colors cursor-pointer">
                        <td className="px-4 py-2.5 font-semibold text-text-primary">{s.symbol || s.asset || '—'}</td>
                        <td className="px-4 py-2.5">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${buy ? 'badge-buy' : 'badge-sell'}`}>{dir}</span>
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-text-primary">{formatConfidence(confVal)}</td>
                        <td className="px-4 py-2.5 font-mono text-text-secondary">{toIST(s.timestamp || s.created_at)}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-text-secondary">{s.expected_hold_hours ? `${s.expected_hold_hours}h` : (p.expected_holding_hours ? `${p.expected_holding_hours}h` : '4h')}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-profit">{typeof tpVal === 'number' ? tpVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : tpVal}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-loss">{typeof slVal === 'number' ? slVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : slVal}</td>
                        <td className="px-4 py-2.5 text-text-secondary">{stratVal}</td>
                        <td className="px-4 py-2.5 text-right">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-trading-elevated text-accent-emerald">{statusVal}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 2. When 0 Actionable Signals: Honest Diagnostic Message */}
        {forecasts.length === 0 && (
          <div className="p-4 rounded-lg border border-panel-border/70 bg-trading-surface/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 text-accent-gold" />
              <div>
                <p className="text-xs font-bold text-text-primary">No valid H4 setups currently meet the trading criteria.</p>
                <p className="text-[11px] text-text-muted">Market conditions are neutral/consolidating. All models are actively evaluated below under strict Zero-Trust rules.</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-text-muted uppercase">Next Evaluation</span>
              <p className="text-xs font-mono font-bold text-text-primary">{nextEvaluation}</p>
            </div>
          </div>
        )}

        {/* 3. Multi-Model Intelligence Observability Matrix */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-accent-cyan" /> H4 Intelligence Scan Observability Matrix
            </h2>
            <span className="text-[10px] text-text-muted">Multi-model consensus across 9 core assets</span>
          </div>

          <div className="overflow-x-auto border border-panel-border rounded-lg bg-trading-surface shadow-sm">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] text-text-muted uppercase border-b border-panel-border bg-trading-elevated">
                  <th className="text-left px-3 py-2.5">Asset</th>
                  <th className="text-right px-3 py-2.5">Price</th>
                  <th className="text-center px-3 py-2.5">Regime</th>
                  <th className="text-center px-3 py-2.5">Quant Baseline</th>
                  <th className="text-center px-3 py-2.5">Kronos Foundation</th>
                  <th className="text-center px-3 py-2.5">FAISS Memory</th>
                  <th className="text-center px-3 py-2.5">Time Pattern</th>
                  <th className="text-center px-3 py-2.5">Consensus</th>
                  <th className="text-center px-3 py-2.5">Risk Decision</th>
                  <th className="text-right px-3 py-2.5">Final State</th>
                </tr>
              </thead>
              <tbody>
                {matrix.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-4 py-8 text-center text-text-muted">
                      {loading ? (
                        'Evaluating multi-model intelligence across markets...'
                      ) : error ? (
                        <div className="text-loss font-mono">
                          <p className="font-bold">FORECAST DATA UNAVAILABLE</p>
                          <p className="text-xs text-text-muted mt-1">{error}</p>
                        </div>
                      ) : (
                        <div className="text-text-muted font-mono">
                          <p className="font-bold">FORECAST DATA UNAVAILABLE</p>
                          <p className="text-xs text-text-muted mt-1">Backend service did not return multi-model scan matrix.</p>
                        </div>
                      )}
                    </td>
                  </tr>
                ) : (
                  matrix.map((row: any, idx: number) => {
                    const isActive = row.final === 'ACTIVE';
                    return (
                      <tr key={idx} className="border-t border-panel-border/30 hover:bg-trading-hover/40 transition-colors">
                        <td className="px-3 py-2 font-bold text-text-primary">{row.asset}</td>
                        <td className="px-3 py-2 text-right font-mono text-text-primary">
                          {typeof row.price === 'number' ? row.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 5 }) : row.price}
                        </td>
                        <td className="px-3 py-2 text-center font-mono text-[11px] text-text-secondary">{row.regime}</td>
                        <td className="px-3 py-2 text-center font-mono text-[11px] text-text-primary">{row.quant}</td>
                        <td className="px-3 py-2 text-center font-mono text-[11px] text-accent-cyan">{row.kronos}</td>
                        <td className="px-3 py-2 text-center font-mono text-[11px]">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${row.faiss === 'VALID' ? 'bg-accent-emerald/10 text-accent-emerald' : 'bg-trading-elevated text-text-muted'}`}>
                            {row.faiss}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-center font-mono text-[10px] text-text-muted">{row.time_pattern}</td>
                        <td className="px-3 py-2 text-center font-mono text-[11px]">
                          <span className={`font-bold ${row.consensus === 'BUY' ? 'text-profit' : row.consensus === 'SELL' ? 'text-loss' : 'text-text-muted'}`}>
                            {row.consensus}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-center font-mono text-[11px]">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] ${row.risk === 'TAKE_NOW' ? 'bg-profit/10 text-profit font-bold' : 'bg-trading-elevated text-text-muted'}`}>
                            {row.risk} ({row.risk_reason})
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-[11px]">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${isActive ? 'bg-profit text-white' : 'bg-trading-elevated text-text-muted'}`}>
                            {row.final}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {selected && <SignalDetailPanel signal={selected} onClose={() => setSelected(null)} />}
    </div>
  );
};

