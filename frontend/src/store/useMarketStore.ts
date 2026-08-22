import { create } from 'zustand';
import type { Ticker, OrderBookLevel } from '../types';
import { wsManager } from '../services/websocket-manager';

export interface OrderBook {
  symbol: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  timestamp: number;
}

interface MarketState {
  tickers: Record<string, Ticker>;
  orderBooks: Record<string, OrderBook>;
  isConnected: boolean;
  subscribe: (symbol: string, channel: 'tick' | 'book' | 'candle') => void;
  unsubscribe: (symbol: string, channel: 'tick' | 'book' | 'candle') => void;
  updateTicker: (ticker: Ticker) => void;
  updateOrderBook: (book: OrderBook) => void;
}

export const useMarketStore = create<MarketState>((set, get) => ({
  tickers: {},
  orderBooks: {},
  isConnected: false,

  subscribe: (symbol, channel) => {
    wsManager.subscribe(`${channel}.${symbol}`);
  },

  unsubscribe: (symbol, channel) => {
    wsManager.unsubscribe(`${channel}.${symbol}`);
  },

  updateTicker: (ticker) => set((state) => ({
    tickers: { ...state.tickers, [ticker.symbol]: ticker }
  })),

  updateOrderBook: (book) => set((state) => ({
    orderBooks: { ...state.orderBooks, [book.symbol]: book }
  })),
}));