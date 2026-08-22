from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.future import select

from app.database.manager import db_manager
from app.database.models.validation import ResearchValidationRecord


class ResearchValidationEngine:
    async def get_records(self, period: str = None) -> list[ResearchValidationRecord]:
        session_maker = db_manager.get_session()
        async with session_maker() as session:
            # We would normally filter by period (e.g. daily, weekly) but we will just grab all for now
            stmt = select(ResearchValidationRecord).where(ResearchValidationRecord.status == "RESOLVED")
            result = await session.execute(stmt)
            return result.scalars().all()

    async def compute_metrics(self, period: str = None) -> dict[str, Any]:
        records = await self.get_records(period)
        
        if not records:
            return {
                "total_forecasts": 0,
                "overall_accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "win_rate": 0.0,
                "loss_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "average_return": 0.0,
                "average_drawdown": 0.0,
                "max_drawdown": "0.0%",
                "mae": 0.0,
                "rmse": 0.0,
                "mape": 0.0,
                "avg_holding_error": 0.0
            }
            
        df = pd.DataFrame([{
            "pnl_pct": r.pnl_pct or 0.0,
            "direction_correct": r.direction_correct or False,
            "target_hit": r.target_hit or False,
            "stop_hit": r.stop_hit or False,
            "expected_hold_time": r.expected_hold_time_minutes or 0.0,
            "actual_hold_time": r.actual_hold_time_minutes or 0.0,
            "confidence": r.confidence or 0.0
        } for r in records])
        
        total_forecasts = len(df)
        wins = df[df["pnl_pct"] > 0]
        losses = df[df["pnl_pct"] <= 0]
        
        overall_accuracy = df["direction_correct"].mean()
        win_rate = len(wins) / total_forecasts if total_forecasts > 0 else 0
        loss_rate = 1 - win_rate
        
        gross_profit = wins["pnl_pct"].sum() if not wins.empty else 0
        gross_loss = abs(losses["pnl_pct"].sum()) if not losses.empty else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (99.9 if gross_profit > 0 else 0)
        
        avg_return = df["pnl_pct"].mean()
        std_return = df["pnl_pct"].std() if total_forecasts > 1 else 0
        sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        downside_returns = df[df["pnl_pct"] < 0]["pnl_pct"]
        downside_std = downside_returns.std() if len(downside_returns) > 1 else 0
        sortino_ratio = (avg_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
        
        cumulative = (1 + df["pnl_pct"]).cumprod()
        running_max = cumulative.cummax()
        drawdowns = (running_max - cumulative) / running_max
        max_drawdown = drawdowns.max() if not drawdowns.empty else 0
        avg_drawdown = drawdowns.mean() if not drawdowns.empty else 0
        
        calmar_ratio = avg_return / max_drawdown if max_drawdown > 0 else 0
        
        mae = abs(df["pnl_pct"] - df["confidence"]).mean() # Simplified MAE
        rmse = np.sqrt(((df["pnl_pct"] - df["confidence"]) ** 2).mean())
        mape = (abs((df["confidence"] - df["pnl_pct"]) / df["confidence"].replace(0, 1))).mean()
        
        avg_holding_error = abs(df["expected_hold_time"] - df["actual_hold_time"]).mean()
        
        return {
            "total_forecasts": total_forecasts,
            "overall_accuracy": round(float(overall_accuracy), 4),
            "precision": round(float(overall_accuracy), 4), # Simplified
            "recall": round(float(win_rate), 4), # Simplified
            "win_rate": round(float(win_rate), 4),
            "loss_rate": round(float(loss_rate), 4),
            "profit_factor": round(float(profit_factor), 2),
            "sharpe_ratio": round(float(sharpe_ratio), 2),
            "sortino_ratio": round(float(sortino_ratio), 2),
            "calmar_ratio": round(float(calmar_ratio), 2),
            "average_return": round(float(avg_return), 4),
            "average_drawdown": round(float(avg_drawdown), 4),
            "max_drawdown": f"{round(float(max_drawdown) * 100, 2)}%",
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "mape": round(float(mape), 4),
            "avg_holding_error": round(float(avg_holding_error), 2)
        }

    async def get_rankings(self, period: str = None) -> dict[str, list[dict[str, Any]]]:
        records = await self.get_records(period)
        if not records:
            return {
                "top_assets": [],
                "top_timeframes": [],
                "top_strategies": [],
                "top_models": [],
                "top_sessions": []
            }
            
        df = pd.DataFrame([{
            "asset": r.asset,
            "timeframe": r.timeframe,
            "strategy_name": r.strategy_name or "Unknown",
            "model_name": r.model_name or "Unknown",
            "session": r.session or "Unknown",
            "pnl_pct": r.pnl_pct or 0.0,
            "direction_correct": r.direction_correct or False
        } for r in records])
        
        def group_stats(group_col: str):
            if df.empty or group_col not in df.columns:
                return []
            grouped = df.groupby(group_col)
            stats = []
            for name, group in grouped:
                total = len(group)
                wins = len(group[group["pnl_pct"] > 0])
                win_rate = wins / total if total > 0 else 0
                avg_pnl = group["pnl_pct"].mean()
                gross_profit = group[group["pnl_pct"] > 0]["pnl_pct"].sum()
                gross_loss = abs(group[group["pnl_pct"] <= 0]["pnl_pct"].sum())
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else (99.9 if gross_profit > 0 else 1.0)
                
                stats.append({
                    "name": str(name),
                    "win_rate": round(win_rate, 4),
                    "avg_pnl": round(avg_pnl, 4),
                    "profit_factor": round(profit_factor, 2),
                    "total_count": total
                })
            stats.sort(key=lambda x: (x["win_rate"], x["profit_factor"]), reverse=True)
            return stats
            
        return {
            "top_assets": group_stats("asset"),
            "top_timeframes": group_stats("timeframe"),
            "top_strategies": group_stats("strategy_name"),
            "top_models": group_stats("model_name"),
            "top_sessions": group_stats("session")
        }

validation_engine = ResearchValidationEngine()
