import React, { useEffect, useState } from 'react';
import {
  Calendar, Clock, RefreshCw, AlertTriangle, ChevronDown, ChevronUp,
  TrendingUp, TrendingDown, Minus, Globe, Filter,
} from 'lucide-react';

const API_BASE = '/api/v1';

const IST_TZ = 'Asia/Kolkata';
const toIST = (ts: any): string => {
  if (!ts) return '—';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleString('en-IN', { timeZone: IST_TZ, hour12: false, month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

type TabView = 'today' | 'tomorrow' | 'week';

const ImportanceBadge: React.FC<{ level: string }> = ({ level }) => {
  const styles: Record<string, string> = {
    HIGH: 'bg-red-500/20 text-red-400 border-red-500/30',
    MEDIUM: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    LOW: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${styles[level] || styles.LOW}`}>
      {level}
    </span>
  );
};

const CurrencyBadge: React.FC<{ currency: string }> = ({ currency }) => {
  const colors: Record<string, string> = {
    USD: 'bg-green-500/15 text-green-400', EUR: 'bg-blue-500/15 text-blue-400',
    GBP: 'bg-purple-500/15 text-purple-400', JPY: 'bg-red-500/15 text-red-400',
    AUD: 'bg-amber-500/15 text-amber-400', CAD: 'bg-orange-500/15 text-orange-400',
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${colors[currency] || 'bg-slate-700 text-slate-300'}`}>
      {currency}
    </span>
  );
};

const CountdownBadge: React.FC<{ countdown: string }> = ({ countdown }) => {
  if (countdown === 'RELEASED') {
    return <span className="text-emerald-400 text-xs font-medium">✓ Released</span>;
  }
  return (
    <span className="flex items-center gap-1 text-xs text-amber-400 font-mono">
      <Clock className="w-3 h-3" /> {countdown}
    </span>
  );
};

export const EconomicCalendar: React.FC = () => {
  const [tab, setTab] = useState<TabView>('today');
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [currencyFilter, setCurrencyFilter] = useState<string>('ALL');

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/calendar/events?filter_type=${tab}`);
      const json = await res.json();
      setEvents(json?.events || []);
    } catch { /* offline */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [tab]);

  const filtered = currencyFilter === 'ALL'
    ? events
    : events.filter(e => e.currency === currencyFilter);

  const currencies = ['ALL', ...new Set(events.map(e => e.currency))];

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4" style={{ background: 'linear-gradient(135deg, #0a0e17 0%, #111827 50%, #0d1321 100%)' }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
            <Calendar className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Economic Calendar</h1>
            <p className="text-xs text-slate-400">Macro events with probabilistic scenario analysis</p>
          </div>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-300 hover:bg-slate-700/60 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Tab Bar */}
      <div className="flex items-center gap-2">
        {(['today', 'tomorrow', 'week'] as TabView[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-slate-800/40 text-slate-400 border border-slate-700/30 hover:bg-slate-700/40'
            }`}>
            {t === 'today' ? 'Today' : t === 'tomorrow' ? 'Tomorrow' : 'Next 7 Days'}
          </button>
        ))}
        <div className="flex-1" />
        {/* Currency Filter */}
        <div className="flex items-center gap-1">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          {currencies.map(c => (
            <button key={c} onClick={() => setCurrencyFilter(c)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                currencyFilter === c ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800/40 text-slate-500 hover:text-slate-300'
              }`}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Events Table */}
      {loading && events.length === 0 ? (
        <div className="flex items-center justify-center py-20 text-slate-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading calendar…
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
          No events found for this period
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((event: any) => {
            const isExpanded = expanded === event.event_id;
            return (
              <div key={event.event_id}
                className="bg-slate-900/60 border border-slate-800/50 rounded-xl overflow-hidden hover:border-slate-700/50 transition-colors">
                {/* Event Row */}
                <div className="p-3 flex items-center gap-3 cursor-pointer" onClick={() => setExpanded(isExpanded ? null : event.event_id)}>
                  <div className="w-24 flex-shrink-0">
                    <div className="text-xs text-slate-300 font-mono">{toIST(event.scheduled_utc)}</div>
                    <CountdownBadge countdown={event.countdown || '—'} />
                  </div>
                  <CurrencyBadge currency={event.currency} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white font-medium truncate">{event.event_name}</div>
                    <div className="text-[10px] text-slate-500">{event.event_category} · {event.country}</div>
                  </div>
                  <ImportanceBadge level={event.importance} />
                  <div className="grid grid-cols-3 gap-3 text-[10px] text-center w-48">
                    <div><span className="text-slate-500">Forecast</span><br /><span className="text-white font-mono">{event.forecast_value ?? '—'}</span></div>
                    <div><span className="text-slate-500">Previous</span><br /><span className="text-slate-300 font-mono">{event.previous_value ?? '—'}</span></div>
                    <div><span className="text-slate-500">Actual</span><br /><span className="text-amber-400 font-mono">{event.actual_value ?? 'PENDING'}</span></div>
                  </div>
                  {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                </div>

                {/* Expanded: Scenarios + Sensitivities */}
                {isExpanded && (
                  <div className="border-t border-slate-800/50 p-3 space-y-3">
                    {/* 3-Way Scenarios */}
                    {event.scenarios && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" /> Probabilistic Scenarios
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          {(['HOT', 'IN_LINE', 'COOL'] as const).map(scenario => {
                            const s = event.scenarios?.[scenario];
                            const styles = {
                              HOT: 'border-red-500/30 bg-red-500/5',
                              IN_LINE: 'border-slate-600/30 bg-slate-800/30',
                              COOL: 'border-blue-500/30 bg-blue-500/5',
                            };
                            const labels = { HOT: '🔥 HOT', IN_LINE: '➡️ IN LINE', COOL: '❄️ COOL' };
                            return (
                              <div key={scenario} className={`rounded-lg p-2.5 border ${styles[scenario]}`}>
                                <div className="text-xs font-bold text-white mb-1">{labels[scenario]}</div>
                                <div className="text-[10px] text-slate-400 mb-1.5">{s?.description || '—'}</div>
                                <div className="text-xs text-slate-300">
                                  Probability: <span className="font-bold">{s?.probability ? `${(s.probability * 100).toFixed(0)}%` : '—'}</span>
                                </div>
                                {/* Asset reactions */}
                                {s?.asset_reactions && Object.keys(s.asset_reactions).length > 0 && (
                                  <div className="mt-1.5 space-y-0.5">
                                    {Object.entries(s.asset_reactions).map(([asset, reaction]: [string, any]) => (
                                      <div key={asset} className="flex items-center justify-between text-[9px]">
                                        <span className="text-slate-500">{asset}</span>
                                        <span className={`font-medium ${reaction.direction === 'BUY' ? 'text-emerald-400' : reaction.direction === 'SELL' ? 'text-red-400' : 'text-slate-400'}`}>
                                          {reaction.direction === 'BUY' ? <TrendingUp className="w-2.5 h-2.5 inline" /> : reaction.direction === 'SELL' ? <TrendingDown className="w-2.5 h-2.5 inline" /> : <Minus className="w-2.5 h-2.5 inline" />}
                                          {' '}{reaction.expected_move_pips ? `${reaction.expected_move_pips}p` : '—'}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Historical Stats */}
                    {event.historical_stats?.sample_size > 0 && (
                      <div className="bg-slate-800/30 rounded-lg p-2.5">
                        <h4 className="text-xs font-semibold text-slate-400 mb-1">Historical Statistics ({event.historical_stats.sample_size} events)</h4>
                        <div className="grid grid-cols-3 gap-2 text-[10px]">
                          <div>HOT: <span className="text-red-400 font-bold">{((event.historical_stats.hot_pct || 0) * 100).toFixed(0)}%</span></div>
                          <div>In Line: <span className="text-slate-300 font-bold">{((event.historical_stats.in_line_pct || 0) * 100).toFixed(0)}%</span></div>
                          <div>Cool: <span className="text-blue-400 font-bold">{((event.historical_stats.cool_pct || 0) * 100).toFixed(0)}%</span></div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
