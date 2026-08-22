import React, { useEffect, useState } from 'react';
import { api } from '../../services/api-client';

export const H4ForecastsPage: React.FC = () => {
  const [forecasts, setForecasts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchForecasts = async () => {
      try {
        const data = await api.forecasts.history(50);
        // Filter for H4
        setForecasts(data.filter(d => d.timeframe?.toUpperCase() === '4H'));
      } catch (err) {
        console.error('Failed to fetch H4 forecasts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchForecasts();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">H4 Forecasts</h1>
      <div className="bg-trading-surface border border-panel-border rounded-lg p-6">
        <p className="text-text-secondary mb-4">Automatically generated forecasts at every H4 candle open.</p>
        
        {loading ? (
          <p>Loading forecasts...</p>
        ) : forecasts.length === 0 ? (
          <p className="text-text-secondary">No H4 forecasts available.</p>
        ) : (
          <div className="space-y-4">
            {forecasts.map(f => (
              <div key={f.id} className={`border-l-4 p-4 rounded bg-trading-hover ${f.consensus?.direction === 'BUY' ? 'border-accent-blue' : f.consensus?.direction === 'SELL' ? 'border-accent-red' : 'border-gray-500'}`}>
                <h3 className="font-bold">{new Date(f.created_at).toLocaleString()} - {f.symbol}</h3>
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
