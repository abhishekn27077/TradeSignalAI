import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { Search, BrainCircuit, History, Lightbulb, GitMerge, ShieldAlert, RefreshCw } from 'lucide-react';
import { api } from '../services/api-client';

export const MemoryPage: React.FC = () => {
  const [memories, setMemories] = React.useState<any[]>([]);
  const [stats, setStats] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [searchQuery, setSearchQuery] = React.useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [s] = await Promise.all([
        api.memory.statistics().catch(() => null),
      ]);
      setStats(s);
      if (searchQuery) {
        const results = await api.memory.search(searchQuery);
        setMemories(Array.isArray(results) ? results : []);
      } else {
        setMemories([]);
      }
    } catch {
      setMemories([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const results = await api.memory.search(searchQuery);
      setMemories(Array.isArray(results) ? results : []);
    } catch {
      setMemories([]);
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-y-auto bg-trading-dark min-h-full pb-16">
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-accent-purple" /> AI Long-Term Memory
        </h1>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-1 text-text-muted hover:text-text-primary"><RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /></button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-[1fr_350px] gap-3 min-h-0">
        <div className="flex flex-col gap-3 overflow-auto pr-1">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Semantic search through trade memory..."
              className="w-full bg-trading-surface border border-panel-border rounded-[var(--radius-md)] pl-8 pr-3 py-2 text-xs text-text-primary focus:outline-none focus:border-accent-purple/50 transition-colors"
            />
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-32 text-text-muted text-sm">Searching memory...</div>
          ) : memories.length === 0 && searchQuery ? (
            <div className="flex items-center justify-center h-32 text-text-muted text-sm border border-dashed border-panel-border/50 rounded-lg">No results found</div>
          ) : memories.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-text-muted text-sm border border-dashed border-panel-border/50 rounded-lg">
              Search trade memory using the search bar above. Memory is built automatically from completed trades.
            </div>
          ) : (
            memories.map((mem: any) => (
              <Card key={mem.id} className="hover:border-accent-purple/30 transition-colors">
                <div className="flex flex-col gap-3">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      {mem.type === 'trade_lesson' && <Lightbulb className="w-4 h-4 text-warning" />}
                      {mem.type === 'market_pattern' && <GitMerge className="w-4 h-4 text-accent-blue" />}
                      {mem.type === 'system_rule' && <ShieldAlert className="w-4 h-4 text-profit" />}
                      <h2 className="text-sm font-semibold text-text-primary">{mem.content?.title || mem.title || 'Memory'}</h2>
                    </div>
                    <Badge variant="accent" className="bg-accent-purple/10 text-accent-purple border-accent-purple/20 text-[9px] px-1.5 py-0">
                      {mem.confidence ? `${Math.round(mem.confidence * 100)}% match` : ''}
                    </Badge>
                  </div>
                  <p className="text-xs text-text-secondary leading-relaxed pl-6 border-l-2 border-panel-border">
                    {mem.content?.description || mem.content || mem.description || ''}
                  </p>
                  {mem.metadata?.tags && mem.metadata.tags.length > 0 && (
                    <div className="flex gap-1.5 pl-6">
                      {mem.metadata.tags.map((t: string) => (
                        <span key={t} className="px-1.5 py-0.5 bg-trading-surface border border-panel-border rounded text-[10px] text-text-muted">#{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>

        <div className="flex flex-col gap-3">
          <Card title="Memory Stats">
            {stats ? (
              <div className="space-y-2 text-[11px]">
                <div className="flex justify-between"><span className="text-text-muted">Total Records</span><span data-mono>{stats.total_memory_records}</span></div>
                <div className="flex justify-between"><span className="text-text-muted">Vector Dimensions</span><span data-mono>{stats.vector_dimensions}</span></div>
                <div className="flex justify-between"><span className="text-text-muted">Provider</span><span data-mono className="text-[9px]">{stats.provider}</span></div>
              </div>
            ) : (
              <div className="text-text-muted text-xs">Memory system initializing</div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};