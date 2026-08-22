import React, { useState, useEffect } from 'react';

export const DecisionHistory: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    // Stub fetch to /api/v1/decision/history
    setHistory([
      {
        id: "1",
        created_at: new Date().toISOString(),
        trade_grade: "A+",
        qualification_score: 92.5,
        is_approved: true,
        rr_ratio: 3.1
      },
      {
        id: "2",
        created_at: new Date(Date.now() - 3600000).toISOString(),
        trade_grade: "B",
        qualification_score: 75.0,
        is_approved: false,
        rr_ratio: 1.5
      }
    ]);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-8">Decision History</h1>
      
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-900 border-b border-gray-700 text-gray-400">
            <tr>
              <th className="px-6 py-4 font-medium">Time</th>
              <th className="px-6 py-4 font-medium">Score</th>
              <th className="px-6 py-4 font-medium">Grade</th>
              <th className="px-6 py-4 font-medium">R:R</th>
              <th className="px-6 py-4 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {history.map((decision) => (
              <tr key={decision.id} className="hover:bg-gray-750 transition-colors">
                <td className="px-6 py-4 text-gray-300">
                  {new Date(decision.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 text-gray-300">
                  {decision.qualification_score.toFixed(1)}
                </td>
                <td className="px-6 py-4">
                  <span className={`font-bold ${decision.is_approved ? 'text-green-500' : 'text-yellow-500'}`}>
                    {decision.trade_grade}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-300">
                  {decision.rr_ratio ? decision.rr_ratio.toFixed(2) : '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    decision.is_approved 
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                      : 'bg-red-500/20 text-red-400 border border-red-500/30'
                  }`}>
                    {decision.is_approved ? 'APPROVED' : 'REJECTED'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
