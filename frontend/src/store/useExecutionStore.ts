import { create } from 'zustand';
import type { Order, Position } from '../types';
import { api } from '../services/api-client';
import { useAppStore } from './useAppStore';

interface ExecutionState {
  orders: Order[];
  positions: Position[];
  latency: number;
  slippage: number;
  fetchExecutionData: () => Promise<void>;
  setOrders: (orders: Order[]) => void;
  setPositions: (positions: Position[]) => void;
}

function mapPosition(p: any): Position {
  return {
    id: p.id || p.ticket || `${p.symbol}-${Date.now()}`,
    symbol: p.symbol || '',
    direction: p.direction || p.type || (p.pnl >= 0 ? 'LONG' : 'SHORT'),
    quantity: p.quantity || p.qty || p.volume || 0,
    entryPrice: p.entry_price || p.entryPrice || p.price_open || 0,
    currentPrice: p.current_price || p.currentPrice || p.price_current || 0,
    pnl: p.pnl || p.profit || 0,
    pnlPct: p.pnlPct ?? p.pnl_percent ?? 0,
    openedAt: p.opened_at || p.openedAt || p.time || Date.now(),
  };
}

function mapOrder(o: any): Order {
  return {
    id: o.id || o.ticket || `${Date.now()}`,
    symbol: o.symbol || '',
    direction: o.direction || o.type || 'BUY',
    type: o.type === 'LIMIT' ? 'LIMIT' : o.type === 'STOP' ? 'STOP' : 'MARKET',
    status: o.status || 'PENDING',
    quantity: o.quantity || o.qty || o.volume || 0,
    price: o.price || 0,
    filledPrice: o.filled_price || o.filledPrice,
    createdAt: o.created_at || o.createdAt || o.time_open || Date.now(),
  };
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  orders: [],
  positions: [],
  latency: 0,
  slippage: 0,

  fetchExecutionData: async () => {
    try {
      const [posData, ordData] = await Promise.all([
        api.execution.positions(),
        api.execution.orders(),
      ]);
      const positions = (Array.isArray(posData) ? posData : []).map(mapPosition);
      const orders = (Array.isArray(ordData) ? ordData : []).map(mapOrder);
      set({ positions, orders });

      const appState = useAppStore.getState();
      appState.setPositions(positions);
      appState.setOrders(orders);
    } catch {}
  },

  setOrders: (orders) => set({ orders }),
  setPositions: (positions) => set({ positions }),
}));