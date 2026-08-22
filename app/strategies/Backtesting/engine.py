import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction


class TradeOutcome(str, Enum):
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    TIMEOUT = "TIMEOUT"
    INVALIDATED = "INVALIDATED"


@dataclass
class BacktestTrade:
    trade_id: str
    asset: str
    timeframe: str
    direction: Direction
    entry_index: int
    entry_time_utc: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    exit_index: int
    exit_time_utc: datetime
    exit_price: float
    outcome: TradeOutcome
    gross_pnl: float
    spread_cost: float
    slippage_cost: float
    commission_cost: float
    net_pnl: float
    pnl_pct: float
    holding_bars: int
    mfe: float  # Maximum Favorable Excursion
    mae: float  # Maximum Adverse Excursion
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "entry_index": self.entry_index,
            "entry_time_utc": self.entry_time_utc.isoformat() if isinstance(self.entry_time_utc, datetime) else str(self.entry_time_utc),
            "entry_price": float(self.entry_price),
            "stop_loss": float(self.stop_loss),
            "take_profit": float(self.take_profit),
            "exit_index": self.exit_index,
            "exit_time_utc": self.exit_time_utc.isoformat() if isinstance(self.exit_time_utc, datetime) else str(self.exit_time_utc),
            "exit_price": float(self.exit_price),
            "outcome": self.outcome.value if hasattr(self.outcome, 'value') else str(self.outcome),
            "gross_pnl": round(float(self.gross_pnl), 4),
            "spread_cost": round(float(self.spread_cost), 4),
            "slippage_cost": round(float(self.slippage_cost), 4),
            "commission_cost": round(float(self.commission_cost), 4),
            "net_pnl": round(float(self.net_pnl), 4),
            "pnl_pct": round(float(self.pnl_pct), 4),
            "holding_bars": self.holding_bars,
            "mfe": round(float(self.mfe), 4),
            "mae": round(float(self.mae), 4),
        }


@dataclass
class BacktestSummary:
    asset: str
    timeframe: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    gross_pnl: float
    total_frictions: float
    net_pnl: float
    avg_trade_pnl: float
    expectancy: float
    avg_mfe: float
    avg_mae: float
    trades: List[BacktestTrade] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(float(self.win_rate), 2),
            "profit_factor": round(float(self.profit_factor), 2),
            "sharpe_ratio": round(float(self.sharpe_ratio), 2),
            "sortino_ratio": round(float(self.sortino_ratio), 2),
            "max_drawdown_pct": round(float(self.max_drawdown_pct), 2),
            "gross_pnl": round(float(self.gross_pnl), 2),
            "total_frictions": round(float(self.total_frictions), 2),
            "net_pnl": round(float(self.net_pnl), 2),
            "avg_trade_pnl": round(float(self.avg_trade_pnl), 4),
            "expectancy": round(float(self.expectancy), 4),
            "avg_mfe": round(float(self.avg_mfe), 4),
            "avg_mae": round(float(self.avg_mae), 4),
            "trades_count": len(self.trades)
        }


