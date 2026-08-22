import React, { useEffect, useState } from 'react';
import { api } from '../../services/api-client';
import { Layers, Search, Code, CheckCircle, Activity } from 'lucide-react';

interface CoverageStats {
  symbols: Record<string, { timeframe: string; candle_count: number; has_features: boolean }[]>;
  total_with_features: number;
  total_datasets: number;
}

export const FeatureStorePage: React.FC = () => {
  const [coverage, setCoverage] = useState<CoverageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedTF, setSelectedTF] = useState<string>('');
  const [previewData, setPreviewData] = useState<any[]>([]);

  useEffect(() => {
    loadCoverage();
  }, []);

  const loadCoverage = async () => {
    try {
      setLoading(true);
      const res = await api.get<{coverage: CoverageStats}>('/data/features/coverage');
      setCoverage(res.coverage);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async (symbol: string, tf: string) => {
    setSelectedSymbol(symbol);
    setSelectedTF(tf);
    try {
      const res = await api.get<{data: any[]}>(`/data/features/${symbol}/${tf}?limit=5`);
      setPreviewData(res.data || []);
    } catch (e) {
      console.error(e);
      setPreviewData([]);
    }
  };

  const generateFeatures = async (symbol: string, tf: string) => {
    try {
      await api.post('/data/features/generate', { symbol, timeframe: tf });
      // In a real app, this would show a toast and wait for a websocket completion event
      alert(`Feature generation started for ${symbol} ${tf}`);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Layers className="text-accent-blue" />
            Feature Store
          </h1>
          <p className="text-text-secondary mt-1">
            Standardized technical indicator features for machine learning models
          </p>
        </div>
        <div className="px-4 py-2 bg-trading-surface border border-panel-border rounded-md text-sm">
          <span className="text-text-secondary">Coverage: </span>
          <span className="font-bold text-accent-cyan">
            {coverage ? `${Math.round((coverage.total_with_features / Math.max(coverage.total_datasets, 1)) * 100)}%` : '...'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Coverage List */}
        <div className="bg-trading-surface border border-panel-border rounded-lg p-6 flex flex-col">
          <h2 className="text-lg font-bold mb-4 flex items-center justify-between">
            Dataset Coverage
            <button onClick={loadCoverage} className="text-accent-blue hover:text-accent-blue/80">
              <Activity className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </h2>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            {coverage && Object.entries(coverage.symbols).map(([sym, tfs]) => (
              <div key={sym} className="bg-trading-elevated border border-panel-border-light rounded-md p-3">
                <h3 className="font-mono font-bold text-lg border-b border-panel-border/50 pb-2 mb-2">{sym}</h3>
                <div className="space-y-2">
                  {tfs.map(tf => (
                    <div key={tf.timeframe} className="flex items-center justify-between group">
                      <div className="flex items-center gap-2">
                        <span className="text-accent-gold font-medium w-8">{tf.timeframe}</span>
                        {tf.has_features ? (
                          <CheckCircle className="w-4 h-4 text-accent-green" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border border-panel-border bg-trading-dark" />
                        )}
                      </div>
                      <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={() => loadPreview(sym, tf.timeframe)}
                          className="text-xs px-2 py-1 bg-trading-surface hover:bg-trading-hover rounded border border-panel-border"
                        >
                          Preview
                        </button>
                        <button 
                          onClick={() => generateFeatures(sym, tf.timeframe)}
                          className="text-xs px-2 py-1 bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue rounded border border-accent-blue/30"
                        >
                          Generate
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Feature Preview */}
        <div className="col-span-2 bg-trading-surface border border-panel-border rounded-lg flex flex-col">
          <div className="p-4 border-b border-panel-border bg-trading-elevated flex items-center justify-between">
            <h2 className="font-bold flex items-center gap-2">
              <Code className="w-5 h-5 text-accent-purple" />
              Feature Vector Preview
            </h2>
            {selectedSymbol && selectedTF && (
              <span className="font-mono bg-trading-dark px-2 py-1 rounded border border-panel-border text-sm">
                {selectedSymbol} | {selectedTF}
              </span>
            )}
          </div>
          
          <div className="flex-1 p-0 overflow-hidden bg-[#0d1117]">
            {previewData.length > 0 ? (
              <div className="h-full overflow-auto p-4 font-mono text-xs text-[#c9d1d9]">
                <pre>
                  {JSON.stringify(previewData, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-text-muted">
                <Search className="w-12 h-12 mb-4 opacity-20" />
                <p>Select a dataset to preview its computed features</p>
                <p className="text-xs mt-2 max-w-md text-center">
                  Features include momentum (RSI, MACD), volatility (Bollinger Bands, ATR), and trend (EMAs) indicators ready for model consumption.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
