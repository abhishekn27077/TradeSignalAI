import React, { useEffect, useState } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { Button } from '../components/core/Button';
import { KPICard } from '../components/core/KPICard';
import {
  Play, Square, Settings2, Activity, TrendingUp, AlertTriangle,
  ShieldCheck, RefreshCw, Pause, ChevronDown, BarChart3, Zap,
  Target, Eye, EyeOff, Sliders, Cpu,
} from 'lucide-react';
import { api } from '../services/api-client';
import type { StrategyConfig, StrategyAnalytics, OptimizerRecommendation } from '../types';

export const StrategiesPage: React.FC = () => {
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [analytics, setAnalytics] = useState<Record<string, StrategyAnalytics>>({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null);
  const [editConfig, setEditConfig] = useState<any>({});
  const [optimizing, setOptimizing] = useState<string | null>(null);
  const [optimizations, setOptimizations] = useState<Record<string, OptimizerRecommendation>>({});

  const load = async () => {
    setLoading(true);
    try {
      const s = await api.strategies.list();
      setStrategies(s || []);
      const aMap: Record<string, StrategyAnalytics> = {};
      for (const strat of s || []) {
        try {
          const a = await api.strategies.analytics(strat.name);
          if (a) aMap[strat.name] = a;
        } catch {}
      }
      setAnalytics(aMap);
    } catch (err) {
      console.error('Failed to load strategies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); const i = setInterval(load, 30000); return () => clearInterval(i); }, []);

  const doEnable = async (name: string) => { await api.strategies.enable(name); load(); };
  const doDisable = async (name: string) => { await api.strategies.disable(name); load(); };
  const doPause = async (name: string) => { await api.strategies.pause(name); load(); };
  const doResume = async (name: string) => { await api.strategies.resume(name); load(); };

  const startEdit = (s: StrategyConfig) => {
    setEditing(s.name);
    setEditConfig({
      priority: s.priority,
      weight: s.weight,
      max_concurrent_trades: s.max_concurrent_trades,
      daily_trade_limit: s.daily_trade_limit,
      min_trade_quality: s.min_trade_quality,
      min_ai_confidence: s.min_ai_confidence,
    });
  };

  const saveConfig = async (name: string) => {
    await api.strategies.config(name, editConfig);
    setEditing(null);
    load();
  };

  const runOptimize = async (name: string) => {
    setOptimizing(name);
    try {
      const r = await api.strategies.optimize(name);
      setOptimizations(prev => ({ ...prev, [name]: r }));
    } catch {}
    setOptimizing(null);
  };

  const activeCount = strategies.filter(s => s.status === 'ENABLED').length;
  const pausedCount = strategies.filter(s => s.status === 'PAUSED').length;
  const totalPnl = Object.values(analytics).reduce((sum, a) => sum + (a.total_pnl || 0), 0);

  const statusBadge = (status: string) => {
    if (status === 'ENABLED') return <Badge variant="profit" dot>ON</Badge>;
    if (status === 'PAUSED') return <Badge variant="warning" dot>PAUSED</Badge>;
    return <Badge variant="neutral" dot>OFF</Badge>;
  };

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-y-auto bg-trading-dark min-h-full pb-16">
      <div className="flex items-center justify-between shrink-0">
        <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <Cpu className="w-4 h-4 text-accent-blue" /> Strategy Center
        </h2>
        <button onClick={load} className="p-1 text-text-muted hover:text-text-primary">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-5 gap-3 shrink-0">
        <KPICard label="Active" value={activeCount.toString()} icon={<Activity className="w-4 h-4 text-profit" />} />
        <KPICard label="Paused" value={pausedCount.toString()} icon={<Pause className="w-4 h-4 text-warning" />} />
        <KPICard label="Total" value={strategies.length.toString()} icon={<TrendingUp className="w-4 h-4 text-accent-blue" />} />
        <KPICard label="Total PnL" value={`$${totalPnl.toFixed(0)}`} icon={<BarChart3 className="w-4 h-4 text-profit" />} />
        <KPICard label="Optimizations" value={Object.keys(optimizations).length.toString()} icon={<Zap className="w-4 h-4 text-warning" />} />
      </div>

      <div className="flex-1 overflow-auto">
        {loading && strategies.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-text-muted text-sm">Loading strategies...</div>
        ) : strategies.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-text-muted text-sm border border-dashed border-panel-border rounded-lg">
            No strategies loaded. Configure strategies in the backend.
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            {strategies.map((strat) => {
              const a = analytics[strat.name];
              const opt = optimizations[strat.name];
              const isEditing = editing === strat.name;
              return (
                <Card key={strat.name} title={strat.name} subtitle={`v${strat.version} · ${strat.category}`}
                  action={statusBadge(strat.status)}
                >
                  <div className="flex flex-col gap-3">
                    <p className="text-[11px] text-text-secondary leading-relaxed">{strat.description}</p>

                    <div className="grid grid-cols-4 gap-2 bg-trading-elevated/50 p-2.5 rounded-[var(--radius-md)] border border-panel-border/30">
                      <div>
                        <div className="text-[10px] text-text-muted mb-1 uppercase tracking-wider">Win Rate</div>
                        <div className="text-sm font-medium text-profit">{a?.win_rate ?? 0}%</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-text-muted mb-1 uppercase tracking-wider">Profit Factor</div>
                        <div className="text-sm font-medium text-text-primary">{a?.profit_factor ?? 0}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-text-muted mb-1 uppercase tracking-wider">Drawdown</div>
                        <div className="text-sm font-medium text-loss">-{a?.max_drawdown_pct ?? 0}%</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-text-muted mb-1 uppercase tracking-wider">Trades</div>
                        <div className="text-sm font-medium text-text-secondary">{a?.total_trades ?? 0}</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-text-muted">
                      <div className="flex items-center gap-3">
                        <span>Priority: <span className="text-text-primary font-medium">{strat.priority}</span></span>
                        <span>Weight: <span className="text-text-primary font-medium">{strat.weight}x</span></span>
                        <span>Max Trades: <span className="text-text-primary font-medium">{strat.max_concurrent_trades}</span></span>
                        <span>Daily Limit: <span className="text-text-primary font-medium">{strat.daily_trade_limit}</span></span>
                      </div>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        strat.risk_profile === 'Low' || strat.risk_profile === 'Very Low' ? 'text-profit bg-profit/10' :
                        strat.risk_profile === 'High' || strat.risk_profile === 'Very High' ? 'text-loss bg-loss/10' :
                        'text-warning bg-warning/10'
                      }`}>{strat.risk_profile}</span>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {strat.supported_timeframes.map(tf => (
                        <span key={tf} className="px-1.5 py-0.5 bg-trading-surface border border-panel-border rounded text-[10px] text-text-secondary">{tf}</span>
                      ))}
                      {strat.required_indicators.map(ind => (
                        <span key={ind} className="px-1.5 py-0.5 bg-accent-blue/5 border border-accent-blue/20 rounded text-[10px] text-accent-blue">{ind}</span>
                      ))}
                    </div>

                    {strat.last_signal && (
                      <div className="flex items-center gap-2 text-[10px] bg-trading-elevated/30 p-2 rounded-[var(--radius-md)] border border-panel-border/20">
                        <Zap className="w-3 h-3 text-warning" />
                        <span className="text-text-muted">Last Signal:</span>
                        <span className={`font-medium ${strat.last_signal.direction === 'BUY' ? 'text-profit' : 'text-loss'}`}>
                          {strat.last_signal.direction}
                        </span>
                        <span className="text-text-secondary">{strat.last_signal.symbol || strat.last_signal.asset}</span>
                        <span className="text-text-muted">Conf: {((strat.last_signal.confidence || 0) * 100).toFixed(0)}%</span>
                      </div>
                    )}

                    {isEditing ? (
                      <div className="bg-trading-elevated/50 p-2.5 rounded-[var(--radius-md)] border border-accent-blue/30 space-y-2">
                        <div className="grid grid-cols-3 gap-2 text-[10px]">
                          {['priority', 'weight', 'max_concurrent_trades', 'daily_trade_limit', 'min_trade_quality', 'min_ai_confidence'].map(f => (
                            <div key={f}>
                              <label className="text-text-muted uppercase tracking-wider block mb-0.5">{f.replace(/_/g, ' ')}</label>
                              <input
                                type="number"
                                step={f === 'weight' || f === 'min_ai_confidence' ? 0.1 : 1}
                                className="w-full bg-trading-surface border border-panel-border rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:border-accent-blue/50"
                                value={(editConfig as any)[f] ?? ''}
                                onChange={e => setEditConfig({ ...editConfig, [f]: parseFloat(e.target.value) || 0 })}
                              />
                            </div>
                          ))}
                        </div>
                        <div className="flex gap-2 justify-end">
                          <Button variant="ghost" size="sm" onClick={() => setEditing(null)}>Cancel</Button>
                          <Button variant="primary" size="sm" onClick={() => saveConfig(strat.name)}>Save</Button>
                        </div>
                      </div>
                    ) : null}

                    {opt ? (
                      <div className="bg-trading-elevated/30 p-2 rounded-[var(--radius-md)] border border-warning/20">
                        <div className="flex items-center gap-1 mb-1">
                          <Zap className="w-3 h-3 text-warning" />
                          <span className="text-[10px] font-medium text-warning uppercase">Optimization</span>
                          <Badge variant={opt.urgency === 'HIGH' ? 'loss' : opt.urgency === 'MEDIUM' ? 'warning' : 'neutral'}>
                            {opt.urgency}
                          </Badge>
                        </div>
                        <ul className="text-[10px] text-text-secondary space-y-0.5 ml-4 list-disc">
                          {opt.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                        </ul>
                      </div>
                    ) : null}

                    <div className="flex items-center justify-between pt-2 border-t border-panel-border/50">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" className="h-7 text-[10px]" onClick={() => startEdit(strat)}>
                          <Sliders className="w-3 h-3 mr-1" /> Config
                        </Button>
                        <Button variant="ghost" size="sm" className="h-7 text-[10px]" onClick={() => runOptimize(strat.name)} disabled={optimizing === strat.name}>
                          <Zap className="w-3 h-3 mr-1" /> {optimizing === strat.name ? '...' : 'Optimize'}
                        </Button>
                      </div>
                      <div className="flex items-center gap-1">
                        {strat.status === 'ENABLED' ? (
                          <>
                            <Button variant="ghost" size="sm" className="h-7 text-[10px]" onClick={() => doPause(strat.name)}>
                              <Pause className="w-3 h-3 mr-1" /> Pause
                            </Button>
                            <Button variant="danger" size="sm" className="h-7 text-[10px]" onClick={() => doDisable(strat.name)}>
                              <Square className="w-3 h-3 mr-1" /> Disable
                            </Button>
                          </>
                        ) : strat.status === 'PAUSED' ? (
                          <>
                            <Button variant="buy" size="sm" className="h-7 text-[10px]" onClick={() => doResume(strat.name)}>
                              <Play className="w-3 h-3 mr-1" /> Resume
                            </Button>
                            <Button variant="danger" size="sm" className="h-7 text-[10px]" onClick={() => doDisable(strat.name)}>
                              <Square className="w-3 h-3 mr-1" /> Disable
                            </Button>
                          </>
                        ) : (
                          <Button variant="buy" size="sm" className="h-7 text-[10px]" onClick={() => doEnable(strat.name)}>
                            <Play className="w-3 h-3 mr-1" /> Enable
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
