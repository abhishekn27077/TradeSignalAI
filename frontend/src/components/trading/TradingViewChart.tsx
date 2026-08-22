import React from 'react';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';
import { useAppStore } from '../../store/useAppStore';

interface TradingViewChartProps {
  symbol: string;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ symbol }) => {
  // Convert standard pair format (e.g. BTC-USD) to TradingView format (e.g. BINANCE:BTCUSD)
  const tvSymbol = symbol.includes('-')
    ? `BINANCE:${symbol.replace('-', '')}`
    : symbol.includes('/')
      ? `BINANCE:${symbol.replace('/', '')}`
      : symbol;

  return (
    <div className="flex flex-col w-full h-full bg-slate-900 overflow-hidden">
      <AdvancedRealTimeChart
        symbol={tvSymbol}
        theme="dark"
        interval="15"
        timezone="Etc/UTC"
        style="1"
        locale="en"
        enable_publishing={false}
        hide_top_toolbar={false}
        hide_legend={false}
        save_image={false}
        container_id="tradingview_chart"
        autosize={true}
      />
    </div>
  );
};