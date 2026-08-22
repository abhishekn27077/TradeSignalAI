import React, { useEffect, useState } from 'react';
import { api } from '../../services/api-client';
import { Database, Activity, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

interface Dataset {
  symbol: string;
  timeframe: string;
  candle_count: number;
  earliest: string | null;
  latest: string | null;
}

interface DBStats {
  total_symbols: number;
  total_candles: number;
  symbols_by_asset_class: Record<string, number>;
  datasets: Dataset[];
  providers: string[];
}

export const MarketDatabasePage: React.FC = () => {
  const [stats, setStats] = useState<DBStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.get<{stats: DBStats}>('/data/database');
      setStats(data.stats);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="text-accent-blue" />
            Market Database
          </h1>
          <p className="text-text-secondary mt-1">
            Enterprise historical market data storage and analytics
          </p>
        </div>
        <button 
          onClick={loadStats}
          className="px-4 py-2 bg-trading-elevated hover:bg-trading-hover rounded-md border border-panel-border transition-colors text-sm"
        >
          Refresh Stats
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Activity className="w-8 h-8 animate-spin text-accent-blue" />
        </div>
      ) : stats ? (
        <div className="space-y-6">
          {/* Top Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-trading-surface border border-panel-border rounded-lg p-5">
              <h3 className="text-text-muted text-sm font-medium">Total Symbols</h3>
              <p className="text-3xl font-bold mt-2">{stats.total_symbols}</p>
            </div>
            <div className="bg-trading-surface border border-panel-border rounded-lg p-5">
              <h3 className="text-text-muted text-sm font-medium">Total Candles</h3>
              <p className="text-3xl font-bold mt-2">{stats.total_candles.toLocaleString()}</p>
            </div>
            <div className="bg-trading-surface border border-panel-border rounded-lg p-5">
              <h3 className="text-text-muted text-sm font-medium">Data Providers</h3>
              <div className="flex gap-2 mt-3">
                {stats.providers?.map(p => (
                  <span key={p} className="px-2 py-1 bg-accent-blue/10 text-accent-blue rounded text-xs">
                    {p}
                  </span>
                ))}
              </div>
            </div>
            <div className="bg-trading-surface border border-panel-border rounded-lg p-5">
              <h3 className="text-text-muted text-sm font-medium">Database Status</h3>
              <div className="flex items-center gap-2 mt-3 text-accent-green">
                <CheckCircle className="w-5 h-5" />
                <span className="font-medium">Healthy</span>
              </div>
            </div>
          </div>

          {/* Asset Classes */}
          <div className="bg-trading-surface border border-panel-border rounded-lg p-6">
            <h2 className="text-lg font-bold mb-4">Coverage by Asset Class</h2>
            <div className="flex gap-6">
              {Object.entries(stats.symbols_by_asset_class || {}).map(([ac, count]) => (
                <div key={ac} className="flex-1 bg-trading-elevated p-4 rounded-md border border-panel-border-light text-center">
                  <h3 className="text-text-secondary capitalize text-sm">{ac}</h3>
                  <p className="text-2xl font-bold mt-1 text-accent-cyan">{count}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Datasets Table */}
          <div className="bg-trading-surface border border-panel-border rounded-lg overflow-hidden">
            <div className="p-4 border-b border-panel-border bg-trading-elevated">
              <h2 className="font-bold">Available Datasets</h2>
            </div>
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-trading-surface shadow-sm">
                  <tr className="text-text-muted border-b border-panel-border">
                    <th className="p-4 font-medium">Symbol</th>
                    <th className="p-4 font-medium">Timeframe</th>
                    <th className="p-4 font-medium text-right">Candles</th>
                    <th className="p-4 font-medium">Earliest Data</th>
                    <th className="p-4 font-medium">Latest Data</th>
                    <th className="p-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-panel-border">
                  {stats.datasets?.map((ds) => (
                    <tr key={`${ds.symbol}-${ds.timeframe}`} className="hover:bg-trading-hover/50">
                      <td className="p-4 font-mono font-medium text-text-primary">{ds.symbol}</td>
                      <td className="p-4 text-accent-gold">{ds.timeframe}</td>
                      <td className="p-4 text-right font-mono text-text-secondary">
                        {ds.candle_count.toLocaleString()}
                      </td>
                      <td className="p-4 text-text-secondary">
                        {ds.earliest ? new Date(ds.earliest).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="p-4 text-text-secondary">
                        {ds.latest ? new Date(ds.latest).toLocaleString() : 'N/A'}
                      </td>
                      <td className="p-4">
                        {ds.candle_count > 0 ? (
                          <span className="flex items-center gap-1.5 text-accent-green text-xs">
                            <CheckCircle className="w-3.5 h-3.5" /> Ready
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5 text-color-warning text-xs">
                            <AlertTriangle className="w-3.5 h-3.5" /> Empty
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {(!stats.datasets || stats.datasets.length === 0) && (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-text-muted">
                        No datasets found in database
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center text-text-muted mt-20">Failed to load database stats</div>
      )}
    </div>
  );
};
