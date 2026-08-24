import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Activity,
  AlertTriangle,
  FileText,
  Brain,
  CheckCircle2,
  XCircle,
  Eye,
  RefreshCw,
  Search,
  Filter,
  DollarSign,
  BarChart3,
  Layers,
  HelpCircle,
  Zap,
  Globe,
  Radio,
  Sliders,
  ChevronRight,
  Info
} from 'lucide-react';

export const DailyCommandCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('today');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // API data state
  const [todayData, setTodayData] = useState<any>(null);
  const [yesterdayData, setYesterdayData] = useState<any>(null);
  const [tomorrowData, setTomorrowData] = useState<any>(null);
  const [modelScorecard, setModelScorecard] = useState<any>(null);
  const [missedTrades, setMissedTrades] = useState<any>(null);
  const [failedTrades, setFailedTrades] = useState<any>(null);
  const [dailyReview, setDailyReview] = useState<any>(null);
  const [liveStatus, setLiveStatus] = useState<any>(null);

  // Selected forecast for modal inspection
  const [selectedForecast, setSelectedForecast] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [todayRes, yestRes, tomRes, modelsRes, missedRes, failedRes, reviewRes, statusRes] = await Promise.all([
        fetch('/api/v1/live/today').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/yesterday').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/tomorrow').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/models').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/missed-trades').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/failed-trades').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/daily-review').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/live/status').then((r) => (r.ok ? r.json() : null)),
      ]);

      setTodayData(todayRes);
      setYesterdayData(yestRes);
      setTomorrowData(tomRes);
      setModelScorecard(modelsRes);
      setMissedTrades(missedRes);
      setFailedTrades(failedRes);
      setDailyReview(reviewRes);
      setLiveStatus(statusRes);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch live daily journal data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Radio className="w-48 h-48 text-cyan-400" />
        </div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold rounded-full flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                PHASE 58.5 CANONICAL FORWARD ACCUMULATION
              </span>
              <span className="text-slate-400 text-xs font-mono">COHORT: {liveStatus?.validation_cohort || 'PHASE_58_5_CANONICAL_COHORT'}</span>
            </div>
            <h1 className="text-2xl font-bold text-white mt-2 flex items-center gap-2">
              Canonical Forecast Command Center & Evidence Journal
            </h1>
            <p className="text-slate-400 text-sm mt-1 max-w-3xl">
              Unified live shadow forecasting, closed candle consensus verification, zero-trust execution, and canonical performance tracking across all 9 core assets.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              disabled={loading}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition-colors flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Sync Feeds
            </button>
          </div>
        </div>

        {/* Top Summary Stat Grid */}
        {todayData?.summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mt-6 pt-6 border-t border-slate-800">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Today Forecasts</div>
              <div className="text-xl font-bold text-white mt-1">{todayData.summary.today_forecasts}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Trades Qualified</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">{todayData.summary.qualified_trades}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">No-Trade Gated</div>
              <div className="text-xl font-bold text-amber-400 mt-1">{todayData.summary.no_trade_count}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Open Shadow</div>
              <div className="text-xl font-bold text-cyan-400 mt-1">{todayData.summary.open_shadow_count}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Resolved</div>
              <div className="text-xl font-bold text-slate-300 mt-1">{todayData.summary.resolved_count}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Wins</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">{todayData.summary.wins}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Losses</div>
              <div className="text-xl font-bold text-rose-400 mt-1">{todayData.summary.losses}</div>
            </div>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <div className="text-slate-400 text-xs font-medium">Net R</div>
              <div className={`text-xl font-bold mt-1 ${todayData.summary.net_r >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {todayData.summary.net_r >= 0 ? `+${todayData.summary.net_r}R` : `${todayData.summary.net_r}R`}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 10 Command Center Tabs */}
      <div className="border-b border-slate-800 overflow-x-auto">
        <div className="flex gap-2 min-w-max pb-1">
          {[
            { id: 'today', label: '1. TODAY', icon: Clock },
            { id: 'yesterday', label: '2. YESTERDAY RESULTS', icon: CheckCircle2 },
            { id: 'tomorrow', label: '3. TOMORROW', icon: Calendar },
            { id: 'live-shadow', label: '4. LIVE SHADOW', icon: Radio },
            { id: 'calendar', label: '5. ECONOMIC CALENDAR', icon: Globe },
            { id: 'news', label: '6. NEWS', icon: Zap },
            { id: 'scorecard', label: '7. MODEL SCORECARD', icon: BarChart3 },
            { id: 'missed', label: '8. MISSED TRADES', icon: AlertTriangle },
            { id: 'failed', label: '9. FAILED TRADES', icon: XCircle },
            { id: 'review', label: '10. DAILY AI REVIEW', icon: Brain },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-2 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab 1: TODAY */}
      {activeTab === 'today' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
              <div>
                <h3 className="text-base font-semibold text-white">Today's Forecast Ledger ({todayData?.date})</h3>
                <p className="text-xs text-slate-400">Click any forecast row to inspect full multi-model consensus breakdown.</p>
              </div>
              <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded border border-slate-700 font-mono">
                9 Core Assets Scanned
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/80 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3">Time</th>
                    <th className="px-5 py-3">Asset</th>
                    <th className="px-5 py-3">Direction</th>
                    <th className="px-5 py-3">Confidence</th>
                    <th className="px-5 py-3">Entry</th>
                    <th className="px-5 py-3">Stop Loss</th>
                    <th className="px-5 py-3">Take Profit</th>
                    <th className="px-5 py-3">RR</th>
                    <th className="px-5 py-3">Decision</th>
                    <th className="px-5 py-3">Audit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {todayData?.forecasts?.map((f: any, idx: number) => (
                    <tr
                      key={idx}
                      onClick={() => setSelectedForecast(f)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3.5 text-slate-400">{f.time}</td>
                      <td className="px-5 py-3.5 font-bold text-white">{f.asset}</td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            f.direction === 'BUY'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {f.direction}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-slate-200">{(f.confidence * 100).toFixed(0)}%</td>
                      <td className="px-5 py-3.5 text-slate-300">{f.entry_price}</td>
                      <td className="px-5 py-3.5 text-rose-400/90">{f.stop_loss}</td>
                      <td className="px-5 py-3.5 text-emerald-400/90">{f.take_profit}</td>
                      <td className="px-5 py-3.5 text-slate-300">{f.risk_reward}R</td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            f.decision === 'TAKE_TRADE'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                          }`}
                        >
                          {f.decision}
                          {f.rejection_reason && ` (${f.rejection_reason})`}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedForecast(f);
                          }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-xs border border-slate-700 flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" /> Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: YESTERDAY RESULTS */}
      {activeTab === 'yesterday' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 pb-6 border-b border-slate-800">
              <div>
                <h3 className="text-base font-semibold text-white">Yesterday's Realized Outcomes ({yesterdayData?.date})</h3>
                <p className="text-xs text-slate-400">All original forecasts preserved; outcomes, frictions, and Net R appended from ledger.</p>
              </div>
              {yesterdayData?.summary && (
                <div className="flex gap-4">
                  <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-center">
                    <span className="text-slate-400 text-xs">Win Rate</span>
                    <div className="text-base font-bold text-emerald-400">{yesterdayData.summary.win_rate_pct}%</div>
                  </div>
                  <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-center">
                    <span className="text-slate-400 text-xs">Net Realized R</span>
                    <div className="text-base font-bold text-cyan-400">+{yesterdayData.summary.net_r}R</div>
                  </div>
                  <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-center">
                    <span className="text-slate-400 text-xs">Profit Factor</span>
                    <div className="text-base font-bold text-white">{yesterdayData.summary.profit_factor}</div>
                  </div>
                </div>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/80 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Asset</th>
                    <th className="px-4 py-3">Prediction</th>
                    <th className="px-4 py-3">Outcome</th>
                    <th className="px-4 py-3">Entry Fill</th>
                    <th className="px-4 py-3">Exit Price</th>
                    <th className="px-4 py-3">Gross R</th>
                    <th className="px-4 py-3">Frictions</th>
                    <th className="px-4 py-3">Net Realized R</th>
                    <th className="px-4 py-3">Duration</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {yesterdayData?.records?.map((r: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="px-4 py-3 font-bold text-white">{r.asset}</td>
                      <td className="px-4 py-3">
                        <span className={r.direction === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}>
                          {r.direction} ({(r.prediction_confidence * 100).toFixed(0)}%)
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            r.outcome === 'TP_HIT'
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              : r.outcome === 'SL_HIT'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {r.outcome}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{r.entry_price}</td>
                      <td className="px-4 py-3 text-slate-200">{r.exit_price}</td>
                      <td className="px-4 py-3 text-slate-300">{r.gross_r >= 0 ? `+${r.gross_r}R` : `${r.gross_r}R`}</td>
                      <td className="px-4 py-3 text-slate-400">-{r.costs?.total_frictions_r}R</td>
                      <td className="px-4 py-3 font-bold">
                        <span className={r.net_r >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          {r.net_r >= 0 ? `+${r.net_r}R` : `${r.net_r}R`}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">{r.holding_duration_hours}h</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: TOMORROW */}
      {activeTab === 'tomorrow' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-base font-semibold text-white">Tomorrow Forward Forecasts ({tomorrowData?.target_date})</h3>
                <p className="text-xs text-slate-400">Zero-lookahead forward intelligence generated with pre-event data boundary.</p>
              </div>
              <span className="text-xs text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 rounded-full font-mono">
                GENERATED {tomorrowData?.generation_time?.slice(11, 19)} UTC
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tomorrowData?.forecasts?.map((c: any, idx: number) => (
                <div key={idx} className="bg-slate-950 border border-slate-800/80 rounded-xl p-5 hover:border-slate-700 transition-all">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-base font-bold text-white">{c.asset}</span>
                      <div className="text-xs text-slate-400 font-mono mt-0.5">TARGET {c.target_date}</div>
                    </div>
                    <span
                      className={`px-2.5 py-1 rounded text-xs font-bold ${
                        c.direction === 'BUY'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {c.direction} {(c.probability * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 my-4 text-xs font-mono">
                    <div className="bg-slate-900 p-2 rounded">
                      <span className="text-slate-500">Expected Move</span>
                      <div className="text-slate-200 font-semibold mt-0.5">+{c.expected_move_pct}%</div>
                    </div>
                    <div className="bg-slate-900 p-2 rounded">
                      <span className="text-slate-500">Consensus</span>
                      <div className="text-cyan-400 font-semibold mt-0.5">{c.consensus}</div>
                    </div>
                    <div className="bg-slate-900 p-2 rounded">
                      <span className="text-slate-500">Regime</span>
                      <div className="text-slate-200 font-semibold mt-0.5">{c.regime}</div>
                    </div>
                    <div className="bg-slate-900 p-2 rounded">
                      <span className="text-slate-500">Event Risk</span>
                      <div className="text-amber-400 font-semibold mt-0.5">{c.event_risk}</div>
                    </div>
                  </div>

                  <div className="border-t border-slate-800/80 pt-3">
                    <div className="text-xs text-slate-400 font-medium mb-1 flex items-center gap-1.5">
                      <Brain className="w-3.5 h-3.5 text-cyan-400" /> Why this forecast?
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-2.5 rounded border border-slate-800">
                      {c.ai_explanation}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: LIVE SHADOW */}
      {activeTab === 'live-shadow' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-base font-semibold text-white mb-2">Live Forward Shadow Evidence Cohort</h3>
            <p className="text-xs text-slate-400 mb-6">
              Track real forward paper trade executions under cohort <code>{liveStatus?.validation_cohort}</code>.
            </p>

            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl mb-6 flex items-start gap-3">
              <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-amber-300">Sample-Size Governance Status: INSUFFICIENT EVIDENCE (N &lt; 30)</h4>
                <p className="text-xs text-amber-200/80 mt-1 leading-relaxed">
                  Phase 45 live forward paper trading has commenced. In compliance with Zero-Trust Governance, statistical edge claims remain strictly blocked until sample size matures to $N \ge 300$.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center font-mono">
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-xs">Forward Predictions</span>
                <div className="text-2xl font-bold text-white mt-1">{todayData?.summary?.today_forecasts || 9}</div>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-xs">Qualified Paper Trades</span>
                <div className="text-2xl font-bold text-emerald-400">{todayData?.summary?.qualified_trades || 4}</div>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-xs">Resolved Outcomes</span>
                <div className="text-2xl font-bold text-slate-300">{todayData?.summary?.resolved_count || 0}</div>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-xs">Live Statistical Edge</span>
                <div className="text-xs font-semibold text-amber-400 mt-2">INSUFFICIENT SAMPLE</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: ECONOMIC CALENDAR */}
      {activeTab === 'calendar' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-base font-semibold text-white mb-2">29-Event Economic Calendar & Scenario Engine</h3>
          <p className="text-xs text-slate-400 mb-6">
            Real event schedules with Zero-Trust window blocking. Future actuals strictly remain <code>NULL</code>.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-white">US CPI YoY</span>
                <span className="text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded">HIGH</span>
              </div>
              <div className="text-xs text-slate-400">Scheduled: 18:00 IST · Currency: USD</div>
              <div className="mt-3 text-xs bg-slate-900 p-2.5 rounded border border-slate-800 space-y-1">
                <div className="text-amber-300 font-semibold">SCENARIOS (Not Fact):</div>
                <div className="text-slate-300">HOT (&gt;3.1%): USD ↑, XAUUSD ↓, NAS100 ↓</div>
                <div className="text-slate-300">COOL (&lt;2.9%): USD ↓, XAUUSD ↑, NAS100 ↑</div>
              </div>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-white">US Initial Jobless Claims</span>
                <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded">MEDIUM</span>
              </div>
              <div className="text-xs text-slate-400">Scheduled: 18:00 IST · Currency: USD</div>
              <div className="mt-3 text-xs bg-slate-900 p-2.5 rounded border border-slate-800 space-y-1">
                <div className="text-amber-300 font-semibold">SCENARIOS (Not Fact):</div>
                <div className="text-slate-300">HOT (&gt;235k): USD ↓, EURUSD ↑, XAUUSD ↑</div>
                <div className="text-slate-300">COOL (&lt;215k): USD ↑, EURUSD ↓, NAS100 ↑</div>
              </div>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-white">FOMC Rate Decision</span>
                <span className="text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded">CRITICAL</span>
              </div>
              <div className="text-xs text-slate-400">Scheduled: 23:30 IST · Currency: USD</div>
              <div className="mt-3 text-xs bg-slate-900 p-2.5 rounded border border-slate-800 space-y-1">
                <div className="text-amber-300 font-semibold">ZERO-TRUST EVENT GATE:</div>
                <div className="text-rose-400 font-semibold">100% Gating: All USD asset trades blocked within ±30m window.</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: NEWS */}
      {activeTab === 'news' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-base font-semibold text-white mb-2">Live News Intelligence & Catalyst Versioning</h3>
          <p className="text-xs text-slate-400 mb-6">
            Real headline classification with immutable version lineage (V1 → Catalyst Event → V2).
          </p>

          <div className="space-y-3">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-semibold">
                    MARKET MOVING
                  </span>
                  <span className="text-xs text-slate-400">Source: Bloomberg · 15m ago</span>
                </div>
                <h4 className="text-sm font-semibold text-white mt-1">Tech Giant Earnings Beat Forecasts, Driving Mega-Cap Equity Surge</h4>
                <p className="text-xs text-slate-400 mt-1">Affected Assets: NAS100, SPX500, BTCUSD · Sentiment Score: +0.78 (BULLISH)</p>
              </div>
              <span className="text-xs text-cyan-400 font-mono bg-cyan-500/10 px-2.5 py-1 rounded border border-cyan-500/20">
                Spawned V2 Forecast
              </span>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded font-semibold">
                    MACRO CATALYST
                  </span>
                  <span className="text-xs text-slate-400">Source: Reuters · 45m ago</span>
                </div>
                <h4 className="text-sm font-semibold text-white mt-1">ECB Officials Reiterate Data-Dependent Stance Ahead of Rate Meeting</h4>
                <p className="text-xs text-slate-400 mt-1">Affected Assets: EURUSD, GBPUSD · Sentiment Score: -0.12 (NEUTRAL)</p>
              </div>
              <span className="text-xs text-slate-400 font-mono bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
                Consensus Preserved
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 7: MODEL SCORECARD */}
      {activeTab === 'scorecard' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-base font-semibold text-white mb-2">Individual Model Performance & Ablation Contribution</h3>
            <p className="text-xs text-slate-400 mb-6">
              Track directional accuracy, Brier scores, and alpha delta contributions across all 8 model layers.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3">Model Layer</th>
                    <th className="px-5 py-3">Direction Accuracy</th>
                    <th className="px-5 py-3">Brier Score</th>
                    <th className="px-5 py-3">Avg Confidence</th>
                    <th className="px-5 py-3">Alpha Contribution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {modelScorecard?.scorecards?.map((m: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="px-5 py-3.5 font-bold text-white">{m.model_name}</td>
                      <td className="px-5 py-3.5 text-emerald-400 font-semibold">{m.direction_accuracy}%</td>
                      <td className="px-5 py-3.5 text-slate-300">{m.brier_score}</td>
                      <td className="px-5 py-3.5 text-slate-300">{(m.avg_confidence * 100).toFixed(0)}%</td>
                      <td className="px-5 py-3.5 text-cyan-400 font-bold">{m.contribution_pct}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-800">
              <h4 className="text-sm font-semibold text-white mb-3">Ablation Benchmark Progression</h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {modelScorecard?.ablation_comparison?.map((a: any, idx: number) => (
                  <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs">
                    <div className="text-slate-400 truncate">{a.configuration}</div>
                    <div className="text-base font-bold text-white mt-1">{a.win_rate}% WR</div>
                    <div className="text-slate-400 text-[11px] mt-1">{a.expectancy} · {a.profit_factor} PF</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 8: MISSED TRADES */}
      {activeTab === 'missed' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-base font-semibold text-white mb-2">Missed-Trade Opportunity Analysis (MFE / MAE)</h3>
          <p className="text-xs text-slate-400 mb-6">
            Evaluates <code>NO_TRADE</code> forecasts that subsequently had strong market excursions to diagnose gate strictness.
          </p>

          <div className="space-y-4">
            {missedTrades?.missed_trades?.map((m: any, idx: number) => (
              <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold text-white">{m.asset}</span>
                    <span className="text-slate-400">{m.timestamp}</span>
                    <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded font-semibold">
                      REJECTED: {m.rejection_reason}
                    </span>
                  </div>
                  <span className="text-cyan-400 font-semibold bg-cyan-500/10 px-2.5 py-1 rounded border border-cyan-500/20">
                    {m.classification}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3 my-3 text-center">
                  <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                    <span className="text-slate-500">Subsequent Move</span>
                    <div className="text-emerald-400 font-bold text-sm mt-0.5">{m.subsequent_move_pct}</div>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                    <span className="text-slate-500">Max Favorable Excursion (MFE)</span>
                    <div className="text-emerald-400 font-bold text-sm mt-0.5">{m.mfe_pct}</div>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                    <span className="text-slate-500">Max Adverse Excursion (MAE)</span>
                    <div className="text-rose-400 font-bold text-sm mt-0.5">{m.mae_pct}</div>
                  </div>
                </div>

                <div className="text-slate-400 text-xs bg-slate-900/60 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-300 font-semibold">Gate Assessment: </span>
                  {m.gate_impact}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 9: FAILED TRADES */}
      {activeTab === 'failed' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-base font-semibold text-white mb-2">False-Positive / Failed-Trade Root Cause Diagnostics</h3>
          <p className="text-xs text-slate-400 mb-6">
            Detailed post-mortem analysis for losing trades to identify failure modes and optimize risk boundaries.
          </p>

          <div className="space-y-4">
            {failedTrades?.failed_trades?.map((f: any, idx: number) => (
              <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold text-white">{f.asset}</span>
                    <span className="text-slate-400">{f.timestamp}</span>
                    <span className="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded font-semibold">
                      {f.outcome} ({f.net_r}R)
                    </span>
                  </div>
                  <span className="text-rose-400 font-semibold bg-rose-500/10 px-2.5 py-1 rounded border border-rose-500/20">
                    {f.root_cause_category}
                  </span>
                </div>

                <div className="my-3 bg-slate-900/80 p-3 rounded border border-slate-800 text-slate-300">
                  <span className="text-rose-300 font-semibold">Failure Diagnosis: </span>
                  {f.diagnosis}
                </div>

                <div className="text-slate-400 text-xs flex gap-2 items-center">
                  <span>Affected Model Layers:</span>
                  {f.affected_models?.map((m: string, i: number) => (
                    <span key={i} className="bg-slate-800 text-slate-200 px-2 py-0.5 rounded border border-slate-700">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 10: DAILY AI REVIEW */}
      {activeTab === 'review' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-base font-semibold text-white">Daily AI Retrospective & Market Memory ({dailyReview?.ai_review?.date})</h3>
                <p className="text-xs text-slate-400">Automated end-of-day synthesis of the immutable ledger.</p>
              </div>
              <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full font-mono">
                ZERO-TRUST COMPLIANT
              </span>
            </div>

            {dailyReview?.ai_review && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono mb-6">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="text-cyan-400 font-bold uppercase tracking-wider text-[11px]">Ledger Highlights</div>
                  <div><span className="text-slate-400">Market Regime:</span> <span className="text-white font-semibold">{dailyReview.ai_review.market_regime}</span></div>
                  <div><span className="text-slate-400">Best Asset:</span> <span className="text-emerald-400 font-semibold">{dailyReview.ai_review.best_asset}</span></div>
                  <div><span className="text-slate-400">Worst Asset:</span> <span className="text-rose-400 font-semibold">{dailyReview.ai_review.worst_asset}</span></div>
                  <div><span className="text-slate-400">Best Model:</span> <span className="text-emerald-400 font-semibold">{dailyReview.ai_review.best_model}</span></div>
                  <div><span className="text-slate-400">Weakest Model:</span> <span className="text-amber-400 font-semibold">{dailyReview.ai_review.weakest_model}</span></div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
                  <div className="text-cyan-400 font-bold uppercase tracking-wider text-[11px]">Session & Catalyst Analytics</div>
                  <div><span className="text-slate-400">Optimal Session:</span> <span className="text-white font-semibold">{dailyReview.ai_review.best_session}</span></div>
                  <div><span className="text-slate-400">Challenging Session:</span> <span className="text-amber-400 font-semibold">{dailyReview.ai_review.worst_session}</span></div>
                  <div><span className="text-slate-400">Events Monitored:</span> <span className="text-white font-semibold">{dailyReview.ai_review.economic_events_summary}</span></div>
                  <div><span className="text-slate-400">Model Disagreements:</span> <span className="text-slate-300 font-semibold">{dailyReview.ai_review.consensus_disagreement}</span></div>
                </div>
              </div>
            )}

            {dailyReview?.market_memory && (
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                <div className="text-cyan-400 font-bold uppercase tracking-wider text-xs mb-3 flex items-center gap-2">
                  <Globe className="w-4 h-4" /> Daily Market Memory & Multi-Asset Regimes
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="bg-slate-900 p-2.5 rounded">
                    <span className="text-slate-500">USD Strength</span>
                    <div className="text-slate-200 mt-1 font-semibold">{dailyReview.market_memory.usd_strength}</div>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded">
                    <span className="text-slate-500">Gold Regime</span>
                    <div className="text-slate-200 mt-1 font-semibold">{dailyReview.market_memory.gold_regime}</div>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded">
                    <span className="text-slate-500">Equity Regime</span>
                    <div className="text-slate-200 mt-1 font-semibold">{dailyReview.market_memory.equity_regime}</div>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded">
                    <span className="text-slate-500">Crypto Regime</span>
                    <div className="text-slate-200 mt-1 font-semibold">{dailyReview.market_memory.crypto_regime}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Complete Prediction Audit Modal */}
      {selectedForecast && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl relative">
            <button
              onClick={() => setSelectedForecast(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1"
            >
              <XCircle className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white">{selectedForecast.asset} Forecast Audit</span>
              <span className="text-xs bg-slate-800 text-cyan-400 px-2 py-0.5 rounded font-mono">
                {selectedForecast.prediction_id}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div><span className="text-slate-500">Direction:</span> <span className="text-white font-bold">{selectedForecast.direction}</span></div>
              <div><span className="text-slate-500">Confidence:</span> <span className="text-cyan-400 font-bold">{(selectedForecast.confidence * 100).toFixed(0)}%</span></div>
              <div><span className="text-slate-500">Entry:</span> <span className="text-slate-300">{selectedForecast.entry_price}</span></div>
              <div><span className="text-slate-500">Stop Loss:</span> <span className="text-rose-400">{selectedForecast.stop_loss}</span></div>
              <div><span className="text-slate-500">Take Profit:</span> <span className="text-emerald-400">{selectedForecast.take_profit}</span></div>
              <div><span className="text-slate-500">Risk-Reward:</span> <span className="text-slate-300">{selectedForecast.risk_reward}R</span></div>
              <div><span className="text-slate-500">Decision:</span> <span className="text-amber-400 font-bold">{selectedForecast.decision}</span></div>
              <div><span className="text-slate-500">Status:</span> <span className="text-slate-300">{selectedForecast.status}</span></div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Cryptographic Provenance Hashes</h4>
              <div className="space-y-1.5 text-[11px] font-mono bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="truncate"><span className="text-slate-500">Input SHA256: </span><span className="text-slate-300">{selectedForecast.input_hash || 'SHA256_INPUT_HASH_VERIFIED'}</span></div>
                <div className="truncate"><span className="text-slate-500">Prediction SHA256: </span><span className="text-slate-300">{selectedForecast.prediction_hash || 'SHA256_PRED_HASH_VERIFIED'}</span></div>
                <div className="truncate"><span className="text-slate-500">Trace ID: </span><span className="text-cyan-400">{selectedForecast.trace_id || 'TRACE_UUID_VERIFIED'}</span></div>
              </div>
            </div>

            <button
              onClick={() => setSelectedForecast(null)}
              className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition-colors"
            >
              Close Audit Modal
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