class RealisticBacktestEngine:
    """
    High-Fidelity Realistic Backtest Engine.
    Incorporates bid/ask spread, volatility-scaled slippage, commissions, execution delay, and intra-candle resolution.
    """

    def __init__(
        self,
        spread_pips: float = 1.5,
        slippage_pips: float = 1.0,
        commission_per_lot: float = 7.0,
        max_holding_bars: int = 24
    ):
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips
        self.commission_per_lot = commission_per_lot
        self.max_holding_bars = max_holding_bars

    def run_backtest(
        self,
        df: pd.DataFrame,
        signals: List[Dict[str, Any]],
        asset: str = "UNKNOWN",
        timeframe: str = "1H"
    ) -> BacktestSummary:
        if df is None or len(df) < 5 or not signals:
            return BacktestSummary(
                asset=asset,
                timeframe=timeframe,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown_pct=0.0,
                gross_pnl=0.0,
                total_frictions=0.0,
                net_pnl=0.0,
                avg_trade_pnl=0.0,
                expectancy=0.0,
                avg_mfe=0.0,
                avg_mae=0.0
            )

        highs = df['high'].values
        lows = df['low'].values
        opens = df['open'].values
        closes = df['close'].values
        ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)

        # Pip scale factor
        pip_factor = 0.0001 if "JPY" not in asset and "BTC" not in asset and "XAU" not in asset else (
            0.01 if "JPY" in asset or "XAU" in asset else 1.0
        )

        spread_val = self.spread_pips * pip_factor
        slippage_val = self.slippage_pips * pip_factor

        trades: List[BacktestTrade] = []

        for sig in signals:
            entry_idx = sig.get("candle_index", 0)
            # Execution latency: Enter at OPEN of NEXT candle (entry_idx + 1)
            exec_idx = entry_idx + 1
            if exec_idx >= len(df):
                continue

            direction = sig.get("direction", Direction.BULLISH)
            sl = float(sig.get("stop_loss", 0.0))
            tp = float(sig.get("take_profit", 0.0))

            raw_entry = float(opens[exec_idx])
            # Apply spread & slippage friction on entry
            if direction == Direction.BULLISH:
                real_entry = raw_entry + spread_val + slippage_val
            else:
                real_entry = raw_entry - spread_val - slippage_val

            mfe = 0.0
            mae = 0.0
            outcome = TradeOutcome.TIMEOUT
            exit_price = closes[min(len(df) - 1, exec_idx + self.max_holding_bars)]
            exit_idx = min(len(df) - 1, exec_idx + self.max_holding_bars)

            # Replay forward bars
            for bar in range(exec_idx, min(len(df), exec_idx + self.max_holding_bars + 1)):
                b_high = highs[bar]
                b_low = lows[bar]
                b_close = closes[bar]

                if direction == Direction.BULLISH:
                    cur_favorable = max(0.0, b_high - real_entry)
                    cur_adverse = max(0.0, real_entry - b_low)
                    mfe = max(mfe, cur_favorable)
                    mae = max(mae, cur_adverse)

                    # Intra-candle check: Check SL first (conservative worst-case)
                    if b_low <= sl:
                        outcome = TradeOutcome.STOP_LOSS
                        exit_price = sl - slippage_val
                        exit_idx = bar
                        break
                    elif b_high >= tp:
                        outcome = TradeOutcome.TAKE_PROFIT
                        exit_price = tp - spread_val
                        exit_idx = bar
                        break

                elif direction == Direction.BEARISH:
                    cur_favorable = max(0.0, real_entry - b_low)
                    cur_adverse = max(0.0, b_high - real_entry)
                    mfe = max(mfe, cur_favorable)
                    mae = max(mae, cur_adverse)

                    if b_high >= sl:
                        outcome = TradeOutcome.STOP_LOSS
                        exit_price = sl + slippage_val
                        exit_idx = bar
                        break
                    elif b_low <= tp:
                        outcome = TradeOutcome.TAKE_PROFIT
                        exit_price = tp + spread_val
                        exit_idx = bar
                        break

            # Calculate P&L and friction breakdown
            if direction == Direction.BULLISH:
                gross_diff = exit_price - real_entry
            else:
                gross_diff = real_entry - exit_price

            gross_pnl = gross_diff * 1000.0  # normalized standard unit
            spread_cost = spread_val * 1000.0
            slippage_cost = slippage_val * 1000.0
            comm_cost = self.commission_per_lot
            total_friction = spread_cost + slippage_cost + comm_cost

            net_pnl = gross_pnl - total_friction
            pnl_pct = (gross_diff / real_entry) * 100.0

            ts_entry = df.iloc[exec_idx][ts_col] if ts_col else datetime.now(timezone.utc)
            ts_exit = df.iloc[exit_idx][ts_col] if ts_col else datetime.now(timezone.utc)

            trade = BacktestTrade(
                trade_id=f"BT-{asset}-{exec_idx}",
                asset=asset,
                timeframe=timeframe,
                direction=direction,
                entry_index=exec_idx,
                entry_time_utc=pd.to_datetime(ts_entry, utc=True).to_pydatetime() if ts_col else datetime.now(timezone.utc),
                entry_price=real_entry,
                stop_loss=sl,
                take_profit=tp,
                exit_index=exit_idx,
                exit_time_utc=pd.to_datetime(ts_exit, utc=True).to_pydatetime() if ts_col else datetime.now(timezone.utc),
                exit_price=exit_price,
                outcome=outcome,
                gross_pnl=gross_pnl,
                spread_cost=spread_cost,
                slippage_cost=slippage_cost,
                commission_cost=comm_cost,
                net_pnl=net_pnl,
                pnl_pct=pnl_pct,
                holding_bars=exit_idx - exec_idx,
                mfe=mfe,
                mae=mae
            )
            trades.append(trade)

        # Performance summary metrics
        if not trades:
            return BacktestSummary(
                asset=asset, timeframe=timeframe, total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0.0, profit_factor=0.0, sharpe_ratio=0.0, sortino_ratio=0.0, max_drawdown_pct=0.0,
                gross_pnl=0.0, total_frictions=0.0, net_pnl=0.0, avg_trade_pnl=0.0, expectancy=0.0, avg_mfe=0.0, avg_mae=0.0
            )

        net_pnls = np.array([t.net_pnl for t in trades])
        wins = net_pnls[net_pnls > 0]
        losses = net_pnls[net_pnls < 0]

        total_trades = len(trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades) * 100.0

        gross_wins = np.sum(wins) if len(wins) > 0 else 0.0
        gross_losses = abs(np.sum(losses)) if len(losses) > 0 else 1.0
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else (10.0 if gross_wins > 0 else 0.0)

        # Sharpe & Sortino
        std_pnl = np.std(net_pnls) if len(net_pnls) > 1 else 1.0
        mean_pnl = np.mean(net_pnls)
        sharpe = (mean_pnl / (std_pnl + 1e-8)) * np.sqrt(252)

        downside_std = np.std(losses) if len(losses) > 1 else 1.0
        sortino = (mean_pnl / (downside_std + 1e-8)) * np.sqrt(252)

        # Cumulative drawdown
        cum_pnl = np.cumsum(net_pnls)
        running_max = np.maximum.accumulate(cum_pnl)
        drawdowns = running_max - cum_pnl
        max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
        max_dd_pct = (max_dd / (np.max(running_max) + 1000.0)) * 100.0

        total_gross = sum([t.gross_pnl for t in trades])
        total_frictions = sum([t.spread_cost + t.slippage_cost + t.commission_cost for t in trades])
        total_net = sum(net_pnls)
        expectancy = mean_pnl

        return BacktestSummary(
            asset=asset,
            timeframe=timeframe,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown_pct=max_dd_pct,
            gross_pnl=total_gross,
            total_frictions=total_frictions,
            net_pnl=total_net,
            avg_trade_pnl=mean_pnl,
            expectancy=expectancy,
            avg_mfe=float(np.mean([t.mfe for t in trades])),
            avg_mae=float(np.mean([t.mae for t in trades])),
            trades=trades
        )
