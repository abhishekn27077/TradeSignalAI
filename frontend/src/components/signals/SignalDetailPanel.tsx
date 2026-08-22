import React, { useEffect, useState } from 'react';
import {
  X,
  TrendingUp,
  TrendingDown,
  Brain,
  Shield,
  Target,
  Clock,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Layers,
  FileText,
} from 'lucide-react';
import { api } from '../../services/api-client';
import { formatConfidence } from '../../utils/formatters';

interface SignalDetailPanelProps {
  signal: any;
  onClose: () => void;
}

type TabKey = 'details' | 'intelligence' | 'risk' | 'outcome' | 'trace';

export const SignalDetailPanel: React.FC<SignalDetailPanelProps> = ({ signal, onClose }) => {
  const [activeTab, setActiveTab] = useState<TabKey>('details');
  const [fullSignal, setFullSignal] = useState<any>(signal);
  const [loadingFull, setLoadingFull] = useState(false);

  const sig = fullSignal?.signal || fullSignal || {};
  const signalId = sig.signal_id || signal?.signal_id;

  useEffect(() => {
    if (!signalId) return;
    const fetchFull = async () => {
      setLoadingFull(true);
      try {
        const res = await api.signals.getById(signalId);
        if (res) {
          setFullSignal(res);
        }
      } catch (e) {
        console.warn('Failed to fetch complete signal record:', e);
      } finally {
        setLoadingFull(false);
      }
    };
    fetchFull();
  }, [signalId]);

  if (!sig) return null;

  const direction = sig.direction || sig.prediction?.expected_direction || 'WAIT';
  const isBuy = direction === 'BUY' || direction === 'LONG';
  const confidence = sig.confidence ?? sig.prediction?.confidence ?? 0;
  const symbol = sig.symbol || sig.asset || '—';
  const intel = sig.intelligence_snapshot || sig.intelligence || {};
  const outcome = sig.signal_state || sig.outcome || sig.status || 'OUTCOME_UNRESOLVED';

  const toIST = (ts: any) => {
    if (!ts) return '—';
    const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false });
  };

  const getOutcomeBadge = (st: string) => {
    switch (st) {
      case 'TP_HIT':
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-profit/15 text-profit border border-profit/30">
            <CheckCircle2 className="w-3 h-3" /> TP HIT
          </span>
        );
      case 'SL_HIT':
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-loss/15 text-loss border border-loss/30">
            <XCircle className="w-3 h-3" /> SL HIT
          </span>
        );
      case 'TIME_EXIT':
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-accent-blue/15 text-accent-blue border border-accent-blue/30">
            <Clock className="w-3 h-3" /> TIME EXIT
          </span>
        );
      case 'AMBIGUOUS':
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-warning/15 text-warning border border-warning/30">
            <AlertTriangle className="w-3 h-3" /> AMBIGUOUS
          </span>
        );
      case 'EXPIRED':
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-text-muted/15 text-text-muted border border-text-muted/30">
            <Clock className="w-3 h-3" /> EXPIRED
          </span>
        );
      case 'ACTIVE':
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-accent-gold/15 text-accent-gold border border-accent-gold/30">
            <Activity className="w-3 h-3 animate-pulse" /> ACTIVE
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-trading-elevated text-text-secondary border border-panel-border">
            <HelpCircle className="w-3 h-3" /> {st}
          </span>
        );
    }
  };

  const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    { key: 'details', label: 'Details', icon: <FileText className="w-3.5 h-3.5" /> },
    { key: 'intelligence', label: 'Intelligence', icon: <Brain className="w-3.5 h-3.5" /> },
    { key: 'risk', label: 'Risk Trace', icon: <Shield className="w-3.5 h-3.5" /> },
    { key: 'outcome', label: 'Outcome & P&L', icon: <Target className="w-3.5 h-3.5" /> },
    { key: 'trace', label: 'Audit Trace', icon: <Layers className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-xs" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-lg h-full bg-trading-surface border-l border-panel-border flex flex-col shadow-2xl overflow-hidden z-10 animate-in slide-in-from-right duration-200">
        {/* Top Header */}
        <div className={`shrink-0 px-5 py-4 border-b border-panel-border flex items-center justify-between ${isBuy ? 'bg-profit/5' : 'bg-loss/5'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${isBuy ? 'bg-profit/15 text-profit' : 'bg-loss/15 text-loss'}`}>
              {isBuy ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-text-primary">{symbol}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${isBuy ? 'badge-buy' : 'badge-sell'}`}>
                  {direction}
                </span>
                <span className="text-[10px] font-mono bg-trading-elevated text-text-muted px-1.5 py-0.5 rounded">
                  {sig.timeframe || 'H4'}
                </span>
              </div>
              <div className="text-[11px] text-text-muted mt-0.5">
                ID: <span className="font-mono text-text-secondary">{sig.signal_id || '—'}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {getOutcomeBadge(outcome)}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-trading-hover text-text-muted hover:text-text-primary transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="shrink-0 flex border-b border-panel-border bg-trading-dark px-3 pt-2 gap-1 overflow-x-auto">
          {tabs.map((t) => {
            const active = activeTab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium rounded-t-lg transition-colors border-b-2 ${
                  active
                    ? 'border-accent-blue text-accent-blue bg-trading-surface font-semibold'
                    : 'border-transparent text-text-muted hover:text-text-primary hover:bg-trading-hover/40'
                }`}
              >
                {t.icon}
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* TAB 1: DETAILS */}
          {activeTab === 'details' && (
            <div className="space-y-4">
              {/* Confidence Meter */}
              <div className="bg-trading-dark p-3.5 rounded-xl border border-panel-border/60">
                <div className="flex justify-between items-center mb-1.5 text-xs">
                  <span className="text-text-muted">AI Calibration Confidence</span>
                  <span className="text-text-primary font-bold font-mono">{formatConfidence(confidence)}</span>
                </div>
                <div className="h-2 bg-trading-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-accent-blue to-accent-gold rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(Math.max((confidence || 0) * 100, 0), 100)}%` }}
                  />
                </div>
              </div>

              {/* Core Key-Value Matrix */}
              <div className="bg-trading-dark rounded-xl border border-panel-border/60 divide-y divide-panel-border/40 text-xs">
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Generated Time (IST)</span>
                  <span className="text-text-primary font-mono">{toIST(sig.created_at || sig.prediction_timestamp || sig.timestamp)}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Entry Price</span>
                  <span className="text-text-primary font-mono font-semibold">{sig.entry_price ?? sig.current_price ?? '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Stop Loss</span>
                  <span className="text-loss font-mono font-semibold">{sig.stop_loss ?? '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Take Profit 1</span>
                  <span className="text-profit font-mono font-semibold">{sig.take_profit_1 ?? sig.take_profit ?? '—'}</span>
                </div>
                {sig.take_profit_2 && (
                  <div className="flex justify-between px-4 py-2.5">
                    <span className="text-text-muted">Take Profit 2</span>
                    <span className="text-profit font-mono">{sig.take_profit_2}</span>
                  </div>
                )}
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Risk : Reward</span>
                  <span className="text-text-primary font-mono font-semibold">{sig.risk_reward ? `1 : ${sig.risk_reward}` : '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Trade Grade</span>
                  <span className="text-accent-gold font-bold">{sig.trade_quality || '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Strategy Name</span>
                  <span className="text-text-primary font-mono">{sig.strategy_name || '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Expected Holding Time</span>
                  <span className="text-text-primary font-mono">{sig.expected_holding_time ? `${sig.expected_holding_time} hours` : '—'}</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: INTELLIGENCE */}
          {activeTab === 'intelligence' && (
            <div className="space-y-4">
              {/* Quant Baseline & Kronos */}
              <div className="bg-trading-dark p-4 rounded-xl border border-panel-border/60 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-text-primary uppercase tracking-wider">
                  <Brain className="w-4 h-4 text-accent-blue" />
                  <span>Model Agreement & Quant Baseline</span>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="bg-trading-surface p-3 rounded-lg border border-panel-border/40">
                    <div className="text-[10px] text-text-muted uppercase">Consensus Pct</div>
                    <div className="text-sm font-bold font-mono text-text-primary mt-0.5">
                      {sig.consensus_pct !== undefined && sig.consensus_pct !== null ? `${(sig.consensus_pct * 100).toFixed(1)}%` : (sig.quant_baseline?.agreement_percentage ? `${sig.quant_baseline.agreement_percentage.toFixed(1)}%` : '—')}
                    </div>
                  </div>
                  <div className="bg-trading-surface p-3 rounded-lg border border-panel-border/40">
                    <div className="text-[10px] text-text-muted uppercase">Market Regime</div>
                    <div className="text-sm font-bold text-accent-gold mt-0.5">
                      {sig.market_regime || sig.market_trend || intel.market_regime || '—'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Intelligence Snapshot Breakdown */}
              <div className="bg-trading-dark p-4 rounded-xl border border-panel-border/60 space-y-2.5 text-xs">
                <div className="font-bold text-text-primary text-[11px] uppercase tracking-wider mb-2">Contextual Intelligence Inputs</div>
                
                <div className="flex justify-between py-1.5 border-b border-panel-border/40">
                  <span className="text-text-muted">Kronos Pattern Mini</span>
                  <span className="text-text-primary font-mono">{intel.kronos_score ?? intel.kronos ?? 'Available'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-panel-border/40">
                  <span className="text-text-muted">FAISS Similarity Matches</span>
                  <span className="text-text-primary font-mono">{intel.faiss_matches_count ?? intel.similar_patterns ?? sig.similar_trades ?? '—'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-panel-border/40">
                  <span className="text-text-muted">News Sentiment</span>
                  <span className="text-text-primary font-medium">{intel.news_sentiment ?? intel.news ?? 'Neutral'}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-panel-border/40">
                  <span className="text-text-muted">Event Risk</span>
                  <span className="text-text-primary font-medium">{intel.event_risk ?? 'Low / Standard'}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-text-muted">Macro Context</span>
                  <span className="text-text-primary font-medium">{intel.macro_context ?? 'Normal Liquidity'}</span>
                </div>
              </div>

              {/* Models Used */}
              {Array.isArray(sig.ai_models_used) && sig.ai_models_used.length > 0 && (
                <div className="bg-trading-dark p-4 rounded-xl border border-panel-border/60 space-y-2">
                  <div className="text-[11px] font-bold text-text-primary uppercase tracking-wider">Models in Consensus</div>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {sig.ai_models_used.map((m: string, i: number) => (
                      <span key={i} className="text-[10px] font-mono bg-trading-surface px-2.5 py-1 rounded border border-panel-border text-text-secondary">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: RISK TRACE */}
          {activeTab === 'risk' && (
            <div className="space-y-4">
              <div className="bg-trading-dark p-4 rounded-xl border border-panel-border/60 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-text-primary uppercase tracking-wider">
                  <Shield className="w-4 h-4 text-accent-gold" />
                  <span>Risk Decision & Validation</span>
                </div>

                <div className="flex justify-between items-center bg-trading-surface p-3 rounded-lg border border-panel-border/40">
                  <span className="text-xs text-text-muted">Execution Gate Decision</span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-accent-blue/15 text-accent-blue">
                    {sig.status === 'ACTIVE' || sig.status === 'COMPLETED' ? 'APPROVED' : (sig.status || 'NO_TRADE')}
                  </span>
                </div>

                {sig.reasoning && (
                  <div className="bg-trading-surface p-3 rounded-lg border border-panel-border/40">
                    <div className="text-[10px] text-text-muted uppercase mb-1">Signal Reasoning</div>
                    <p className="text-xs text-text-primary leading-relaxed font-sans">{sig.reasoning}</p>
                  </div>
                )}

                {sig.ai_explanation && (
                  <div className="bg-trading-surface p-3 rounded-lg border border-panel-border/40">
                    <div className="text-[10px] text-text-muted uppercase mb-1">AI Explanation</div>
                    <p className="text-xs text-text-secondary italic leading-relaxed font-sans">{sig.ai_explanation}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: OUTCOME & P&L */}
          {activeTab === 'outcome' && (
            <div className="space-y-4">
              {/* Outcome Status Banner */}
              <div className="bg-trading-dark p-4 rounded-xl border border-panel-border/60 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-text-muted">Resolution State</span>
                  {getOutcomeBadge(outcome)}
                </div>

                {/* Net P&L Highlight Card */}
                <div className={`p-4 rounded-xl border text-center ${
                  sig.net_pnl !== null && sig.net_pnl !== undefined
                    ? sig.net_pnl > 0
                      ? 'bg-profit/10 border-profit/30'
                      : sig.net_pnl < 0
                      ? 'bg-loss/10 border-loss/30'
                      : 'bg-trading-surface border-panel-border'
                    : 'bg-trading-surface border-panel-border'
                }`}>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">Net P&L (After Costs)</div>
                  <div className={`text-xl font-bold font-mono mt-1 ${
                    sig.net_pnl !== null && sig.net_pnl !== undefined
                      ? sig.net_pnl > 0
                        ? 'text-profit'
                        : sig.net_pnl < 0
                        ? 'text-loss'
                        : 'text-text-primary'
                      : 'text-text-muted'
                  }`}>
                    {sig.net_pnl !== null && sig.net_pnl !== undefined
                      ? `${sig.net_pnl >= 0 ? '+' : ''}${sig.net_pnl.toFixed(2)} USD`
                      : 'Pending Resolution'}
                  </div>
                  {sig.r_multiple !== null && sig.r_multiple !== undefined && (
                    <div className="text-[11px] text-text-secondary font-mono mt-0.5">
                      R-Multiple: <span className="font-bold">{sig.r_multiple >= 0 ? `+${sig.r_multiple.toFixed(2)}R` : `${sig.r_multiple.toFixed(2)}R`}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Exact Cost & Execution Breakdown */}
              <div className="bg-trading-dark rounded-xl border border-panel-border/60 divide-y divide-panel-border/40 text-xs">
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Exit Price</span>
                  <span className="text-text-primary font-mono font-semibold">{sig.exit_price ?? '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Exit Time (IST)</span>
                  <span className="text-text-primary font-mono">{toIST(sig.exit_time || sig.closed_at)}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Gross Move P&L</span>
                  <span className="text-text-primary font-mono">{sig.gross_pnl !== null && sig.gross_pnl !== undefined ? `${sig.gross_pnl >= 0 ? '+' : ''}${sig.gross_pnl.toFixed(2)}` : '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Spread Cost (Deducted)</span>
                  <span className="text-loss font-mono">{sig.spread_cost !== null && sig.spread_cost !== undefined ? `-${sig.spread_cost.toFixed(2)}` : '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Slippage Cost (Deducted)</span>
                  <span className="text-loss font-mono">{sig.slippage_cost !== null && sig.slippage_cost !== undefined ? `-${sig.slippage_cost.toFixed(2)}` : '—'}</span>
                </div>
                <div className="flex justify-between px-4 py-2.5">
                  <span className="text-text-muted">Broker Fees (Deducted)</span>
                  <span className="text-loss font-mono">{sig.fees_cost !== null && sig.fees_cost !== undefined ? `-${sig.fees_cost.toFixed(2)}` : '—'}</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: AUDIT TRACE */}
          {activeTab === 'trace' && (
            <div className="space-y-4">
              <div className="bg-trading-dark p-4 rounded-xl border border-panel-border/60 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-text-primary uppercase tracking-wider">
                  <Layers className="w-4 h-4 text-accent-blue" />
                  <span>Immutable Audit Ledger</span>
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <div className="text-[10px] text-text-muted uppercase">Signal ID</div>
                    <div className="font-mono text-text-primary text-[11px] break-all bg-trading-surface p-2 rounded border border-panel-border/40 mt-1">
                      {sig.signal_id || '—'}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-text-muted uppercase">Trace ID (Correlation)</div>
                    <div className="font-mono text-text-primary text-[11px] break-all bg-trading-surface p-2 rounded border border-panel-border/40 mt-1">
                      {sig.trace_id || '—'}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-text-muted uppercase">Duplicate Protection Hash (SHA-256)</div>
                    <div className="font-mono text-text-secondary text-[10px] break-all bg-trading-surface p-2 rounded border border-panel-border/40 mt-1">
                      {sig.duplicate_protection_hash || '—'}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <div className="bg-trading-surface p-2.5 rounded border border-panel-border/40">
                      <div className="text-[10px] text-text-muted uppercase">Candle Timestamp</div>
                      <div className="font-mono text-[11px] text-text-primary mt-0.5">{toIST(sig.candle_timestamp)}</div>
                    </div>
                    <div className="bg-trading-surface p-2.5 rounded border border-panel-border/40">
                      <div className="text-[10px] text-text-muted uppercase">Data Freshness</div>
                      <div className="font-mono text-[11px] text-profit mt-0.5">{sig.data_freshness_status || 'FRESH'}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
