import React, { useEffect } from 'react';
import { KPICard } from '../components/core/KPICard';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { ShieldAlert, Gauge, TrendingDown, Activity, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api-client';

export const RiskPage: React.FC = () => {
  const riskMetrics = useAppStore((s) => s.riskMetrics);
  const portfolio = useAppStore((s) => s.portfolio);
  const refreshRisk = useAppStore((s) => s.refreshRisk);
  const [riskLimits, setRiskLimits] = React.useState<any[]>([]);
  const [stressResults, setStressResults] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await refreshRisk();
      try {
        const [limitsData] = await Promise.all([
          api.risk.limits(),
        ]);
        const limitsArr = Object.entries(limitsData).map(([k, v]: [string, any]) => ({
          name: k.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
          current: typeof v.current === 'number' ? `${v.current.toFixed(1)}${k.includes('loss') ? '%' : k.includes('leverage') ? 'x' : '%'}` : String(v.current),
          limit: typeof v.threshold === 'number' ? `${v.threshold}${k.includes('loss') ? '%' : k.includes('leverage') ? 'x' : '%'}` : String(v.threshold),
          ok: v.current <= v.threshold,
        }));
        setRiskLimits(limitsArr);
      } catch {}
      try {
        const scenarios = ['black_monday', 'flash_crash', 'bull_market'];
        const results = await Promise.all(
          scenarios.map((s) => api.risk.stressTest(s, 100000).catch(() => null))
        );
        setStressResults(results.filter(Boolean));
      } catch {}
      setLoading(false);
    };
    load();
    const interval = setInterval(refreshRisk, 15000);
    return () => clearInterval(interval);
  }, []);

  const rm = riskMetrics;

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Risk Management</h2>
        <button onClick={refreshRisk} className="p-1 text-text-muted hover:text-text-primary"><RefreshCw className="w-3.5 h-3.5" /></button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <KPICard label="Risk Score" value={`${rm?.riskScore ?? 0} / 100`} change={-(rm?.riskScore ?? 0)} icon={<ShieldAlert className="w-4 h-4" />} />
        <KPICard label="VaR (1D, 95%)" value={`$${(rm?.var1d || 0).toLocaleString()}`} icon={<Gauge className="w-4 h-4" />} />
        <KPICard label="Drawdown" value={`-${(portfolio?.drawdown || 0).toFixed(1)}%`} change={-(portfolio?.drawdown || 0)} icon={<TrendingDown className="w-4 h-4" />} />
        <KPICard label="Leverage" value={`${(rm?.leverage || 0).toFixed(1)}x`} icon={<Activity className="w-4 h-4" />} />
      </div>

      <div className="grid grid-cols-2 gap-3 flex-1 min-h-0">
        <Card title="Risk Limits">
          {loading ? (
            <div className="text-text-muted text-xs py-4 text-center">Loading...</div>
          ) : riskLimits.length === 0 ? (
            <div className="text-text-muted text-xs py-4 text-center">No risk limits configured. Start TradingView to populate limits.</div>
          ) : (
            <div className="flex flex-col gap-2">
              {riskLimits.map((l) => (
                <div key={l.name} className="flex items-center justify-between py-1">
                  <span className="text-[11px] text-text-secondary">{l.name}</span>
                  <div className="flex items-center gap-2">
                    <span data-mono className="text-[10px] text-text-primary">{l.current}</span>
                    <span className="text-[9px] text-text-muted">/ {l.limit}</span>
                    <Badge variant={l.ok ? 'profit' : 'warning'} dot>{l.ok ? 'OK' : 'WARN'}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Stress Scenarios">
          {stressResults.length === 0 ? (
            <div className="text-text-muted text-xs py-4 text-center">Run stress tests via the risk API</div>
          ) : (
            <div className="flex flex-col gap-2">
              {stressResults.map((s: any, i) => (
                <div key={i} className="flex items-center justify-between py-1">
                  <span className="text-[11px] text-text-secondary">{s.scenario?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</span>
                  <span data-mono className={`text-[11px] font-semibold ${s.drawdown >= 0 ? 'text-profit' : 'text-loss'}`}>
                    {s.drawdown >= 0 ? '+' : ''}{s.drawdown?.toFixed(1) ?? 0}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Exposure Summary">
          <div className="space-y-2 text-[11px]">
            <div className="flex justify-between"><span className="text-text-muted">Exposure Long</span><span data-mono className="text-profit">{rm?.exposureLong || 0}%</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Exposure Short</span><span data-mono className="text-loss">{rm?.exposureShort || 0}%</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Net Exposure</span><span data-mono className={rm?.exposureNet && rm.exposureNet >= 0 ? 'text-profit' : 'text-loss'}>{(rm?.exposureNet || 0) >= 0 ? '+' : ''}{rm?.exposureNet || 0}%</span></div>
          </div>
        </Card>

        <Card title="Risk Limits Status">
          <div className="flex flex-col gap-2 text-[11px]">
            <div className="flex justify-between"><span className="text-text-muted">Limits Configured</span><span data-mono>{riskLimits.length}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Breaches</span><span data-mono className="text-loss">{riskLimits.filter((l: any) => !l.ok).length}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Max Drawdown</span><span data-mono className="text-warning">-{(portfolio?.maxDrawdown || 0).toFixed(1)}%</span></div>
          </div>
        </Card>
      </div>
    </div>
  );
};