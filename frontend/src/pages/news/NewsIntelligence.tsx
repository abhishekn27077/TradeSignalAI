import React, { useEffect, useState } from 'react';
import {
  Newspaper, RefreshCw, Filter, TrendingUp, TrendingDown, Minus,
  ExternalLink, Tag, AlertTriangle, Globe,
} from 'lucide-react';

const API_BASE = '/api/v1';

const CATEGORIES = [
  'ALL', 'CENTRAL_BANK', 'INFLATION', 'EMPLOYMENT', 'GDP',
  'GEOPOLITICAL', 'COMMODITY', 'EARNINGS', 'MARKET', 'RISK',
];

const SentimentBar: React.FC<{ score: number }> = ({ score }) => {
  const pct = ((score + 1) / 2) * 100; // -1..1 → 0..100
  const color = score > 0.2 ? 'bg-emerald-400' : score < -0.2 ? 'bg-red-400' : 'bg-slate-400';
  return (
    <div className="flex items-center gap-1.5 w-20">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-[10px] font-mono font-bold ${score > 0 ? 'text-emerald-400' : score < 0 ? 'text-red-400' : 'text-slate-400'}`}>
        {score > 0 ? '+' : ''}{score.toFixed(2)}
      </span>
    </div>
  );
};

const CategoryBadge: React.FC<{ category: string }> = ({ category }) => {
  const colors: Record<string, string> = {
    CENTRAL_BANK: 'bg-purple-500/15 text-purple-400',
    INFLATION: 'bg-red-500/15 text-red-400',
    EMPLOYMENT: 'bg-blue-500/15 text-blue-400',
    GDP: 'bg-green-500/15 text-green-400',
    GEOPOLITICAL: 'bg-orange-500/15 text-orange-400',
    COMMODITY: 'bg-amber-500/15 text-amber-400',
    EARNINGS: 'bg-cyan-500/15 text-cyan-400',
    MARKET: 'bg-slate-500/15 text-slate-400',
    RISK: 'bg-red-500/15 text-red-300',
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${colors[category] || colors.MARKET}`}>
      {category}
    </span>
  );
};

export const NewsIntelligence: React.FC = () => {
  const [articles, setArticles] = useState<any[]>([]);
  const [macroContext, setMacroContext] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('ALL');

  const load = async () => {
    setLoading(true);
    try {
      const cat = category === 'ALL' ? '' : `&category=${category}`;
      const res = await fetch(`${API_BASE}/news/intelligence?limit=50${cat}`);
      const json = await res.json();
      setArticles(json?.articles || []);
      setMacroContext(json?.macro_context || {});
    } catch { /* offline */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [category]);

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4" style={{ background: 'linear-gradient(135deg, #0a0e17 0%, #111827 50%, #0d1321 100%)' }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Newspaper className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">News Intelligence</h1>
            <p className="text-xs text-slate-400">AI-classified news with sentiment analysis & asset mapping</p>
          </div>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-300 hover:bg-slate-700/60 transition-colors">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Macro Context Bar */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-slate-900/60 border border-slate-800/50 rounded-lg p-3 text-center">
          <div className="text-lg font-bold text-white">{macroContext.total_articles || 0}</div>
          <div className="text-[10px] text-slate-500">Total Articles</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/50 rounded-lg p-3 text-center">
          <div className={`text-lg font-bold ${(macroContext.overall_sentiment || 0) > 0 ? 'text-emerald-400' : (macroContext.overall_sentiment || 0) < 0 ? 'text-red-400' : 'text-slate-300'}`}>
            {(macroContext.overall_sentiment || 0) > 0 ? '+' : ''}{(macroContext.overall_sentiment || 0).toFixed(3)}
          </div>
          <div className="text-[10px] text-slate-500">Overall Sentiment</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/50 rounded-lg p-3 text-center">
          <div className={`text-lg font-bold ${macroContext.overall_mood === 'RISK_ON' ? 'text-emerald-400' : macroContext.overall_mood === 'RISK_OFF' ? 'text-red-400' : 'text-amber-400'}`}>
            {macroContext.overall_mood || 'UNKNOWN'}
          </div>
          <div className="text-[10px] text-slate-500">Market Mood</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/50 rounded-lg p-3 text-center">
          <div className="text-lg font-bold text-amber-400">{macroContext.market_moving_count || 0}</div>
          <div className="text-[10px] text-slate-500">Market Moving</div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <Filter className="w-3.5 h-3.5 text-slate-500" />
        {CATEGORIES.map(c => (
          <button key={c} onClick={() => setCategory(c)}
            className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-colors ${
              category === c ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30' : 'bg-slate-800/40 text-slate-500 hover:text-slate-300 border border-transparent'
            }`}>
            {c.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Articles */}
      {loading && articles.length === 0 ? (
        <div className="flex items-center justify-center py-20 text-slate-500">
          <RefreshCw className="w-5 h-5 animate-spin mr-2" /> Loading intelligence…
        </div>
      ) : articles.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
          No news articles available
        </div>
      ) : (
        <div className="space-y-2">
          {articles.map((article: any, idx: number) => (
            <div key={idx}
              className="bg-slate-900/60 border border-slate-800/50 rounded-xl p-3 hover:border-slate-700/50 transition-colors">
              <div className="flex items-start gap-3">
                {/* Sentiment indicator */}
                <div className={`w-1 h-12 rounded-full flex-shrink-0 mt-0.5 ${
                  article.sentiment_score > 0.1 ? 'bg-emerald-400' : article.sentiment_score < -0.1 ? 'bg-red-400' : 'bg-slate-600'
                }`} />

                <div className="flex-1 min-w-0">
                  {/* Title + Source */}
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm text-white font-medium leading-tight line-clamp-2">
                      {article.original_title || 'Untitled'}
                    </h3>
                    {article.url && (
                      <a href={article.url} target="_blank" rel="noopener noreferrer"
                        className="text-slate-500 hover:text-blue-400 flex-shrink-0">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  {/* Meta Row */}
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <CategoryBadge category={article.category} />
                    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                      article.importance === 'HIGH' ? 'bg-red-500/15 text-red-400' :
                      article.importance === 'MEDIUM' ? 'bg-amber-500/15 text-amber-400' :
                      'bg-slate-700/50 text-slate-500'
                    }`}>
                      {article.importance}
                    </span>
                    <SentimentBar score={article.sentiment_score || 0} />
                    <span className="text-[10px] text-slate-500">{article.source}</span>
                    {article.is_market_moving && (
                      <span className="flex items-center gap-0.5 text-[10px] text-amber-400 font-medium">
                        <AlertTriangle className="w-2.5 h-2.5" /> MARKET MOVING
                      </span>
                    )}
                  </div>

                  {/* Affected Assets */}
                  {article.affected_assets?.length > 0 && (
                    <div className="flex items-center gap-1 mt-1.5">
                      <Tag className="w-3 h-3 text-slate-500" />
                      {article.affected_assets.map((asset: string) => (
                        <span key={asset} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/60 text-slate-400 font-medium">
                          {asset}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
