import React, { useEffect, useState } from 'react';
import { Eye, ShieldAlert, CheckCircle2, Clock, Activity, Cpu, TrendingUp, AlertTriangle, RefreshCw, BarChart2 } from 'lucide-react';

interface ShadowLiveState {
  timestamp_utc: string;
  market_session: {
    asset: string;
    is_market_open: boolean;
    is_weekend: boolean;
    active_sessions: string[];
    is_london_ny_overlap: boolean;
  };
  drift_status: string;
  risk_multiplier: number;
  active_predictions_count: number;
  recent_predictions: Array<{
    prediction_id: string;
    signal_id: string;
    generated_at_utc: string;
    asset: string;
    timeframe: string;
    direction: string;
    entry: number;
    stop_loss: number;
    take_profit: number;
    raw_confidence: number;
    calibrated_confidence: number;
    grade: string;
    status: string;
    decision_hash: string;
  }>;
}

export const ShadowLivePage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<ShadowLiveState | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const fetchLiveState = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/shadow/live');
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setState(data);
          setLastRefreshed(new Date().toLocaleTimeString());
        }
      }
    } catch (e) {
      console.error('Failed to fetch shadow live state:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveState();
    const interval = setInterval(fetchLiveState, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 border border-purple-500/30 rounded-lg text-purple-400">
              <Eye className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Shadow-Live Trading Terminal</h1>
              <p className="text-sm text-slate-400">
                Point-in-time immutable predictions frozen before market outcome with zero real-money risk
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-purple-500/10 border border-purple-500/30 text-purple-400 rounded-full text-xs font-mono font-semibold flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" />
            SHADOW MODE ACTIVE
          </span>
          <button
            onClick={fetchLiveState}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-lg text-xs font-medium text-slate-300 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Top Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
        {/* Market Sessions */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Clock className="w-4 h-4 text-blue-400" />
            Active Sessions
          </div>
          <div className="text-lg font-bold text-slate-100">
            {state?.market_session?.active_sessions?.join(', ') || 'LONDON, NY'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {state?.market_session?.is_london_ny_overlap ? 'High Liquidity Overlap Active' : 'Single Session Processing'}
          </div>
        </div>

        {/* Drift Status */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
            Model Drift Status
          </div>
          <div className="text-lg font-bold text-emerald-400">
            {state?.drift_status || 'NORMAL'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Risk Multiplier: <span className="text-slate-200 font-mono">{state?.risk_multiplier || 1.0}x</span>
          </div>
        </div>

        {/* Active Predictions */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Cpu className="w-4 h-4 text-purple-400" />
            Active Shadow Setups
          </div>
          <div className="text-lg font-bold text-purple-400">
            {state?.active_predictions_count || 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Frozen with cryptographic SHA-256
          </div>
        </div>

        {/* Capital Safety */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <CheckCircle2 className="w-4 h-4 text-amber-400" />
            Real Money Gate
          </div>
          <div className="text-lg font-bold text-amber-400">
            HARD LOCKOUT (0.0%)
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Paper Sandbox Only
          </div>
        </div>
      </div>

      {/* Predictions Table */}
      <div className="mt-8 bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-purple-400" />
            Point-in-Time Shadow Predictions Ledger
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {lastRefreshed ? `Updated: ${lastRefreshed}` : ''}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Prediction ID</th>
                <th className="p-3">Asset / TF</th>
                <th className="p-3">Direction</th>
                <th className="p-3">Entry</th>
                <th className="p-3">SL / TP</th>
                <th className="p-3">Confidence (Raw / Cal)</th>
                <th className="p-3">Grade</th>
                <th className="p-3">Status</th>
                <th className="p-3">Decision Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
              {state?.recent_predictions && state.recent_predictions.length > 0 ? (
                state.recent_predictions.map((p) => (
                  <tr key={p.prediction_id} className="hover:bg-slate-900/40 transition">
                    <td className="p-3 text-slate-400 font-sans font-medium">{p.prediction_id}</td>
                    <td className="p-3 text-slate-100 font-bold">{p.asset} <span className="text-slate-400 font-normal">({p.timeframe})</span></td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        p.direction === 'BUY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        p.direction === 'SELL' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {p.direction}
                      </span>
                    </td>
                    <td className="p-3 text-slate-200">{p.entry}</td>
                    <td className="p-3 text-slate-400">
                      <span className="text-rose-400">{p.stop_loss}</span> / <span className="text-emerald-400">{p.take_profit}</span>
                    </td>
                    <td className="p-3">
                      <span className="text-slate-200">{(p.raw_confidence * 100).toFixed(0)}%</span> / <span className="text-purple-400">{(p.calibrated_confidence * 100).toFixed(0)}%</span>
                    </td>
                    <td className="p-3 text-amber-400 font-bold">{p.grade}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-xs">
                        {p.status}
                      </span>
                    </td>
                    <td className="p-3 text-slate-500 text-[10px]">{p.decision_hash?.substring(0, 12)}...</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="p-6 text-center text-slate-500">
                    No active shadow predictions in current window.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
