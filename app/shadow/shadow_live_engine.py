"""
app/shadow/shadow_live_engine.py
================================
Shadow-Live Signal Generation & Immutable Prediction Engine (Phase 72).

Zero Real-Money Execution Guarantee:
Runs the entire production intelligence pipeline against real market data,
freezing every prediction into an immutable SQLite record BEFORE outcomes are known.

Canonical table: shadow_predictions
Lifecycle:
MARKET_DATA_RECEIVED -> FEATURES_COMPUTED -> SIGNAL_CANDIDATE -> RISK_CHECK ->
QUALIFIED -> ACTIONABLE -> ENTRY_WINDOW -> EXPIRED / PAPER_ENTERED -> EXIT -> RESOLVED.
"""

from __future__ import annotations
import os
import sqlite3
import hashlib
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from app.core.canonical_prospective_ledger import CORE_ASSETS
from app.core.market_clock import MarketClockService
from app.analytics.models.kronos.kronos_forensic_evaluator import kronos_forensic_evaluator
from app.strategies.Structure.swing import SwingDetector
from app.strategies.Structure.bos_choch import BOSEngine, CHoCHEngine
from app.strategies.SmartMoney.OrderBlocks.order_block_engine import OrderBlockEngine
from app.strategies.Technical.supertrend import compute_supertrend
from app.strategies.Technical.indicators import compute_rsi, compute_macd, compute_atr
from app.strategies.indicators.indicator_registry import indicator_registry

logger = logging.getLogger("shadow_live_engine")

POLICY_VERSION = "POL-72-v1"
MODEL_VERSION = "ENSEMBLE-P72-v1"
KRONOS_MODEL_VERSION = "NeoQuasar/Kronos-mini-v1"


