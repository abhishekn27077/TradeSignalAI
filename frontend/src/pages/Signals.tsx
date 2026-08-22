import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { Button } from '../components/core/Button';
import { ConfidenceMeter } from '../components/trading/ConfidenceMeter';
import {
  Search, Filter, Clock, CheckCircle2, XCircle, ChevronRight,
  Zap, RefreshCw, Brain, Target, Activity, AlertTriangle, Shield,
  BarChart3, TrendingUp, TrendingDown,
} from 'lucide-react';
import { api } from '../services/api-client';
import type { LiveSignal } from '../types';

const QUALITY_COLORS: Record<string, string> = {
  'A+': 'text-profit bg-profit/10 border-profit/20',
  'A': 'text-profit bg-profit/10 border-profit/20',
  'B+': 'text-accent-blue bg-accent-blue/10 border-accent-blue/20',
  'B': 'text-accent-blue bg-accent-blue/10 border-accent-blue/20',
  'C': 'text-warning bg-warning/10 border-warning/20',
  'D': 'text-loss bg-loss/10 border-loss/20',
  'REJECT': 'text-loss bg-loss/10 border-loss/20',
};

export const SignalsPage: React.FC = () => {
  const [liveSignals, setLiveSignals] = React.useState<LiveSignal[]>([]);
  const [activeSignal, setActiveSignal] = React.useState<LiveSignal | null>(null);
  const [loading, setLoading] = React.useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.signals.live();
      setLiveSignals(data || []);
    } catch (err) {
      console.error('Failed to load live signals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (liveSignals.length > 0 && !activeSignal) {
      setActiveSignal(liveSignals[0]);
    }
  }, [liveSignals]);

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-hidden bg-trading-dark">
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <Activity className="w-4 h-4 text-accent-blue" /> Live Signal Panel
        </h1>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-1 text-text-muted hover:text-text-primary">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="text" placeholder="Search..." className="bg-trading-surface border border-panel-border rounded-[var(--radius-md)] pl-8 pr-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent-blue/50 w-40 transition-colors" />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden grid grid-cols-[1.4fr_1fr] gap-3">
        <Card title="Live Feed" noPadding className="overflow-hidden flex flex-col">
          <div className="flex-1 overflow-auto">
            {loading && liveSignals.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-text-muted text-xs">Loading signals...</div>
            ) : liveSignals.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-text-muted text-xs border border-dashed border-panel-border/50 rounded m-4">
                No signals yet. Enable strategies to generate signals.
              </div>
            ) : (
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-trading-surface z-10">
                  <tr className="text-text-muted text-[10px] uppercase tracking-wider border-b border-panel-border">
                    <th className="text-left px-3 py-2.5 font-medium">Asset</th>
                    <th className="text-center px-3 py-2.5 font-medium">Direction</th>
                    <th className="text-left px-3 py-2.5 font-medium">Strategy</th>
                    <th className="text-center px-3 py-2.5 font-medium">Confidence</th>
                    <th className="text-center px-3 py-2.5 font-medium">Quality</th>
                    <th className="text-center px-3 py-2.5 font-medium">AI</th>
                    <th className="text-center px-3 py-2.5 font-medium">Hold</th>
                    <th className="px-3 py-2.5"></th>
                  </tr>
                </thead>
                <tbody>
                  {liveSignals.map((ls, idx) => {
                    const sig = ls.signal || {};
                    const pred = ls.prediction || {};
                    const quality = ls.trade_quality || {};
                    const aiVal = ls.ai_validation || {};
                    return (
                      <tr key={sig.signal_id || idx}
                        onClick={() => setActiveSignal(ls)}
                        className={`border-b border-panel-border/30 hover:bg-trading-hover transition-colors group cursor-pointer ${activeSignal?.signal?.signal_id === sig.signal_id ? 'bg-trading-hover/50' : ''}`}
                      >
                        <td className="px-3 py-3 font-medium text-text-primary whitespace-nowrap">{sig.symbol || sig.asset || '--'}</td>
                        <td className="px-3 py-3 text-center whitespace-nowrap">
                          <Badge variant={sig.direction === 'BUY' ? 'profit' : sig.direction === 'SELL' ? 'loss' : 'neutral'}>
                            {sig.direction || 'WAIT'}
                          </Badge>
                        </td>
                        <td className="px-3 py-3 text-text-primary">{sig.strategy_name || sig.strategy || '--'}</td>
                        <td className="px-3 py-3">
                          <div className="w-20 mx-auto">
                            <ConfidenceMeter value={((sig.confidence || 0.5) * 100)} size={60} />
                          </div>
                        </td>
                        <td className="px-3 py-3 text-center">
                          {quality.score != null ? (
                            <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium border ${QUALITY_COLORS[quality.grade] || 'text-text-muted'}`}>
                              {quality.grade} {quality.score}
                            </span>
                          ) : <span className="text-text-muted">--</span>}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {aiVal.decision === 'APPROVE' || aiVal.decision === 'INCREASE_CONFIDENCE' ? (
                            <CheckCircle2 className="w-4 h-4 text-profit mx-auto" />
                          ) : aiVal.decision === 'REDUCE_CONFIDENCE' ? (
                            <AlertTriangle className="w-4 h-4 text-warning mx-auto" />
                          ) : (
                            <XCircle className="w-4 h-4 text-loss mx-auto" />
                          )}
                        </td>
                        <td className="px-3 py-3 text-center text-[10px] text-text-secondary">
                          {pred.expected_holding_hours ? `${pred.expected_holding_hours}h` : '--'}
                        </td>
                        <td className="px-3 py-3 text-right">
                          <ChevronRight className="w-4 h-4 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity inline-block" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </Card>

        <div className="flex flex-col gap-3 overflow-auto">
          {activeSignal ? (
            <>
              <Card title="Signal Details" className="shrink-0">
                <SignalDetail signal={activeSignal} />
              </Card>
              <Card title="AI Validation" className="shrink-0">
                <AIValidationDetail ai={activeSignal.ai_validation} />
              </Card>
              <Card title="Trade Quality Breakdown" className="shrink-0">
                <QualityBreakdown quality={activeSignal.trade_quality} />
              </Card>
            </>
          ) : (
            <Card title="Signal Details">
              <div className="flex items-center justify-center h-full text-text-muted text-sm">Select a signal to view details</div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

const SignalDetail: React.FC<{ signal: LiveSignal }> = ({ signal }) => {
  const sig = signal.signal || {};
  const pred = signal.prediction || {};
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between pb-2 border-b border-panel-border/50">
        <div>
          <h2 className="text-base font-bold text-text-primary">{sig.symbol || sig.asset || '--'}</h2>
          <span className="text-[10px] text-text-muted">{sig.timestamp || '--'}</span>
        </div>
        <Badge variant={sig.direction === 'BUY' ? 'profit' : sig.direction === 'SELL' ? 'loss' : 'neutral'} className="text-sm px-3 py-1">
          {sig.direction || 'WAIT'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[10px]">
        <div className="bg-trading-elevated/30 p-2 rounded-[var(--radius-md)]">
          <div className="text-text-muted uppercase tracking-wider mb-1">Strategy</div>
          <div className="text-text-primary font-medium">{sig.strategy_name || sig.strategy || '--'}</div>
        </div>
        <div className="bg-trading-elevated/30 p-2 rounded-[var(--radius-md)]">
          <div className="text-text-muted uppercase tracking-wider mb-1">Confidence</div>
          <div className="text-text-primary font-medium">{((sig.confidence || 0.5) * 100).toFixed(0)}%</div>
        </div>
      </div>

      <div className="text-[10px] text-text-secondary leading-relaxed bg-trading-elevated/20 p-2 rounded-[var(--radius-md)]">
        {sig.reasoning || 'No reasoning provided'}
      </div>

      <div className="border-t border-panel-border/50 pt-2 mt-2">
        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2 font-semibold">Prediction & Risk</div>
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div>
            <span className="text-text-muted">Expected Move:</span>
            <span className={`ml-1 font-medium ${(pred.expected_move_pct || 0) >= 0 ? 'text-profit' : 'text-loss'}`}>
              {pred.expected_move_pct != null ? `${pred.expected_move_pct > 0 ? '+' : ''}${pred.expected_move_pct}%` : '--'}
            </span>
          </div>
          <div><span className="text-text-muted">Hold Time:</span><span className="ml-1 text-text-primary font-medium">{pred.expected_holding_hours || '--'}h</span></div>
          <div><span className="text-text-muted">Target:</span><span className="ml-1 text-profit font-medium">{sig.target_price ? `$${sig.target_price}` : '--'}</span></div>
          <div><span className="text-text-muted">Stop Loss:</span><span className="ml-1 text-loss font-medium">{sig.stop_loss ? `$${sig.stop_loss}` : '--'}</span></div>
          <div><span className="text-text-muted">Position Size:</span><span className="ml-1 text-text-primary font-medium">{sig.recommended_size || '--'}</span></div>
          <div><span className="text-text-muted">Risk Score:</span><span className="ml-1 text-warning font-medium">{sig.risk_score || '--'}</span></div>
        </div>
      </div>

      <div className="border-t border-panel-border/50 pt-2 mt-2">
        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2 font-semibold">Market Context</div>
        <div className="grid grid-cols-3 gap-2 text-[10px]">
          <div><span className="text-text-muted block">Regime</span><span className="text-text-primary font-medium">{sig.market_regime || '--'}</span></div>
          <div><span className="text-text-muted block">Volatility</span><span className="text-text-primary font-medium">{sig.volatility || '--'}</span></div>
          <div><span className="text-text-muted block">Trend</span><span className="text-text-primary font-medium">{sig.trend_strength || '--'}</span></div>
        </div>
      </div>

      <div className="border-t border-panel-border/50 pt-2 mt-2">
        <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2 font-semibold">Similar Historical Setups</div>
        {sig.historical_similars ? (
          <div className="grid grid-cols-3 gap-2 text-[10px] bg-trading-elevated/20 p-2 rounded-[var(--radius-md)]">
            <div><span className="text-text-muted block">Count</span><span className="text-text-primary font-medium">{sig.historical_similars.count || 0}</span></div>
            <div><span className="text-text-muted block">Win Rate</span><span className={`font-medium ${(sig.historical_similars.win_rate || 0) > 0.5 ? 'text-profit' : 'text-loss'}`}>{((sig.historical_similars.win_rate || 0) * 100).toFixed(0)}%</span></div>
            <div><span className="text-text-muted block">Best Strat</span><span className="text-accent-blue font-medium">{sig.historical_similars.best_strategy || '--'}</span></div>
          </div>
        ) : (
          <div className="text-[10px] text-text-muted">No historical data available</div>
        )}
      </div>
    </div>
  );
};

const AIValidationDetail: React.FC<{ ai: any }> = ({ ai }) => {
  if (!ai) return <div className="text-[10px] text-text-muted">No validation data</div>;
  const decisionColor = ai.decision === 'APPROVE' || ai.decision === 'INCREASE_CONFIDENCE' ? 'text-profit' :
    ai.decision === 'REDUCE_CONFIDENCE' ? 'text-warning' : 'text-loss';
  const decisionIcon = ai.decision === 'APPROVE' || ai.decision === 'INCREASE_CONFIDENCE' ? '✅' :
    ai.decision === 'REDUCE_CONFIDENCE' ? '⚠️' : '❌';
  return (
    <div className="flex flex-col gap-2 text-[10px]">
      <div className="flex items-center justify-between">
        <span className="text-lg font-bold" style={{ color: decisionColor.includes('profit') ? 'var(--color-profit)' : decisionColor.includes('warning') ? 'var(--color-warning)' : 'var(--color-loss)' }}>
          {decisionIcon} {ai.decision?.replace(/_/g, ' ')}
        </span>
        <span className="text-text-muted">Adj: {(ai.confidence_adjustment ?? 0) > 0 ? '+' : ''}{(ai.confidence_adjustment ?? 0)}</span>
      </div>
      <p className="text-text-secondary leading-relaxed">{ai.reasoning || '--'}</p>
      <div className="bg-trading-elevated/30 p-2 rounded-[var(--radius-md)]">
        <div className="text-text-muted uppercase tracking-wider mb-1">Risk Summary</div>
        <div className="text-text-primary">{ai.risk_summary || '--'}</div>
      </div>
      <div className="bg-trading-elevated/30 p-2 rounded-[var(--radius-md)]">
        <div className="text-text-muted uppercase tracking-wider mb-1">Alternative Scenario</div>
        <div className="text-text-primary">{ai.alternative_scenario || '--'}</div>
      </div>
    </div>
  );
};

const QualityBreakdown: React.FC<{ quality: any }> = ({ quality }) => {
  if (!quality || !quality.details) return <div className="text-[10px] text-text-muted">No quality data</div>;
  const d = quality.details;
  const breakdown = d.breakdown || {};
  const maxVal = Math.max(...Object.values(breakdown).map(v => typeof v === 'number' ? v : 0), 1);
  return (
    <div className="flex flex-col gap-2 text-[10px]">
      <div className="flex items-center justify-between">
        <span className={`text-lg font-bold ${QUALITY_COLORS[quality.grade]?.split(' ')[0] || 'text-text-primary'}`}>
          {quality.grade} · {quality.score}/100
        </span>
        <Badge variant={d.verdict === 'ACCEPT' ? 'profit' : 'loss'}>{d.verdict}</Badge>
      </div>
      <div className="space-y-1">
        {Object.entries(breakdown).map(([key, val]) => {
          const v = typeof val === 'number' ? val : 0;
          const pct = maxVal > 0 ? (v / maxVal) * 100 : 0;
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="w-24 text-text-muted capitalize">{key.replace(/_/g, ' ')}</span>
              <div className="flex-1 h-2 bg-trading-surface rounded-full overflow-hidden">
                <div className="h-full bg-accent-blue/60 rounded-full transition-all" style={{ width: `${pct}%` }} />
              </div>
              <span className="w-6 text-right text-text-primary font-medium">{v}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
