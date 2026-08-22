import React, { useState, useEffect } from 'react';
import { Play, Square, Download, Activity, Server, Database, TrendingUp, AlertTriangle } from 'lucide-react';
import { api } from '../services/api-client';
import { useAppStore } from '../store/useAppStore';
import { message } from 'antd';

export const QualificationPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [mode, setMode] = useState<string>('synthetic');
  const [regime, setRegime] = useState<string>('trending');
  
  const fetchStatus = async () => {
    try {
      const res = await api.qualification.status();
      setStatus(res);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const int = setInterval(fetchStatus, 3000);
    return () => clearInterval(int);
  }, []);

  const handleStart = async () => {
    try {
      await api.qualification.start(mode, { regime });
      message.info('Qualification mode started');
      fetchStatus();
    } catch (e) {
      message.error('Failed to start qualification');
    }
  };

  const handleStop = async () => {
    try {
      await api.qualification.stop();
      message.info('Qualification mode stopped');
      fetchStatus();
    } catch (e) {
      message.error('Failed to stop qualification');
    }
  };

  const handleGenerateReport = async () => {
    try {
      const rep = await api.qualification.report();
      setReport(rep);
      message.success('Generated Qualification Report');
    } catch (e) {
      message.error('Failed to generate report');
    }
  };

  const isRunning = status?.is_running;

  return (
    <div className="p-6 h-full flex flex-col space-y-6 overflow-y-auto">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="text-trading-accent" />
            Trading Qualification Suite
          </h2>
          <p className="text-gray-400">Run synthetic stress tests, historical replays, and live validations.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-trading-panel border border-trading-border rounded-lg p-6 flex flex-col space-y-4">
          <h3 className="text-lg font-semibold text-white mb-2">Control Panel</h3>
          
          <div className="space-y-2">
            <label className="text-sm text-gray-400">Runtime Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              disabled={isRunning}
              className="w-full bg-trading-dark border border-trading-border rounded p-2 text-white"
            >
              <option value="synthetic">Mode 1: Synthetic Stress Test</option>
              <option value="historical">Mode 2: Historical Replay</option>
              <option value="live">Mode 3: Live Paper Trading</option>
            </select>
          </div>

          {mode === 'synthetic' && (
            <div className="space-y-2">
              <label className="text-sm text-gray-400">Market Regime</label>
              <select
                value={regime}
                onChange={(e) => setRegime(e.target.value)}
                disabled={isRunning}
                className="w-full bg-trading-dark border border-trading-border rounded p-2 text-white"
              >
                <option value="trending">Trending Market</option>
                <option value="sideways">Sideways Market</option>
                <option value="high_volatility">High Volatility</option>
                <option value="low_volatility">Low Volatility</option>
                <option value="flash_crash">Flash Crash</option>
                <option value="pump_dump">Pump & Dump</option>
              </select>
            </div>
          )}

          <div className="flex space-x-4 pt-4 mt-auto">
            {!isRunning ? (
              <button
                onClick={handleStart}
                className="flex-1 bg-trading-accent hover:bg-trading-accent/80 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2"
              >
                <Play size={18} />
                Start Test
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2"
              >
                <Square size={18} />
                Stop Test
              </button>
            )}
            
            <button
              onClick={handleGenerateReport}
              disabled={isRunning}
              className="bg-trading-dark border border-trading-border hover:bg-gray-800 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Download size={18} />
              Report
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 bg-trading-panel border border-trading-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Runtime Metrics</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <MetricCard title="Status" value={isRunning ? "RUNNING" : "STOPPED"} color={isRunning ? "text-green-400" : "text-gray-400"} />
            <MetricCard title="Active Mode" value={status?.active_mode || "N/A"} />
            <MetricCard title="Uptime (s)" value={Math.round(status?.uptime_seconds || 0).toString()} />
            
            <MetricCard title="Trades Completed" value={status?.metrics?.trades_completed?.toString() || "0"} icon={<TrendingUp size={16} />} />
            <MetricCard title="Signals Generated" value={status?.metrics?.signals_generated?.toString() || "0"} />
            <MetricCard title="Journal Entries" value={status?.metrics?.journal_entries?.toString() || "0"} />
            
            <MetricCard title="CPU Usage" value={`${status?.metrics?.cpu_percent?.toFixed(1) || 0}%`} icon={<Server size={16} />} />
            <MetricCard title="RAM Usage" value={`${status?.metrics?.ram_mb?.toFixed(1) || 0} MB`} />
            <MetricCard title="DB Size" value={`${status?.metrics?.db_size_mb?.toFixed(2) || 0} MB`} icon={<Database size={16} />} />
          </div>
        </div>
      </div>

      {report && (
        <div className="bg-trading-panel border border-trading-border rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            Final Qualification Report
            <span className={`text-sm px-2 py-1 rounded ${report.status === 'PASS' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
              {report.status}
            </span>
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-trading-dark p-4 rounded border border-trading-border text-center">
              <div className="text-sm text-gray-400">Overall Score</div>
              <div className="text-2xl font-bold text-white">{report.overall_score}%</div>
            </div>
            <div className="bg-trading-dark p-4 rounded border border-trading-border text-center">
              <div className="text-sm text-gray-400">Integration Score</div>
              <div className="text-xl font-bold text-white">{report.integration_score}%</div>
            </div>
            <div className="bg-trading-dark p-4 rounded border border-trading-border text-center">
              <div className="text-sm text-gray-400">Reliability Score</div>
              <div className="text-xl font-bold text-white">{report.reliability_score}%</div>
            </div>
            <div className="bg-trading-dark p-4 rounded border border-trading-border text-center">
              <div className="text-sm text-gray-400">Performance Score</div>
              <div className="text-xl font-bold text-white">{report.performance_score}%</div>
            </div>
          </div>
          
          <div className="space-y-4">
            {report.warnings.length > 0 && (
              <div className="bg-yellow-900/20 border border-yellow-700/50 p-4 rounded text-yellow-500 text-sm">
                <div className="font-bold flex items-center gap-2 mb-2"><AlertTriangle size={16}/> Warnings</div>
                <ul className="list-disc pl-5">
                  {report.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}
            
            <div className="bg-trading-dark border border-trading-border p-4 rounded">
              <pre className="text-xs text-gray-400 overflow-x-auto">
                {JSON.stringify(report.metrics, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const MetricCard = ({ title, value, color = "text-white", icon = null }: any) => (
  <div className="bg-trading-dark p-4 rounded border border-trading-border">
    <div className="text-xs text-gray-400 flex items-center gap-1 mb-1">
      {icon} {title}
    </div>
    <div className={`text-xl font-mono font-bold ${color}`}>{value}</div>
  </div>
);
