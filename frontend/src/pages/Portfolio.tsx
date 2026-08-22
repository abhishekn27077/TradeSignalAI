import React, { useEffect } from 'react';
import { KPICard } from '../components/core/KPICard';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { useAppStore } from '../store/useAppStore';
import { DollarSign, TrendingUp, TrendingDown, PieChart, Wallet, RefreshCw } from 'lucide-react';
import { api } from '../services/api-client';

export const PortfolioPage: React.FC = () => {
  const storePortfolio = useAppStore((s) => s.portfolio);
  const storePositions = useAppStore((s) => s.positions);
  const refreshPositions = useAppStore((s) => s.refreshPositions);
  const refreshPortfolio = useAppStore((s) => s.refreshPortfolio);
  const [stats, setStats] = React.useState<any>(null);

  useEffect(() => {
    const load = async () => {
      await Promise.all([refreshPortfolio(), refreshPositions()]);
      try {
        const data = await api.analytics.performance();
        setStats(data);
      } catch {}
    };
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const displayPositions = storePositions;

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Portfolio Overview</h2>
        <button onClick={() => { refreshPortfolio(); refreshPositions(); }} className="p-1 text-text-muted hover:text-text-primary">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <KPICard label="Total Equity" value={`$${(storePortfolio.totalEquity || 0).toLocaleString()}`} icon={<Wallet className="w-4 h-4" />} />
        <KPICard label="Total P&L" value={`$${(storePortfolio.totalPnl || 0).toLocaleString()}`} change={storePortfolio.totalPnlPct} icon={<DollarSign className="w-4 h-4" />} />
        <KPICard label="Daily P&L" value={`$${(storePortfolio.dailyPnl || 0).toLocaleString()}`} change={storePortfolio.dailyPnlPct} icon={<TrendingUp className="w-4 h-4" />} />
        <KPICard label="Max Drawdown" value={`${(storePortfolio.maxDrawdown || 0).toFixed(1)}%`} change={-(storePortfolio.maxDrawdown || 0)} icon={<TrendingDown className="w-4 h-4" />} />
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-3 flex-1 min-h-0">
        <Card title="Open Positions" subtitle={`${displayPositions.length} active`} noPadding>
          {displayPositions.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-text-muted text-xs">No open positions</div>
          ) : (
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-text-muted text-[9px] uppercase tracking-wider border-b border-panel-border">
                  <th className="text-left px-3 py-2 font-medium">Symbol</th>
                  <th className="text-center px-3 py-2 font-medium">Side</th>
                  <th className="text-right px-3 py-2 font-medium">Qty</th>
                  <th className="text-right px-3 py-2 font-medium">Entry</th>
                  <th className="text-right px-3 py-2 font-medium">Current</th>
                  <th className="text-right px-3 py-2 font-medium">P&L</th>
                </tr>
              </thead>
              <tbody>
                {displayPositions.map((p: any) => (
                  <tr key={p.id || p.symbol} className="border-b border-panel-border/30 hover:bg-trading-hover transition-colors duration-100">
                    <td className="px-3 py-2 font-medium text-text-primary">{p.symbol}</td>
                    <td className="px-3 py-2 text-center"><Badge variant={p.direction === 'LONG' || p.direction === 'BUY' ? 'profit' : 'loss'}>{p.direction}</Badge></td>
                    <td data-mono className="px-3 py-2 text-right text-text-secondary">{p.quantity}</td>
                    <td data-mono className="px-3 py-2 text-right text-text-secondary">${(p.entryPrice || 0).toLocaleString()}</td>
                    <td data-mono className="px-3 py-2 text-right text-text-primary">${(p.currentPrice || 0).toLocaleString()}</td>
                    <td data-mono className={`px-3 py-2 text-right font-semibold ${(p.pnl || 0) >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {(p.pnl || 0) >= 0 ? '+' : ''}${(p.pnl || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="Performance Stats" action={<PieChart className="w-3.5 h-3.5 text-accent-cyan" />}>
          <div className="space-y-3 text-[11px]">
            <div className="flex justify-between"><span className="text-text-muted">Win Rate</span><span data-mono className="text-profit">{(stats?.win_rate || 0).toFixed(1)}%</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Profit Factor</span><span data-mono className="text-text-primary">{(stats?.profit_factor || 0).toFixed(2)}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Sharpe Ratio</span><span data-mono className="text-text-primary">{(stats?.sharpe_ratio || 0).toFixed(2)}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Total Trades</span><span data-mono className="text-text-primary">{stats?.total_trades || 0}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Net Profit</span><span data-mono className={(stats?.net_profit || 0) >= 0 ? 'text-profit' : 'text-loss'}>${(stats?.net_profit || 0).toLocaleString()}</span></div>
          </div>
        </Card>
      </div>
    </div>
  );
};