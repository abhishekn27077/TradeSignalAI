import React, { useEffect, useState } from 'react';
import { api } from '../../services/api-client';

export const SwingScanner: React.FC = () => {
  const [forecasts, setForecasts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchForecasts = async () => {
      try {
        const data = await api.forecasts.history(50);
        // Filter for D1 or 1W
        setForecasts(data.filter(d => ['D1', '1W', '1D'].includes(d.timeframe?.toUpperCase())));
      } catch (err) {
        console.error('Failed to fetch swing forecasts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchForecasts();
  }, []);

  return (
    <div className="p-6 h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Swing Scanner</h1>
      <p className="text-text-secondary mb-4">Real-time scan for high-confidence multi-day setups.</p>
      
      <div className="bg-trading-surface border border-panel-border rounded-lg p-6 flex-grow">
        {loading ? (
          <p>Loading forecasts...</p>
        ) : forecasts.length === 0 ? (
          <p className="text-text-secondary">No Swing forecasts available.</p>
        ) : (
          <div className="space-y-4">
            {forecasts.map(f => (
              <div key={f.id} className={`border-l-4 p-4 rounded bg-trading-hover ${f.consensus?.direction === 'BUY' ? 'border-accent-blue' : f.consensus?.direction === 'SELL' ? 'border-accent-red' : 'border-gray-500'}`}>
                <h3 className="font-bold">{new Date(f.created_at).toLocaleString()} - {f.symbol} ({f.timeframe})</h3>
                <p className="text-sm mt-1">
                  Direction: {f.consensus?.direction || 'Not Available'} | 
                  Confidence: {f.consensus?.confidence ? `${(f.consensus.confidence * 100).toFixed(1)}%` : 'Not Available'} | 
                  Grade: {f.consensus?.grade || 'Not Available'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
