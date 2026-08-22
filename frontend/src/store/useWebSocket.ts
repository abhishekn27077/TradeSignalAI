import { useEffect, useRef } from 'react';
import { wsManager } from '../services/websocket-manager';
import { useAppStore } from './useAppStore';

export function useWebSocket() {
  const initialized = useRef(false);

  const updateTicker = useAppStore((s) => s.updateTicker);
  const addSignal = useAppStore((s) => s.addSignal);
  const setSystemHealth = useAppStore((s) => s.setSystemHealth);
  const refreshOrders = useAppStore((s) => s.refreshOrders);
  const refreshPositions = useAppStore((s) => s.refreshPositions);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    wsManager.connect();
    wsManager.subscribe('system');
    wsManager.subscribe('signals');
    wsManager.subscribe('orders');
    wsManager.subscribe('positions');

    const unsubTick = wsManager.on('tick', (data: any) => {
      if (data?.symbol) updateTicker(data);
    });
    const unsubSignal = wsManager.on('signal_generated', (data: any) => {
      if (data) addSignal(data);
    });
    const unsubHealth = wsManager.on('system_health', (data: any) => {
      if (data) setSystemHealth(data);
    });
    const unsubOrder = wsManager.on('order_update', () => refreshOrders());
    const unsubPos = wsManager.on('position_update', () => refreshPositions());

    return () => {
      unsubTick();
      unsubSignal();
      unsubHealth();
      unsubOrder();
      unsubPos();
    };
  }, []);

  return {
    subscribeToTicker: (symbol: string) => wsManager.subscribe(`tick.${symbol}`),
    unsubscribeFromTicker: (symbol: string) => wsManager.unsubscribe(`tick.${symbol}`),
  };
}
