import React, { useEffect } from 'react';
import { Badge } from '../components/core/Badge';
import { BookOpen, Brain, TrendingUp, TrendingDown, Lightbulb, RefreshCw } from 'lucide-react';
import { api } from '../services/api-client';

export const JournalPage: React.FC = () => {
  const [entries, setEntries] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [replayTrade, setReplayTrade] = React.useState<string | null>(null);

  const fetchJournal = async () => {
    setLoading(true);
    try {
      const data = await api.journal.trades();
      const list = Array.isArray(data) ? data : (data as any)?.trades || [];
      setEntries(list);
    } catch {
      setEntries([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchJournal();
    const interval = setInterval(fetchJournal, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-accent-gold" />
          <h2 className="text-[16px] font-semibold text-text-primary">Trading Journal</h2>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchJournal} className="p-1 text-text-muted hover:text-text-primary"><RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /></button>
          <span className="text-[11px] text-text-muted">{entries.length} entries</span>
        </div>
      </div>

      {loading && entries.length === 0 ? (
        <div className="flex items-center justify-center h-32 text-text-muted text-sm">Loading trades...</div>
      ) : entries.length === 0 ? (
        <div className="flex items-center justify-center h-32 text-text-muted text-sm border border-dashed border-panel-border/50 rounded-lg">
          No trades recorded. Completed trades will appear here automatically.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {entries.map((entry: any) => (
            <div key={entry.id} className="bg-trading-surface border border-panel-border rounded-[var(--radius-lg)] overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-panel-border">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${(entry.pnl || 0) >= 0 ? 'bg-profit/15' : 'bg-loss/15'}`}>
                    {(entry.pnl || 0) >= 0 ? <TrendingUp className="w-4 h-4 text-profit" /> : <TrendingDown className="w-4 h-4 text-loss" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-semibold text-text-primary">{entry.symbol}</span>
                      <Badge variant={entry.direction === 'BUY' ? 'profit' : 'loss'}>{entry.direction}</Badge>
                    </div>
                    <span className="text-[10px] text-text-muted">{entry.opened_at ? new Date(entry.opened_at).toLocaleDateString() : ''} · {entry.closed_at ? new Date(entry.closed_at).toLocaleDateString() : ''}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div data-mono className={`text-[14px] font-bold ${(entry.pnl || 0) >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {(entry.pnl || 0) >= 0 ? '+' : ''}${(entry.pnl || 0).toLocaleString()}
                    </div>
                    <div className="text-[10px] text-text-muted">{entry.exit_reason || 'Closed'}</div>
                  </div>
                  <button onClick={() => setReplayTrade(replayTrade === entry.id ? null : entry.id)} className="px-3 py-1.5 bg-accent-blue/10 text-accent-blue rounded-[var(--radius-md)] text-[10px] font-semibold hover:bg-accent-blue/20 transition-colors flex items-center gap-1.5">
                    <Lightbulb className="w-3 h-3" />
                    {replayTrade === entry.id ? 'Close Replay' : 'Replay Trade'}
                  </button>
                </div>
              </div>
              
              {replayTrade === entry.id && (
                <div className="p-4 bg-trading-dark/50 border-b border-panel-border">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-[11px] font-semibold text-text-primary uppercase tracking-wider">Historical Trade Replay (Phase 7)</h4>
                    <div className="flex items-center gap-2">
                      <button className="px-2 py-1 bg-trading-surface border border-panel-border rounded text-[10px] hover:bg-trading-hover">⏪ Step Back</button>
                      <button className="px-2 py-1 bg-accent-blue text-white rounded text-[10px] hover:bg-accent-blue/90">▶ Play</button>
                      <button className="px-2 py-1 bg-trading-surface border border-panel-border rounded text-[10px] hover:bg-trading-hover">Step Fwd ⏩</button>
                    </div>
                  </div>
                  <div className="h-64 bg-trading-surface border border-panel-border rounded mb-3 flex items-center justify-center relative">
                    <span className="text-text-muted text-[10px]">Chart Replay View (Loading {entry.symbol} historical ticks...)</span>
                    <div className="absolute bottom-2 left-2 right-2 bg-trading-dark/80 backdrop-blur rounded p-2 border border-panel-border">
                      <div className="text-[10px] text-text-secondary flex justify-between">
                        <span>Time: {new Date(entry.opened_at).toLocaleString()}</span>
                        <span>Price: {entry.entry_price || '--'}</span>
                        <span className="text-accent-blue">Action: Executed {entry.direction}</span>
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-trading-surface p-2 rounded border border-panel-border">
                      <div className="text-[9px] text-text-muted uppercase mb-1">Entry Strategy</div>
                      <div className="text-[11px] text-text-primary">{entry.strategy || '--'}</div>
                    </div>
                    <div className="bg-trading-surface p-2 rounded border border-panel-border">
                      <div className="text-[9px] text-text-muted uppercase mb-1">Portfolio Snapshot (Phase 13)</div>
                      <div className="text-[11px] text-text-primary">Equity: ${(entry.portfolio_equity || 100000).toLocaleString()}</div>
                    </div>
                    <div className="bg-trading-surface p-2 rounded border border-panel-border">
                      <div className="text-[9px] text-text-muted uppercase mb-1">AI Reflection</div>
                      <div className="text-[11px] text-text-secondary">{entry.ai_reflection || 'Evaluating execution quality vs market movement...'}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};