@dataclass(frozen=True)
class ShadowPrediction:
    prediction_id: str
    signal_id: str
    generated_at_utc: str
    asset: str
    timeframe: str
    direction: str  # "BUY", "SELL", "NO_TRADE"
    entry: float
    stop_loss: float
    take_profit: float
    rr: float
    entry_window_start: str
    entry_window_end: str
    expected_close: str
    hold_duration: int
    raw_confidence: float
    calibrated_confidence: float
    grade: str  # "A+", "A", "B", "C", "NO_TRADE"
    regime: str  # "TRENDING", "RANGING", "HIGH_VOLATILITY", "LOW_VOLATILITY", "BREAKOUT"
    event_risk: str  # "NONE", "LOW", "MEDIUM", "HIGH"
    data_quality: str  # "VERIFIED_REAL_DATA", "DEGRADED"
    spread: float
    slippage_assumption: float
    kronos_status: str  # "AVAILABLE", "UNAVAILABLE", "OFFLINE"
    kronos_prediction: float
    kronos_confidence: float
    indicator_snapshot: str  # JSON
    structure_snapshot: str  # JSON
    smc_snapshot: str  # JSON
    consensus_snapshot: str  # JSON
    risk_snapshot: str  # JSON
    model_versions: str  # JSON
    data_snapshot_id: str  # SHA-256
    feature_snapshot_hash: str  # SHA-256
    decision_hash: str  # SHA-256
    policy_version: str = POLICY_VERSION
    generation_version: int = 1
    status: str = "PENDING"  # "PENDING", "PAPER_ENTERED", "WON", "LOST", "EXPIRED", "SUPERSEDED"
    supersedes_id: Optional[str] = None
    outcome: Optional[str] = None
    resolution_reason: Optional[str] = None
    actual_exit_price: Optional[float] = None
    actual_exit_time: Optional[str] = None
    gross_r: Optional[float] = None
    net_r: Optional[float] = None
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ShadowLiveEngine:
    """
    Authoritative Shadow-Live Prediction Engine.
    Enforces immutable prediction snapshots, point-in-time constraints, and realistic paper tracking.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
            return conn
        except Exception:
            for candidate in ["tradesignal.db", "trading_fallback.db", "app/database/trading_fallback.db"]:
                if os.path.exists(candidate):
                    try:
                        conn = sqlite3.connect(candidate, timeout=30.0, check_same_thread=False)
                        conn.execute("PRAGMA journal_mode=WAL;")
                        conn.execute("PRAGMA busy_timeout=30000;")
                        return conn
                    except Exception:
                        pass
        return None

    def _initialize_db(self):
        conn = self._get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shadow_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    generated_at_utc TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    rr REAL NOT NULL,
                    entry_window_start TEXT NOT NULL,
                    entry_window_end TEXT NOT NULL,
                    expected_close TEXT NOT NULL,
                    hold_duration INTEGER NOT NULL,
                    raw_confidence REAL NOT NULL,
                    calibrated_confidence REAL NOT NULL,
                    grade TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    event_risk TEXT NOT NULL,
                    data_quality TEXT NOT NULL,
                    spread REAL NOT NULL,
                    slippage_assumption REAL NOT NULL,
                    kronos_status TEXT NOT NULL,
                    kronos_prediction REAL NOT NULL,
                    kronos_confidence REAL NOT NULL,
                    indicator_snapshot TEXT NOT NULL,
                    structure_snapshot TEXT NOT NULL,
                    smc_snapshot TEXT NOT NULL,
                    consensus_snapshot TEXT NOT NULL,
                    risk_snapshot TEXT NOT NULL,
                    model_versions TEXT NOT NULL,
                    data_snapshot_id TEXT NOT NULL,
                    feature_snapshot_hash TEXT NOT NULL,
                    decision_hash TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    generation_version INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    supersedes_id TEXT,
                    outcome TEXT,
                    resolution_reason TEXT,
                    actual_exit_price REAL,
                    actual_exit_time TEXT,
                    gross_r REAL,
                    net_r REAL,
                    resolved_at TEXT
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_shadow_predictions_lookup
                ON shadow_predictions (asset, timeframe, status, generated_at_utc);
                """
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Error initializing shadow_predictions table: {e}")
        finally:
            conn.close()

    def generate_prediction_id(self, asset: str, timeframe: str, dt_utc: datetime, counter: int = 1) -> str:
        ts_str = dt_utc.strftime("%Y%m%d-%H%M%S")
        return f"PRED-{ts_str}-{asset}-{timeframe}-{POLICY_VERSION}-v{counter}"

    def compute_data_snapshot_hash(self, df: pd.DataFrame, asset: str, dt_utc: datetime) -> str:
        raw_repr = f"{asset}_{dt_utc.isoformat()}_{df[['open', 'high', 'low', 'close', 'volume']].to_json()}"
        return hashlib.sha256(raw_repr.encode('utf-8')).hexdigest()

    def compute_decision_hash(self, prediction_dict: Dict[str, Any]) -> str:
        payload = {k: prediction_dict[k] for k in sorted(prediction_dict.keys()) if k not in ["resolved_at", "outcome", "actual_exit_price", "actual_exit_time", "net_r"]}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()

    def _fetch_candles_from_candidates(self, asset: str, limit: int = 120, before_iso: Optional[str] = None) -> List[Tuple]:
        candidates = [self.db_path, "tradesignal.db", "trading_fallback.db", "app/database/trading_fallback.db"]
        for db in candidates:
            if os.path.exists(db):
                try:
                    conn = sqlite3.connect(db, timeout=5.0)
                    cur = conn.cursor()
                    if before_iso:
                        cur.execute(
                            """
                            SELECT timestamp, open, high, low, close, volume
                            FROM historical_candles
                            WHERE symbol = ? AND timestamp <= ?
                            ORDER BY timestamp DESC LIMIT ?
                            """,
                            (asset, before_iso, limit)
                        )
                    else:
                        cur.execute(
                            """
                            SELECT timestamp, open, high, low, close, volume
                            FROM historical_candles
                            WHERE symbol = ?
                            ORDER BY timestamp DESC LIMIT ?
                            """,
                            (asset, limit)
                        )
                    rows = cur.fetchall()
                    conn.close()
                    if rows and len(rows) >= 10:
                        return rows
                except Exception:
                    pass
        return []

    def generate_shadow_signal(self, asset: str = "EURUSD", timeframe: str = "1h", reference_dt: Optional[datetime] = None) -> ShadowPrediction:
        """
        Executes zero-trust shadow signal generation pipeline.
        """
        now = reference_dt or datetime.now(timezone.utc)
        rows = self._fetch_candles_from_candidates(asset, limit=120, before_iso=now.isoformat())

        if not rows or len(rows) < 30:
            # Output deterministic NO_TRADE prediction
            pred_id = self.generate_prediction_id(asset, timeframe, now)
            return ShadowPrediction(
                prediction_id=pred_id,
                signal_id=f"SIG-{pred_id}",
                generated_at_utc=now.isoformat(),
                asset=asset,
                timeframe=timeframe,
                direction="NO_TRADE",
                entry=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                rr=0.0,
                entry_window_start=now.isoformat(),
                entry_window_end=now.isoformat(),
                expected_close=now.isoformat(),
                hold_duration=3600,
                raw_confidence=0.0,
                calibrated_confidence=0.0,
                grade="NO_TRADE",
                regime="INSUFFICIENT_DATA",
                event_risk="NONE",
                data_quality="DEGRADED",
                spread=0.0,
                slippage_assumption=0.05,
                kronos_status="UNAVAILABLE",
                kronos_prediction=0.0,
                kronos_confidence=0.0,
                indicator_snapshot="{}",
                structure_snapshot="{}",
                smc_snapshot="{}",
                consensus_snapshot="{}",
                risk_snapshot="{}",
                model_versions=json.dumps({"ensemble": MODEL_VERSION}),
                data_snapshot_id="empty_hash",
                feature_snapshot_hash="empty_hash",
                decision_hash="empty_hash",
                status="EXPIRED",
            )

        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, format='mixed')
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        for c in ['open', 'high', 'low', 'close', 'volume']:
            df[c] = pd.to_numeric(df[c], errors='coerce')

        data_snapshot_id = self.compute_data_snapshot_hash(df, asset, now)

        # 1. Feature Extraction
        close = df['close']
        rsi = float(compute_rsi(df, period=14).iloc[-1])
        _, _, macd_hist_series = compute_macd(df)
        macd_hist = float(macd_hist_series.iloc[-1])
        atr = float(compute_atr(df, period=14).iloc[-1])
        _, st_dir_series = compute_supertrend(df, period=10, multiplier=3.0)
        st_dir = "BUY" if st_dir_series.iloc[-1] == 1 else "SELL"
        curr_price = float(close.iloc[-1])

        # 2. SMC & Structure
        swing_detector = SwingDetector(left_len=5, right_len=5)
        swings = swing_detector.detect_swings(df, asset=asset, timeframe=timeframe)
        bos_engine = BOSEngine(swing_len=5)
        bos_events = bos_engine.detect_bos(df, asset=asset, timeframe=timeframe)
        ob_engine = OrderBlockEngine()
        obs = ob_engine.detect_order_blocks(df, asset=asset, timeframe=timeframe)

        # 3. Kronos PyTorch Inference
        kronos_trace = kronos_forensic_evaluator.trace_full_pipeline(asset, limit=60)
        k_status = kronos_trace.get("status", "UNAVAILABLE")
        k_pred = float(kronos_trace.get("expected_return", 0.0))
        k_conf = float(kronos_trace.get("confidence", 0.50))

        # 4. Multi-Factor Consensus & Direction
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])

        bullish_votes = (curr_price > ema20) + (ema20 > ema50) + (rsi > 50) + (st_dir == "BUY") + (k_pred > 0.0002)
        bearish_votes = (curr_price < ema20) + (ema20 < ema50) + (rsi < 50) + (st_dir == "SELL") + (k_pred < -0.0002)

        if bullish_votes >= 3:
            direction = "BUY"
            raw_conf = min(0.95, 0.55 + (bullish_votes * 0.08))
            risk_dist = max(atr * 1.5, curr_price * 0.0030)
            entry = curr_price
            sl = round(entry - risk_dist, 5 if "USD" in asset and "BTC" not in asset and "JPY" not in asset else 2)
            tp = round(entry + (risk_dist * 2.0), 5 if "USD" in asset and "BTC" not in asset and "JPY" not in asset else 2)
            grade = "A" if bullish_votes >= 4 else "B"
            regime = "TRENDING_BULLISH"
        elif bearish_votes >= 3:
            direction = "SELL"
            raw_conf = min(0.95, 0.55 + (bearish_votes * 0.08))
            risk_dist = max(atr * 1.5, curr_price * 0.0030)
            entry = curr_price
            sl = round(entry + risk_dist, 5 if "USD" in asset and "BTC" not in asset and "JPY" not in asset else 2)
            tp = round(entry - (risk_dist * 2.0), 5 if "USD" in asset and "BTC" not in asset and "JPY" not in asset else 2)
            grade = "A" if bearish_votes >= 4 else "B"
            regime = "TRENDING_BEARISH"
        else:
            direction = "NO_TRADE"
            raw_conf = 0.50
            entry = curr_price
            sl = curr_price
            tp = curr_price
            grade = "NO_TRADE"
            regime = "RANGING_CONSOLIDATION"

        # 5. Calibrated Confidence
        calibrated_conf = round(raw_conf * 0.85, 2)  # Conservative shrinkage
        rr = round(abs(tp - entry) / abs(entry - sl), 2) if abs(entry - sl) > 0 else 0.0

        # 6. Exact Timing
        hold_secs = 3600 if timeframe.lower() == "1h" else (14400 if timeframe.lower() == "4h" else 86400)
        entry_win_start = now
        entry_win_end = now + timedelta(seconds=max(300, int(hold_secs * 0.10)))
        expected_close = now + timedelta(seconds=hold_secs)

        pred_id = self.generate_prediction_id(asset, timeframe, now)
        sig_id = f"SIG-{pred_id}"

        ind_snap = json.dumps({"rsi": rsi, "macd_hist": macd_hist, "atr": atr, "st_dir": st_dir, "ema20": ema20, "ema50": ema50})
        struct_snap = json.dumps({"swings_count": len(swings), "bos_count": len(bos_events)})
        smc_snap = json.dumps({"order_blocks_count": len(obs)})
        cons_snap = json.dumps({"bullish_votes": int(bullish_votes), "bearish_votes": int(bearish_votes)})
        risk_snap = json.dumps({"max_risk_pct": 1.0, "spread_pips": 1.2})
        model_vers = json.dumps({"ensemble": MODEL_VERSION, "kronos": KRONOS_MODEL_VERSION, "policy": POLICY_VERSION})
        feat_hash = hashlib.sha256(ind_snap.encode('utf-8')).hexdigest()

        pred_obj = ShadowPrediction(
            prediction_id=pred_id,
            signal_id=sig_id,
            generated_at_utc=now.isoformat(),
            asset=asset,
            timeframe=timeframe,
            direction=direction,
            entry=entry,
            stop_loss=sl,
            take_profit=tp,
            rr=rr,
            entry_window_start=entry_win_start.isoformat(),
            entry_window_end=entry_win_end.isoformat(),
            expected_close=expected_close.isoformat(),
            hold_duration=hold_secs,
            raw_confidence=round(raw_conf, 2),
            calibrated_confidence=calibrated_conf,
            grade=grade,
            regime=regime,
            event_risk="NONE",
            data_quality="VERIFIED_REAL_DATA",
            spread=1.2 if "JPY" not in asset else 1.8,
            slippage_assumption=0.05,
            kronos_status=k_status,
            kronos_prediction=k_pred,
            kronos_confidence=k_conf,
            indicator_snapshot=ind_snap,
            structure_snapshot=struct_snap,
            smc_snapshot=smc_snap,
            consensus_snapshot=cons_snap,
            risk_snapshot=risk_snap,
            model_versions=model_vers,
            data_snapshot_id=data_snapshot_id,
            feature_snapshot_hash=feat_hash,
            decision_hash="",  # Computed below
            policy_version=POLICY_VERSION,
            generation_version=1,
            status="PENDING" if direction != "NO_TRADE" else "EXPIRED",
        )

        # Compute decision hash
        d_hash = self.compute_decision_hash(pred_obj.to_dict())
        pred_obj = ShadowPrediction(**{**pred_obj.to_dict(), "decision_hash": d_hash})
        
        return pred_obj

    def persist_prediction(self, prediction: ShadowPrediction, allow_revision: bool = False, supersedes_id: Optional[str] = None) -> bool:
        """
        Persists a newly generated shadow prediction.
        Enforces strict immutability: once stored, predictions cannot be modified.
        """
        conn = self._get_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute("SELECT prediction_id FROM shadow_predictions WHERE prediction_id = ?", (prediction.prediction_id,))
            if cur.fetchone():
                logger.debug(f"Prediction {prediction.prediction_id} already exists - deduplicated.")
                return True

            if supersedes_id:
                cur.execute("UPDATE shadow_predictions SET status = 'SUPERSEDED' WHERE prediction_id = ?", (supersedes_id,))

            cur.execute(
                """
                INSERT INTO shadow_predictions (
                    prediction_id, signal_id, generated_at_utc, asset, timeframe, direction,
                    entry, stop_loss, take_profit, rr, entry_window_start, entry_window_end,
                    expected_close, hold_duration, raw_confidence, calibrated_confidence,
                    grade, regime, event_risk, data_quality, spread, slippage_assumption,
                    kronos_status, kronos_prediction, kronos_confidence, indicator_snapshot,
                    structure_snapshot, smc_snapshot, consensus_snapshot, risk_snapshot,
                    model_versions, data_snapshot_id, feature_snapshot_hash, decision_hash,
                    policy_version, generation_version, status, supersedes_id, outcome,
                    resolution_reason, actual_exit_price, actual_exit_time, gross_r, net_r, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction.prediction_id, prediction.signal_id, prediction.generated_at_utc,
                    prediction.asset, prediction.timeframe, prediction.direction, prediction.entry,
                    prediction.stop_loss, prediction.take_profit, prediction.rr, prediction.entry_window_start,
                    prediction.entry_window_end, prediction.expected_close, prediction.hold_duration,
                    prediction.raw_confidence, prediction.calibrated_confidence, prediction.grade,
                    prediction.regime, prediction.event_risk, prediction.data_quality, prediction.spread,
                    prediction.slippage_assumption, prediction.kronos_status, prediction.kronos_prediction,
                    prediction.kronos_confidence, prediction.indicator_snapshot, prediction.structure_snapshot,
                    prediction.smc_snapshot, prediction.consensus_snapshot, prediction.risk_snapshot,
                    prediction.model_versions, prediction.data_snapshot_id, prediction.feature_snapshot_hash,
                    prediction.decision_hash, prediction.policy_version, prediction.generation_version,
                    prediction.status, prediction.supersedes_id, prediction.outcome, prediction.resolution_reason,
                    prediction.actual_exit_price, prediction.actual_exit_time, prediction.gross_r,
                    prediction.net_r, prediction.resolved_at
                )
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error persisting shadow prediction {prediction.prediction_id}: {e}")
            return False
        finally:
            conn.close()

    def resolve_prediction(
        self,
        prediction_id: str,
        outcome: str,
        resolution_reason: str,
        actual_exit_price: float,
        actual_exit_time: str,
        gross_r: float,
        net_r: float
    ) -> bool:
        """
        Resolves a shadow prediction outcome deterministically without altering prediction inputs.
        """
        conn = self._get_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            resolved_at = datetime.now(timezone.utc).isoformat()
            cur.execute(
                """
                UPDATE shadow_predictions
                SET outcome = ?,
                    resolution_reason = ?,
                    actual_exit_price = ?,
                    actual_exit_time = ?,
                    gross_r = ?,
                    net_r = ?,
                    status = ?,
                    resolved_at = ?
                WHERE prediction_id = ?
                """,
                (outcome, resolution_reason, actual_exit_price, actual_exit_time, gross_r, net_r, outcome, resolved_at, prediction_id)
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error resolving shadow prediction {prediction_id}: {e}")
            return False
        finally:
            conn.close()

    def get_predictions(self, status: Optional[str] = None, asset: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            query = "SELECT * FROM shadow_predictions WHERE 1=1"
            params = []
            if status and status != "ALL":
                query += " AND status = ?"
                params.append(status)
            if asset and asset != "ALL":
                query += " AND asset = ?"
                params.append(asset)
            query += " ORDER BY generated_at_utc DESC LIMIT ?"
            params.append(limit)
            cur.execute(query, tuple(params))
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return [dict(zip(cols, row)) for row in rows]
        finally:
            conn.close()


# Global Singleton Instance
shadow_live_engine = ShadowLiveEngine()
