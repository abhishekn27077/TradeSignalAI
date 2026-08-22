import React, { useEffect, useState } from 'react';
import {
  Sun, TrendingUp, TrendingDown, Minus, RefreshCw, AlertTriangle,
  Calendar, Shield, ChevronDown, ChevronUp, Zap, Brain, BarChart3,
  Clock, Target, Activity,
} from 'lucide-react';

const API_BASE = '/api/v1';

const IST_TZ = 'Asia/Kolkata';
const toIST = (ts: any): string => {
  if (!ts) return '—';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', { timeZone: IST_TZ, hour12: false, month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

const DirectionBadge: React.FC<{ direction: string; confidence?: number }> = ({ direction, confidence }) => {
  const colors: Record<string, string> = {
    BUY: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    SELL: 'bg-red-500/20 text-red-400 border-red-500/30',
    NEUTRAL: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  const icons: Record<string, React.ReactNode> = {
    BUY: <TrendingUp className="w-3.5 h-3.5" />,
    SELL: <TrendingDown className="w-3.5 h-3.5" />,
    NEUTRAL: <Minus className="w-3.5 h-3.5" />,
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${colors[direction] || colors.NEUTRAL}`}>
      {icons[direction] || icons.NEUTRAL}
      {direction} {confidence != null ? `${(confidence * 100).toFixed(0)}%` : ''}
    </span>
  );
};

const RiskBadge: React.FC<{ level: string }> = ({ level }) => {
  const colors: Record<string, string> = {
    NONE: 'text-slate-500', LOW: 'text-blue-400', MEDIUM: 'text-yellow-400',
    HIGH: 'text-orange-400', EXTREME: 'text-red-400',
  };
  return (
    <span className={`flex items-center gap-1 text-xs font-medium ${colors[level] || colors.NONE}`}>
      <AlertTriangle className="w-3 h-3" /> {level}
    </span>
  );
};

const QualBadge: React.FC<{ qualified: boolean; reason?: string }> = ({ qualified, reason }) => {
  if (qualified) {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold">
      <Zap className="w-3 h-3" /> TRADE SIGNAL
    </span>;
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-700/50 text-slate-400 border border-slate-600/30 text-xs" title={reason || ''}>
      FORECAST ONLY
    </span>
  );
};

export const TomorrowForecast: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      let json = null;
      try {
        const res = await fetch(`${API_BASE}/forecasts/tomorrow`);
        if (res.ok) json = await res.json();
      } catch {}
      if (!json || (!json.forecasts && !json.summary)) {
        const res2 = await fetch(`${API_BASE}/live/tomorrow`);
        if (res2.ok) json = await res2.json();
      }
      if (json) {
        setData(json);
      } else {
        setError('Backend server offline or uninitialized on http://127.0.0.1:8000');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch tomorrow forecasts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const forecasts = data?.forecasts || [];
  const summary = data?.summary || {};

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4" style={{ background: 'linear-gradient(135deg, #0a0e17 0%, #111827 50%, #0d1321 100%)' }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
            <Sun className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Tomorrow's Forecast</h1>
            <p className="text-xs text-slate-400">
              {data?.forecast_for ? `Forecast for ${new Date(data.forecast_for).toLocaleDateString('en-IN', { timeZone: IST_TZ })}` : 'Multi-model AI consensus across 9 assets'}
            </p>
          </div>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-300 hover:bg-slate-700/60 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Summary Bar */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Total Assets', value: summary.total_assets || 0, icon: <Target className="w-4 h-4" />, color: 'text-blue-400' },
          { label: 'Bullish', value: summary.bullish || 0, icon: <TrendingUp className="w-4 h-4" />, color: 'text-emerald-400' },
          { label: 'Bearish', value: summary.bearish || 0, icon: <TrendingDown className="w-4 h-4" />, color: 'text-red-400' },
          { label: 'Neutral', value: summary.neutral || 0, icon: <Minus className="w-4 h-4" />, color: 'text-slate-400' },
          { label: 'Trade Signals', value: summary.trade_signals_qualified || 0, icon: <Zap className="w-4 h-4" />, color: 'text-amber-400' },
        ].map((s, i) => (
          <div key={i} className="bg-slate-900/60 border border-slate-800/50 rounded-lg p-3 text-center">
            <div className={`flex items-center justify-center gap-1.5 ${s.color} text-lg font-bold`}>
              {s.icon} {s.value}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Event Risk Summary */}
      {data?.event_risk_summary?.total_events > 0 && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
          <div className="flex items-center gap-2 text-amber-400 text-sm font-medium mb-1">
            <Calendar className="w-4 h-4" />
            {data.event_risk_summary.total_events} Economic Events Tomorrow
            {data.event_risk_summary.high_impact_count > 0 && (
              <span className="text-red-400 text-xs">({data.event_risk_summary.high_impact_count} HIGH IMPACT)</span>
            )}
          </div>
        </div>
      )}

      {/* Forecast Cards */}
      {loading && forecasts.length === 0 ? (
        <div className="flex items-center justify-center py-20 text-slate-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Generating forecasts…
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
          {forecasts.map((f: any) => {
            const isExpanded = expanded === f.asset;
            return (
              <div key={f.asset}
                className="bg-slate-900/60 border border-slate-800/50 rounded-xl overflow-hidden hover:border-slate-700/50 transition-colors">
                {/* Card Header */}
                <div className="p-3 flex items-center justify-between cursor-pointer"
                  onClick={() => setExpanded(isExpanded ? null : f.asset)}>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-white">{f.asset}</span>
                    <DirectionBadge direction={f.direction} confidence={f.confidence} />
                  </div>
                  <div className="flex items-center gap-2">
                    <QualBadge qualified={f.is_trade_signal_qualified} reason={f.trade_disqualification_reason} />
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="px-3 pb-2 grid grid-cols-3 sm:grid-cols-6 gap-2 text-[10px]">
                  <div><span className="text-slate-500">Price</span><br /><span className="text-white font-mono font-semibold">{f.current_price ? Number(f.current_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : '—'}</span></div>
                  <div><span className="text-slate-500">Consensus</span><br /><span className="text-white font-semibold">{f.consensus_score?.toFixed(1)}%</span></div>
                  <div><span className="text-slate-500">Agreement</span><br /><span className="text-white font-semibold">{f.consensus_agreement_pct?.toFixed(0)}%</span></div>
                  <div><span className="text-slate-500">Regime</span><br /><span className="text-blue-400 font-medium">{f.market_regime || '—'}</span></div>
                  <div><span className="text-slate-500">Event Risk</span><br /><RiskBadge level={f.event_risk || 'NONE'} /></div>
                  <div><span className="text-slate-500">Reevaluate</span><br /><span className="text-accent-cyan font-mono">Next H4</span></div>
                </div>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="border-t border-slate-800/50 p-3 space-y-3">
                    {/* Model Breakdown */}
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 mb-1.5 flex items-center gap-1"><Brain className="w-3.5 h-3.5" /> Model Breakdown</h4>
                      <div className="grid grid-cols-2 gap-1.5">
                        {['quant_prediction', 'kronos_prediction', 'faiss_prediction', 'time_pattern_prediction', 'regime_prediction', 'macro_prediction', 'news_prediction', 'ai_prediction'].map(key => {
                          const pred = f[key];
                          if (!pred) return null;
                          return (
                            <div key={key} className="flex items-center justify-between bg-slate-800/40 rounded px-2 py-1 text-[10px]">
                              <span className="text-slate-400">{(pred.model || key).replace(/_prediction$/, '').replace(/_/g, ' ')}</span>
                              <DirectionBadge direction={pred.direction || 'NEUTRAL'} confidence={pred.confidence} />
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* AI Reasoning */}
                    {f.ai_reasoning && (
                      <div className="bg-slate-800/30 rounded-lg p-2.5">
                        <h4 className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1"><Activity className="w-3.5 h-3.5" /> AI Analysis</h4>
                        <p className="text-xs text-slate-300 leading-relaxed">{f.ai_reasoning}</p>
                      </div>
                    )}

                    {/* Key Factors */}
                    {f.key_factors?.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-1">Key Factors</h4>
                        <ul className="text-[10px] text-slate-300 space-y-0.5">
                          {f.key_factors.map((factor: string, i: number) => (
                            <li key={i} className="flex items-start gap-1">
                              <span className="text-emerald-400 mt-0.5">•</span> {factor}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Trade Details (if qualified) */}
                    {f.is_trade_signal_qualified && (
                      <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-2.5">
                        <h4 className="text-xs font-semibold text-emerald-400 mb-1 flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> Trade Signal</h4>
                        <div className="grid grid-cols-3 gap-2 text-[10px]">
                          <div><span className="text-slate-500">Entry</span><br /><span className="text-white">{f.entry_price || '—'}</span></div>
                          <div><span className="text-slate-500">SL</span><br /><span className="text-red-400">{f.stop_loss || '—'}</span></div>
                          <div><span className="text-slate-500">TP</span><br /><span className="text-emerald-400">{f.take_profit || '—'}</span></div>
                        </div>
                      </div>
                    )}

                    {/* Disqualification reason */}
                    {!f.is_trade_signal_qualified && f.trade_disqualification_reason && (
                      <div className="text-[10px] text-slate-500 italic">
                        ⚠ No Trade: {f.trade_disqualification_reason}
                      </div>
                    )}

                    {/* Scenarios */}
                    {f.scenarios && Object.keys(f.scenarios).length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1"><BarChart3 className="w-3.5 h-3.5" /> Event Scenarios</h4>
                        {Object.entries(f.scenarios).map(([eventName, scenarios]: [string, any]) => (
                          <div key={eventName} className="mb-2">
                            <div className="text-[10px] text-slate-300 font-medium mb-1">{eventName}</div>
                            <div className="grid grid-cols-3 gap-1">
                              {['HOT', 'IN_LINE', 'COOL'].map(scenario => {
                                const s = scenarios?.[scenario];
                                const colors = { HOT: 'border-red-500/30 bg-red-500/5', IN_LINE: 'border-slate-600/30 bg-slate-800/30', COOL: 'border-blue-500/30 bg-blue-500/5' };
                                return (
                                  <div key={scenario} className={`rounded p-1.5 border text-[9px] ${colors[scenario as keyof typeof colors] || ''}`}>
                                    <div className="font-semibold text-slate-300">{scenario.replace('_', ' ')}</div>
                                    <div className="text-slate-500">{s?.probability ? `${(s.probability * 100).toFixed(0)}%` : '—'}</div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      {data?.generated_at && (
        <div className="text-center text-[10px] text-slate-600 pt-2">
          Generated: {toIST(data.generated_at)} IST · Cutoff: {toIST(data.data_cutoff)} IST · Trace: {data.trace_id?.slice(0, 8)}
        </div>
      )}
    </div>
  );
};
