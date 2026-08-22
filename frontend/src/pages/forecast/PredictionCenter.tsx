import React from 'react';

export const PredictionCenterPage: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Prediction Center</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-trading-surface border border-panel-border rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">EURUSD</h2>
            <span className="bg-accent-green/20 text-accent-green px-2 py-1 rounded text-sm font-bold">BUY</span>
          </div>
          <p className="text-text-secondary mb-2">Confidence: <span className="text-white font-bold">92%</span></p>
          <p className="text-text-secondary mb-2">Expected Move: <span className="text-accent-green">+1.2%</span></p>
          <p className="text-text-secondary mb-2">Hold Time: <span>4 Hours</span></p>
          <p className="text-text-secondary">Models Used: Transformer, XGBoost, Market Structure</p>
          <div className="mt-4 p-3 bg-trading-dark rounded border border-panel-border text-sm">
            <strong>AI Reasoning:</strong> Strong bullish momentum detected with MACD crossover above SMA200. Consensus is high.
          </div>
        </div>
      </div>
    </div>
  );
};
