import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { KPICard } from '../components/core/KPICard';
import { Cpu, HardDrive, Wifi, Database, Brain, Activity, Server, Clock, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api-client';
import { wsManager } from '../services/websocket-manager';

export const SystemPage: React.FC = () => {
  const systemHealth = useAppStore((s) => s.systemHealth);
  const refreshSystemHealth = useAppStore((s) => s.refreshSystemHealth);
  const [detailed, setDetailed] = React.useState<any>(null);

  useEffect(() => {
    const fetchAll = async () => {
      await refreshSystemHealth();
      try {
        const [healthData, brokerStatus, runtimeTruth] = await Promise.all([
          api.health.status(),
          api.brokers.status().catch(() => null),
          fetch('/api/v1/system-intelligence/runtime-truth').then(r => r.ok ? r.json() : null).catch(() => null),
        ]);
        setDetailed({ healthData, brokerStatus, runtimeTruth });
      } catch {}
    };
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, []);

  const status = systemHealth || {
    api: 'offline', database: 'offline', websocket: 'offline',
    marketFeed: 'offline', aiEngine: 'offline', brokerConnection: 'offline',
    latencyMs: 0, avgLatency: 0, cpuUsage: 0, memoryUsage: 0, memoryTotal: 0, uptime: '',
  };

  const services = [
    { name: 'FastAPI Backend API', status: status.api, icon: <Server className="w-4 h-4" /> },
    { name: 'WebSocket Feed', status: status.websocket, icon: <Wifi className="w-4 h-4" /> },
    { name: 'Market Database (SQLite)', status: status.database, icon: <Database className="w-4 h-4" /> },
    { name: 'AI & Strategy Engine', status: status.aiEngine, icon: <Brain className="w-4 h-4" /> },
    { name: 'Market Feed (MT5 / Binance)', status: status.marketFeed, icon: <Activity className="w-4 h-4" /> },
    { name: 'Broker Gateway (Paper-Only)', status: status.brokerConnection, icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <div className="h-full flex flex-col gap-3 p-3 overflow-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">System Health</h2>
        <button onClick={refreshSystemHealth} className="p-1 text-text-muted hover:text-text-primary">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <KPICard label="API Status" value={status.api === 'online' ? 'Online' : status.api === 'degraded' ? 'Degraded' : 'Offline'} icon={<Server className="w-4 h-4" />} change={status.api === 'online' ? 100 : 0} />
        <KPICard label="WebSocket" value={status.websocket === 'online' ? 'Connected' : 'Disconnected'} icon={<Wifi className="w-4 h-4" />} change={status.websocket === 'online' ? 100 : 0} />
        <KPICard label="Database" value={status.database === 'online' ? 'Connected' : status.database === 'degraded' ? 'Uninit' : 'Offline'} icon={<Database className="w-4 h-4" />} change={status.database === 'online' ? 100 : 0} />
        <KPICard label="Broker" value={status.brokerConnection === 'online' ? 'Connected' : status.brokerConnection === 'degraded' ? 'Uninit' : 'Offline'} icon={<Activity className="w-4 h-4" />} change={status.brokerConnection === 'online' ? 100 : 0} />
      </div>

      <Card title="Service Status" subtitle="Live from backend">
        <div className="grid grid-cols-2 gap-3">
          {services.map((svc) => {
            const st = svc.status || 'offline';
            return (
              <div key={svc.name} className="flex items-center justify-between p-3 bg-trading-dark rounded-[var(--radius-md)] border border-panel-border/50">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-[var(--radius-md)] flex items-center justify-center ${
                    st === 'online' ? 'bg-profit/10 text-profit' :
                    st === 'degraded' ? 'bg-warning/10 text-warning' : 'bg-loss/10 text-loss'
                  }`}>{svc.icon}</div>
                  <span className="text-[12px] font-medium text-text-primary">{svc.name}</span>
                </div>
                <Badge variant={st === 'online' ? 'profit' : st === 'degraded' ? 'warning' : 'loss'} dot>
                  {st.toUpperCase()}
                </Badge>
              </div>
            );
          })}
        </div>
      </Card>

      {detailed?.healthData?.components && (
        <Card title="Backend Diagnostics" noPadding>
          <div className="p-3 text-[11px] font-mono text-text-secondary space-y-1">
            {Object.entries(detailed.healthData.components).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span>{k}</span>
                <span className={v === 'ok' ? 'text-profit' : 'text-loss'}>{String(v)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {detailed?.runtimeTruth && (
        <Card title="Phase 59 Canonical Runtime Truth & Fingerprint" subtitle="Absolute verified backend process identity" noPadding>
          <div className="p-3 text-[11px] font-mono text-text-secondary space-y-2 bg-slate-950/60 rounded-lg">
            <div className="flex justify-between border-b border-panel-border/30 pb-1">
              <span className="text-text-muted">Canonical Phase:</span>
              <span className="font-bold text-accent-cyan">{detailed.runtimeTruth.phase} ({detailed.runtimeTruth.engine_version})</span>
            </div>
            <div className="flex justify-between border-b border-panel-border/30 pb-1">
              <span className="text-text-muted">Git Commit / Branch:</span>
              <span className="font-bold text-text-primary">{detailed.runtimeTruth.git_commit} ({detailed.runtimeTruth.git_branch})</span>
            </div>
            <div className="flex justify-between border-b border-panel-border/30 pb-1">
              <span className="text-text-muted">Config Hash:</span>
              <span className="font-bold text-accent-gold">{detailed.runtimeTruth.config_hash}</span>
            </div>
            <div className="flex justify-between border-b border-panel-border/30 pb-1">
              <span className="text-text-muted">Backend PID / Executable:</span>
              <span className="font-bold text-text-primary">{detailed.runtimeTruth.backend_pid} ({detailed.runtimeTruth.python_executable})</span>
            </div>
            <div className="flex justify-between border-b border-panel-border/30 pb-1">
              <span className="text-text-muted">Execution Mode:</span>
              <span className="font-bold text-emerald-400">{detailed.runtimeTruth.execution_mode} (Real Money: STRICTLY DISABLED)</span>
            </div>
            <div className="flex justify-between border-b border-panel-border/30 pb-1">
              <span className="text-text-muted">State ID:</span>
              <span className="font-bold text-text-muted">{detailed.runtimeTruth.canonical_state_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Market Data Timestamp:</span>
              <span className="font-bold text-text-primary">{detailed.runtimeTruth.market_data_timestamp}</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
