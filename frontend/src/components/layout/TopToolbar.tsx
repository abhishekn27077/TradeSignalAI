import React, { useEffect, useState } from 'react';
import {
  Search,
  Clock,
  ChevronDown,
  Activity,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Badge } from '../core/Badge';

/* ========================================================================== */
/* TOP TOOLBAR — Professional Trading Terminal Header                         */
/* ========================================================================== */

const IST_TZ = 'Asia/Kolkata';

function getMarketSession(): string {
  const now = new Date();
  const utcH = now.getUTCHours();
  if (utcH >= 0 && utcH < 7) return 'Asia';
  if (utcH >= 7 && utcH < 12) return 'London';
  if (utcH >= 12 && utcH < 21) return 'New York';
  return 'Closed';
}

function getNextH4(): string {
  const now = new Date();
  const h = now.getUTCHours();
  const nextH4 = Math.ceil((h + 1) / 4) * 4;
  const target = new Date(now);
  target.setUTCHours(nextH4, 0, 0, 0);
  if (target <= now) target.setUTCDate(target.getUTCDate() + 1);
  const diff = Math.max(0, Math.floor((target.getTime() - now.getTime()) / 1000));
  const hh = Math.floor(diff / 3600);
  const mm = Math.floor((diff % 3600) / 60);
  const ss = diff % 60;
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}

export const TopToolbar: React.FC = () => {
  const portfolio = useAppStore((s) => s.portfolio);
  const systemHealth = useAppStore((s) => s.systemHealth);
  const [istTime, setIstTime] = useState('');
  const [h4Countdown, setH4Countdown] = useState('');
  const [session, setSession] = useState('');

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setIstTime(now.toLocaleTimeString('en-IN', { timeZone: IST_TZ, hour12: false }));
      setH4Countdown(getNextH4());
      setSession(getMarketSession());
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  const isConnected = systemHealth?.websocket === 'online';
  const sessionColor = session === 'Closed' ? 'text-text-muted' : session === 'New York' ? 'text-accent-blue' : session === 'London' ? 'text-accent-gold' : 'text-accent-cyan';

  return (
    <header
      className="
        h-10 bg-trading-surface border-b border-panel-border
        flex items-center justify-between px-3
        select-none z-[var(--z-toolbar)]
      "
    >
      {/* Left: Logo + Asset Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-[var(--radius-sm)] bg-accent-green/20 flex items-center justify-center">
            <span className="text-[10px] font-bold text-accent-green">TS</span>
          </div>
          <span className="text-[12px] font-semibold text-text-primary tracking-wide">
            TradeSignalAI
          </span>
        </div>

        <div className="flex items-center gap-1.5 ml-2">
          <select
            value={useAppStore(s => s.activeAsset)}
            onChange={(e) => useAppStore.getState().setActiveAsset(e.target.value)}
            className="bg-trading-dark border border-panel-border rounded-[var(--radius-md)] px-2 py-1 text-[11px] text-text-primary outline-none hover:border-text-muted transition-colors cursor-pointer"
          >
            <option value="ALL">All Assets</option>
            <option value="BTC/USD">BTC/USD</option>
            <option value="ETH/USD">ETH/USD</option>
            <option value="EUR/USD">EUR/USD</option>
            <option value="XAU/USD">XAU/USD</option>
            <option value="GBP/USD">GBP/USD</option>
          </select>
        </div>

        <div className="flex items-center gap-1.5 bg-trading-dark border border-panel-border rounded-[var(--radius-md)] px-2.5 py-1 w-44">
          <Search className="w-3 h-3 text-text-muted flex-shrink-0" />
          <input
            type="text"
            placeholder="Search symbols..."
            className="bg-transparent text-[11px] text-text-primary placeholder:text-text-muted outline-none w-full"
          />
        </div>
      </div>

      {/* Center: Session + PnL + Countdown */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-text-muted" />
          <span className={`text-[10px] font-semibold ${sessionColor}`}>{session}</span>
        </div>

        <div className="h-3 w-px bg-panel-border" />

        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-text-muted uppercase">Equity</span>
          <span data-mono className="text-[12px] font-semibold text-text-primary">
            ${portfolio.totalEquity.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-text-muted uppercase">Daily P&L</span>
          <span
            data-mono
            className={`text-[12px] font-semibold ${
              portfolio.dailyPnl >= 0 ? 'text-profit' : 'text-loss'
            }`}
          >
            {portfolio.dailyPnl >= 0 ? '+' : ''}${portfolio.dailyPnl.toLocaleString()}
          </span>
        </div>

        <div className="h-3 w-px bg-panel-border" />

        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-text-muted uppercase">Next H4</span>
          <span data-mono className="text-[11px] font-semibold text-accent-cyan countdown-mono">{h4Countdown}</span>
        </div>
      </div>

      {/* Right: Connection + IST Clock */}
      <div className="flex items-center gap-3">
        <Badge variant={isConnected ? 'profit' : 'loss'} dot>
          {isConnected ? 'LIVE' : 'DISC'}
        </Badge>

        <div className="flex items-center gap-1.5 text-text-muted">
          <Clock className="w-3 h-3" />
          <span data-mono className="text-[11px]">{istTime}</span>
          <span className="text-[9px] text-text-muted">IST</span>
        </div>

        <button className="flex items-center gap-1 text-text-secondary hover:text-text-primary transition-colors duration-150 cursor-pointer">
          <div className="w-5 h-5 rounded-full bg-accent-blue/20 flex items-center justify-center">
            <span className="text-[9px] font-bold text-accent-blue">A</span>
          </div>
          <ChevronDown className="w-3 h-3" />
        </button>
      </div>
    </header>
  );
};
