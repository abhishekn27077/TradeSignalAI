import { create } from 'zustand';
import { api } from '../services/api-client';
import { wsManager } from '../services/websocket-manager';

interface HealthState {
  dbStatus: 'online' | 'degraded' | 'offline';
  brokerStatus: 'online' | 'degraded' | 'offline';
  feedStatus: 'online' | 'degraded' | 'offline';
  omniStatus: 'online' | 'degraded' | 'offline';
  aiStatus: 'online' | 'degraded' | 'offline';
  wsStatus: 'online' | 'degraded' | 'offline';
  fetchHealth: () => Promise<void>;
}

export const useHealthStore = create<HealthState>((set) => ({
  dbStatus: 'offline',
  brokerStatus: 'offline',
  feedStatus: 'offline',
  omniStatus: 'offline',
  aiStatus: 'offline',
  wsStatus: 'offline',

  fetchHealth: async () => {
    try {
      const data = await api.health.status();
      const components = (data as any)?.components || {};
      const toStatus = (v: string) => v === 'ok' ? 'online' as const : v === 'uninitialized' ? 'degraded' as const : 'offline' as const;
      set({
        dbStatus: toStatus(components.database),
        brokerStatus: toStatus(components.broker_api),
        feedStatus: toStatus(components.market_feed),
        omniStatus: toStatus(components.omniroute),
        aiStatus: toStatus(components.ai_engine),
        wsStatus: wsManager.isConnected ? 'online' : (components.websocket === 'ok' ? 'online' : 'offline'),
      });
    } catch {
      set({ dbStatus: 'offline', brokerStatus: 'offline', feedStatus: 'offline', omniStatus: 'offline', aiStatus: 'offline', wsStatus: 'offline' });
    }
  },
}));