import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { Search, Filter, Newspaper, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export const NewsPage: React.FC = () => {
  const storeNews = useAppStore((s) => s.news);
  const refreshNews = useAppStore((s) => s.refreshNews);
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await refreshNews();
      setLoading(false);
    };
    load();
    const interval = setInterval(refreshNews, 30000);
    return () => clearInterval(interval);
  }, []);

  const displayNews = storeNews;

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-hidden bg-trading-dark">
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-accent-blue" /> Market Intelligence
        </h1>
        <div className="flex items-center gap-2">
          <button onClick={refreshNews} className="p-1 text-text-muted hover:text-text-primary"><RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /></button>
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="text" placeholder="Search news..." className="bg-trading-surface border border-panel-border rounded-[var(--radius-md)] pl-8 pr-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent-blue/50 w-64 transition-colors" />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto pr-1">
        {loading && displayNews.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-text-muted text-sm">Loading news...</div>
        ) : displayNews.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-text-muted text-sm border border-dashed border-panel-border/50 rounded-lg">
            No news items. News feed requires RSS or API providers to be configured.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {displayNews.map((item: any) => (
              <Card key={item.id} className="hover:border-accent-blue/30 transition-colors">
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-medium text-text-muted uppercase tracking-wider">{item.source}</span>
                      <span className="text-[10px] text-text-secondary">·</span>
                      <span className="text-[10px] text-text-secondary">{new Date(item.publishedAt || Date.now()).toLocaleTimeString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Badge variant={item.sentiment === 'bullish' ? 'profit' : item.sentiment === 'bearish' ? 'loss' : 'neutral'}>
                        {item.sentiment === 'bullish' && <TrendingUp className="w-3 h-3 mr-1" />}
                        {item.sentiment === 'bearish' && <TrendingDown className="w-3 h-3 mr-1" />}
                        {item.sentiment}
                      </Badge>
                      <Badge variant={item.impact === 'high' ? 'loss' : item.impact === 'medium' ? 'warning' : 'neutral'} dot>
                        {item.impact} impact
                      </Badge>
                    </div>
                  </div>
                  <h2 className="text-base font-semibold text-text-primary leading-tight">{item.title}</h2>
                  {item.summary && (
                    <div className="mt-2 p-3 bg-trading-surface rounded-[var(--radius-md)] border border-panel-border/50 border-l-2 border-l-accent-purple/50">
                      <div className="text-[10px] text-accent-purple font-medium uppercase tracking-widest mb-1.5">AI Analysis</div>
                      <p className="text-xs text-text-secondary leading-relaxed">{item.summary}</p>
                    </div>
                  )}
                  {item.affectedAssets && item.affectedAssets.length > 0 && (
                    <div className="flex gap-1.5 mt-1">
                      {item.affectedAssets.map((a: string) => (
                        <span key={a} className="px-1.5 py-0.5 bg-trading-surface border border-panel-border rounded text-[10px] text-text-muted">{a}</span>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};