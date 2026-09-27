import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { Button } from '../components/core/Button';
import { PriceTicker } from '../components/trading/PriceTicker';
import { TradingViewChart } from '../components/trading/TradingViewChart';
import { TrendingUp, TrendingDown, Eye, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api-client';
import { wsManager } from '../services/websocket-manager';

export const TerminalPage: React.FC = () => {
  const { tickers, positions, portfolio, signals, refreshOrders, refreshPositions } = useAppStore();
  const [orderBook, setOrderBook] = React.useState<{ bids: any[]; asks: any[]; spread: number; mid: number }>({
    bids: [], asks: [], spread: 0, mid: 0,
  });
  const [selectedSymbol, setSelectedSymbol] = React.useState('BTC-USD');
  const [availableSymbols, setAvailableSymbols] = React.useState<string[]>([]);

  useEffect(() => {
    refreshPositions();
    refreshOrders();
    const syms = ['BTC-USD', 'ETH-USD', 'SOL-USD'];
    setAvailableSymbols(syms);
    wsManager.subscribe(`tick.${syms[0]}`);

    const unsubTick = wsManager.on('tick', (data: any) => {
      if (data?.symbol) {
        const price = data.price ?? 0;
        const bid = data.bid ?? null;
        const ask = data.ask ?? null;
        const spread = (ask && bid) ? (ask - bid) : 0;
        setOrderBook(prev => ({
          ...prev,
          mid: price,
          spread,
          bids: data.bids || (bid ? [{ price: bid, size: data.volume || 1.0, total: 1.0 }] : []),
          asks: data.asks || (ask ? [{ price: ask, size: data.volume || 1.0, total: 1.0 }] : []),
        }));
      }
    });

    return () => {
      unsubTick();
      availableSymbols.forEach(s => wsManager.unsubscribe(`tick.${s}`));
    };
  }, []);

  const watchlistData = Object.values(tickers).map(t => ({
    symbol: t.symbol,
    price: t.price,
    change: t.changePct24h || 0,
    volume: (t.volume24h || t.volume || 0) > 1000
      ? `${((t.volume24h || t.volume || 0) / 1e9).toFixed(1)}B`
      : `${((t.volume24h || t.volume || 0) / 1e6).toFixed(1)}M`,
  }));

  const displayPositions = positions;
  const displaySignals = signals.slice(0, 5);

  return (
    <div className="h-full grid grid-cols-[240px_1fr_260px] grid-rows-[1fr_240px] gap-[1px] bg-panel-border">
      <div className="bg-trading-dark row-span-2 overflow-hidden">
        <Card title="Watchlist" action={<Button variant="ghost" size="sm"><Eye className="w-3 h-3" /></Button>} noPadding>
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-text-muted text-[9px] uppercase tracking-wider border-b border-panel-border">
                <th className="text-left px-3 py-1.5 font-medium">Symbol</th>
                <th className="text-right px-3 py-1.5 font-medium">Price</th>
                <th className="text-right px-3 py-1.5 font-medium">Chg%</th>
              </tr>
            </thead>
            <tbody>
              {watchlistData.length > 0 ? watchlistData.map((row) => (
                <tr
                  key={row.symbol}
                  className="border-b border-panel-border/50 hover:bg-trading-hover transition-colors duration-100 cursor-pointer"
                  onClick={() => setSelectedSymbol(row.symbol.replace('/', '-'))}
                >
                  <td className="px-3 py-1.5 font-medium text-text-primary">{row.symbol}</td>
                  <td className="px-3 py-1.5 text-right">
                    <PriceTicker price={row.price} decimals={row.price < 1 ? 4 : 2} />
                  </td>
                  <td className={`px-3 py-1.5 text-right font-medium ${row.change >= 0 ? 'text-profit' : 'text-loss'}`}>
                    <span data-mono>{row.change >= 0 ? '+' : ''}{row.change.toFixed(2)}%</span>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={3} className="px-3 py-4 text-center text-text-muted text-[10px]">No symbols connected. Start TradingView to see prices.</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>

      <div className="bg-trading-dark overflow-hidden">
        <Card
          title={selectedSymbol.replace('-', '/')}
          subtitle={`Live · ${orderBook.mid > 0 ? `$${orderBook.mid.toLocaleString()}` : 'Waiting for data'}`}
          action={
            <div className="flex items-center gap-1">
              {['1m', '5m', '15m', '1H', '4H', '1D'].map((tf) => (
                <button key={tf} className={`px-2 py-0.5 text-[10px] rounded-[var(--radius-sm)] cursor-pointer transition-colors duration-100 ${tf === '1H' ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/30' : 'text-text-muted hover:text-text-primary hover:bg-trading-hover'}`}>{tf}</button>
              ))}
              <button className="ml-1 p-0.5 text-text-muted hover:text-text-primary" onClick={() => { refreshPositions(); refreshOrders(); }}>
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
          }
          noPadding
        >
          <div className="w-full h-full p-2 bg-trading-dark/50">
            <TradingViewChart symbol={selectedSymbol} />
          </div>
        </Card>
      </div>

      <div className="bg-trading-dark row-span-2 overflow-hidden">
        <Card title="Order Book" subtitle={`${selectedSymbol.replace('-', '/')}`} noPadding>
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-hidden flex flex-col justify-end">
              {orderBook.asks.slice().reverse().map((level, i) => (
                <div key={`a${i}`} className="flex items-center text-[10px] px-2 py-[2px] relative">
                  <div className="absolute right-0 top-0 bottom-0 bg-loss/8" style={{ width: `${Math.min(level.total * 5, 100)}%` }} />
                  <span data-mono className="w-1/3 text-loss relative z-10">{level.price.toFixed(2)}</span>
                  <span data-mono className="w-1/3 text-right text-text-secondary relative z-10">{level.size.toFixed(4)}</span>
                  <span data-mono className="w-1/3 text-right text-text-muted relative z-10">{level.total.toFixed(4)}</span>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between px-2 py-1.5 border-y border-panel-border bg-trading-elevated/50">
              <span data-mono className="text-[12px] font-semibold text-text-primary">
                {orderBook.mid > 0 ? orderBook.mid.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--'}
              </span>
              <span className="text-[9px] text-text-muted">Spread: ${orderBook.spread.toFixed(2)}</span>
            </div>

            <div className="flex-1 overflow-hidden">
              {orderBook.bids.map((level, i) => (
                <div key={`b${i}`} className="flex items-center text-[10px] px-2 py-[2px] relative">
                  <div className="absolute left-0 top-0 bottom-0 bg-profit/8" style={{ width: `${Math.min(level.total * 5, 100)}%` }} />
                  <span data-mono className="w-1/3 text-profit relative z-10">{level.price.toFixed(2)}</span>
                  <span data-mono className="w-1/3 text-right text-text-secondary relative z-10">{level.size.toFixed(4)}</span>
                  <span data-mono className="w-1/3 text-right text-text-muted relative z-10">{level.total.toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <div className="bg-trading-dark overflow-hidden grid grid-cols-3 gap-[1px]">
        <Card title="Omni-Engine Status" noPadding>
          <div className="flex flex-col p-2 space-y-3">
            <div>
              <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">Market Regime</div>
              <div className="flex items-center gap-2">
                <Badge variant={useAppStore.getState().marketRegime?.trend?.includes('BULL') ? 'profit' : useAppStore.getState().marketRegime?.trend?.includes('BEAR') ? 'loss' : 'neutral'}>
                  {useAppStore.getState().marketRegime?.trend || 'DETECTING...'}
                </Badge>
                <span className="text-[11px] text-text-secondary">{useAppStore.getState().marketRegime?.volatility || ''} Volatility</span>
              </div>
            </div>
            
            <div>
              <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">AI Risk Status</div>
              <div className="flex items-center gap-2">
                <Badge variant={useAppStore.getState().advancedRisk?.max_daily_drawdown_pct ? 'profit' : 'warning'}>
                  {useAppStore.getState().advancedRisk ? 'CLEARED' : 'ANALYZING...'}
                </Badge>
                <span className="text-[11px] text-text-secondary">Global limits enforced</span>
              </div>
            </div>
            
            <div>
              <div className="text-[10px] text-text-muted uppercase tracking-wider mb-1">Trade Quality Engine</div>
              <div className="flex items-center gap-2">
                <Badge variant="profit">ACTIVE</Badge>
                <span className="text-[11px] text-text-secondary">Scoring incoming signals</span>
              </div>
            </div>
          </div>
        </Card>

        <Card title={`Positions (Equity: $${(portfolio?.totalEquity || 0).toLocaleString()})`} subtitle={`${displayPositions?.length || 0} open`} noPadding>
          <table className="w-full text-[10px]">
            <thead>
              <tr className="text-text-muted text-[9px] uppercase tracking-wider border-b border-panel-border">
                <th className="text-left px-2 py-1 font-medium">Symbol</th>
                <th className="text-center px-2 py-1 font-medium">Side</th>
                <th className="text-right px-2 py-1 font-medium">Qty</th>
                <th className="text-right px-2 py-1 font-medium">Entry</th>
                <th className="text-right px-2 py-1 font-medium">Current</th>
                <th className="text-right px-2 py-1 font-medium">P&L</th>
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(displayPositions) ? displayPositions : []).map((p: any) => (
                <tr key={p.id || p.symbol} className="border-b border-panel-border/30 hover:bg-trading-hover transition-colors duration-100">
                  <td className="px-2 py-1.5 font-medium text-text-primary">{p.symbol}</td>
                  <td className="px-2 py-1.5 text-center"><Badge variant={p.direction === 'LONG' || p.direction === 'BUY' ? 'profit' : 'loss'}>{p.direction}</Badge></td>
                  <td data-mono className="px-2 py-1.5 text-right text-text-secondary">{p.quantity || p.qty}</td>
                  <td data-mono className="px-2 py-1.5 text-right text-text-secondary">{p.entryPrice?.toLocaleString() || '0'}</td>
                  <td data-mono className="px-2 py-1.5 text-right text-text-primary">{p.currentPrice?.toLocaleString() || '0'}</td>
                  <td data-mono className={`px-2 py-1.5 text-right font-semibold ${(p.pnl || 0) >= 0 ? 'text-profit' : 'text-loss'}`}>
                    {(p.pnl || 0) >= 0 ? '+' : ''}${(p.pnl || 0).toFixed(2)}
                  </td>
                </tr>
              ))}
              {displayPositions.length === 0 && (
                <tr><td colSpan={6} className="px-2 py-4 text-center text-text-muted text-[10px]">No open positions</td></tr>
              )}
            </tbody>
          </table>
        </Card>

        <Card title="Latest Signals" noPadding>
          <div className="flex flex-col">
            {displaySignals.map((sig: any) => (
              <div key={sig.id || sig.symbol + sig.timestamp} className="flex items-center justify-between px-2 py-1.5 border-b border-panel-border/30 hover:bg-trading-hover transition-colors duration-100">
                <div className="flex items-center gap-2">
                  {sig.direction === 'BUY' ? <TrendingUp className="w-3 h-3 text-profit" /> : <TrendingDown className="w-3 h-3 text-loss" />}
                  <div>
                    <span className="text-[11px] font-medium text-text-primary">{sig.symbol}</span>
                    <span className="text-[9px] text-text-muted ml-1.5">{sig.strategy}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={sig.direction === 'BUY' ? 'profit' : 'loss'}>{sig.direction}</Badge>
                  <span data-mono className="text-[10px] text-text-secondary">{sig.strength ?? sig.confidence}%</span>
                </div>
              </div>
            ))}
            {displaySignals.length === 0 && (
              <div className="px-2 py-4 text-center text-text-muted text-[10px]">No signals yet. Enable strategies to generate signals.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};