import React, { useState, useEffect } from 'react';
import { DecisionCard } from '../../components/decision/DecisionCard';

export const DecisionDashboard: React.FC = () => {
  const [latestDecision, setLatestDecision] = useState<any>(null);
  
  useEffect(() => {
    // Stub for WebSocket connection to /decision
    setLatestDecision({
      grade: "A",
      score: 85.5,
      confidence: 0.88,
      rrRatio: 2.5,
      approved: true,
      reasons: ["High confidence.", "Good Risk/Reward."],
      warnings: ["Late entry risk."]
    });
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-2">Decision Intelligence Layer</h1>
      <p className="text-gray-400 mb-8">Live trade qualification and institutional risk analysis.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold text-gray-200 mb-4">Latest Evaluation</h2>
          {latestDecision ? (
            <DecisionCard {...latestDecision} />
          ) : (
            <div className="p-4 bg-gray-800 rounded-lg text-gray-400 animate-pulse">
              Waiting for next forecast...
            </div>
          )}
        </div>
        
        <div>
           <h2 className="text-xl font-semibold text-gray-200 mb-4">Current Regime</h2>
           <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 space-y-4">
             <div className="flex justify-between items-center">
               <span className="text-gray-400">Market Regime</span>
               <span className="text-white font-semibold">Trending</span>
             </div>
             <div className="flex justify-between items-center">
               <span className="text-gray-400">Volatility</span>
               <span className="text-yellow-400 font-semibold">High</span>
             </div>
             <div className="flex justify-between items-center">
               <span className="text-gray-400">Active Session</span>
               <span className="text-blue-400 font-semibold">London/NY Overlap</span>
             </div>
             <div className="mt-4 pt-4 border-t border-gray-700">
               <p className="text-sm text-gray-300">
                 System is currently requiring a minimum of Grade <strong>A</strong> (score &gt;= 80) for automatic trade approval.
               </p>
             </div>
           </div>
        </div>
      </div>
    </div>
  );
};
