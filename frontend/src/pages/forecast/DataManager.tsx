import React, { useEffect, useState } from 'react';
import { api } from '../../services/api-client';
import { Download, Play, RefreshCw, AlertCircle, CheckCircle, Activity as ActivityIcon } from 'lucide-react';
import { wsManager } from '../../services/websocket-manager';

interface SyncStatus {
  running: boolean;
  last_sync: string | null;
  next_sync: string | null;
  interval_minutes: number;
}

export const DataManagerPage: React.FC = () => {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [activeJobs, setActiveJobs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    loadStatus();

    wsManager.on('data_sync', (data: any) => {
      setEvents(prev => [data, ...prev].slice(0, 50));
      if (data.type === 'DataDownloadProgress') {
        setActiveJobs(prev => ({
          ...prev,
          [`${data.payload.symbol}:${data.payload.timeframe}`]: `${data.payload.status} (${Math.round(data.payload.progress)}%)`
        }));
      }
    });
    wsManager.subscribe('data_sync');

    return () => {
      wsManager.unsubscribe('data_sync');
    };
  }, []);

  const loadStatus = async () => {
    try {
      const res = await api.get<{sync_service: SyncStatus, active_jobs: Record<string, string>}>('/data/status');
      setStatus(res.sync_service);
      setActiveJobs(res.active_jobs || {});
    } catch (e) {
      console.error(e);
    }
  };

  const startDownloadAll = async () => {
    setLoading(true);
    try {
      await api.post('/data/download/all');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Download className="text-accent-blue" />
            Data Manager
          </h1>
          <p className="text-text-secondary mt-1">
            Monitor and control historical market data synchronization
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={loadStatus}
            className="px-4 py-2 bg-trading-elevated hover:bg-trading-hover rounded border border-panel-border transition-colors flex items-center gap-2 text-sm"
          >
            <RefreshCw className="w-4 h-4" /> Refresh Status
          </button>
          <button 
            onClick={startDownloadAll}
            disabled={loading}
            className="px-4 py-2 bg-accent-blue/10 text-accent-blue hover:bg-accent-blue/20 rounded border border-accent-blue/30 transition-colors flex items-center gap-2 text-sm font-medium"
          >
            <ActivityIcon className="w-4 h-4 mr-2" /> Start Global Sync
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Sync Service Status */}
        <div className="bg-trading-surface border border-panel-border rounded-lg p-6">
          <h2 className="text-lg font-bold mb-4">Background Sync Service</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-panel-border">
              <span className="text-text-secondary">Status</span>
              <span className={`px-2 py-1 rounded text-xs font-bold ${status?.running ? 'bg-accent-green/20 text-accent-green' : 'bg-text-muted/20 text-text-muted'}`}>
                {status?.running ? 'RUNNING' : 'STOPPED'}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-panel-border">
              <span className="text-text-secondary">Sync Interval</span>
              <span className="font-mono text-text-primary">{status?.interval_minutes} min</span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-panel-border">
              <span className="text-text-secondary">Last Sync</span>
              <span className="font-mono text-text-primary text-sm">
                {status?.last_sync ? new Date(status.last_sync).toLocaleTimeString() : 'Never'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-text-secondary">Next Sync</span>
              <span className="font-mono text-text-primary text-sm">
                {status?.next_sync ? new Date(status.next_sync).toLocaleTimeString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Active Jobs */}
        <div className="bg-trading-surface border border-panel-border rounded-lg p-6 col-span-2 flex flex-col">
          <h2 className="text-lg font-bold mb-4">Active Sync Jobs</h2>
          <div className="flex-1 overflow-y-auto">
            {Object.keys(activeJobs).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(activeJobs).map(([key, state]) => (
                  <div key={key} className="flex items-center justify-between bg-trading-elevated p-3 rounded border border-panel-border-light">
                    <span className="font-mono font-medium">{key}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-text-secondary uppercase">{state}</span>
                      {state.includes('downloading') && <ActivityIcon className="w-4 h-4 text-accent-blue animate-spin" />}
                      {state.includes('completed') && <CheckCircle className="w-4 h-4 text-accent-green" />}
                      {state.includes('failed') && <AlertCircle className="w-4 h-4 text-color-loss" />}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-text-muted pb-8">
                <CheckCircle className="w-10 h-10 mb-3 opacity-20" />
                <p>No active synchronization jobs</p>
                <p className="text-xs mt-1">All datasets are up to date</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Live Event Log */}
      <div className="bg-trading-surface border border-panel-border rounded-lg p-6 flex-1 flex flex-col min-h-0">
        <h2 className="text-lg font-bold mb-4">Live Sync Events</h2>
        <div className="flex-1 overflow-y-auto bg-trading-dark rounded border border-panel-border p-4 font-mono text-xs">
          {events.length > 0 ? (
            events.map((ev, i) => (
              <div key={i} className="mb-2 pb-2 border-b border-panel-border/50 last:border-0 last:mb-0 last:pb-0 flex gap-4">
                <span className="text-text-muted whitespace-nowrap">
                  {new Date().toLocaleTimeString()}
                </span>
                <span className="text-accent-gold whitespace-nowrap w-48 overflow-hidden text-ellipsis">
                  {ev.type}
                </span>
                <span className="text-text-secondary truncate">
                  {JSON.stringify(ev.payload)}
                </span>
              </div>
            ))
          ) : (
            <div className="text-text-muted">Listening for events...</div>
          )}
        </div>
      </div>
    </div>
  );
};

