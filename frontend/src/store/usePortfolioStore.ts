import { create } from 'zustand';
import { api } from '../services/api-client';
import { useAppStore } from './useAppStore';

interface PortfolioState {
  equity: number;
  balance: number;
  usedMargin: number;
  freeMargin: number;
  dailyPnl: number;
  weeklyPnl: number;
  fetchPortfolio: () => Promise<void>;
  setPortfolio: (data: Partial<PortfolioState>) => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  equity: 0,
  balance: 0,
  usedMargin: 0,
  freeMargin: 0,
  dailyPnl: 0,
  weeklyPnl: 0,

  fetchPortfolio: async () => {
    try {
      const [bal, perf] = await Promise.all([
        api.execution.balance(),
        api.analytics.performance(),
      ]);
      set({
        equity: bal.equity ?? bal.balance ?? 0,
        balance: bal.balance ?? bal.equity ?? 0,
        usedMargin: bal.used_margin ?? bal.margin ?? 0,
        freeMargin: bal.free_margin ?? bal.freeMargin ?? 0,
        dailyPnl: perf.daily_pnl ?? 0,
        weeklyPnl: perf.weekly_pnl ?? 0,
      });
    } catch {}

    const appState = useAppStore.getState();
    appState.refreshPortfolio();
  },

  setPortfolio: (data) => set((state) => ({ ...state, ...data })),
}));