import React from 'react';
import { useAppStore } from '../../store/useAppStore';

/* ========================================================================== */
/* STATUS BAR — Bottom bar showing system health metrics                      */
/* ========================================================================== */

export const StatusBar: React.FC = () => {
  const systemHealth = useAppStore((s) => s.systemHealth);

  const items = [
    { label: 'API', status: systemHealth?.api ?? 'offline' },
    { label: 'WS', status: systemHealth?.websocket ?? 'offline' },
    { label: 'DB', status: systemHealth?.database ?? 'offline' },
    { label: 'Feed', status: systemHealth?.marketFeed ?? 'offline' },
    { label: 'AI', status: systemHealth?.aiEngine ?? 'offline' },
    { label: 'Broker', status: systemHealth?.brokerConnection ?? 'offline' },
  ];

  const latency = systemHealth?.latencyMs ?? 0;

  return (
    <footer
      className="
        h-6 bg-trading-surface border-t border-panel-border
        flex items-center justify-between px-3
        text-[10px] select-none
      "
    >
      {/* Left: Service statuses */}
      <div className="flex items-center gap-3">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-1">
            <span
              className={`status-dot ${
                item.status === 'online'
                  ? 'status-dot-online'
                  : item.status === 'degraded'
                  ? 'status-dot-warning'
                  : 'status-dot-offline'
              }`}
            />
            <span className="text-text-muted">{item.label}</span>
          </div>
        ))}
      </div>

      {/* Right: Latency + version */}
      <div className="flex items-center gap-3 text-text-muted">
        <span data-mono>
          {latency > 0 ? `${latency.toFixed(0)}ms` : '--ms'}
        </span>
        <span>v3.0.0</span>
      </div>
    </footer>
  );
};

