"""
app/core/prospective_signal_journal.py
======================================
Permanent Immutable Prospective Signal Journal for TradeSignalAI-v3 (Phase 67).

Stores and preserves every prospective signal exactly as generated at T0.
Enforces hard append-only immutability guarantees: historical prediction parameters
can NEVER be mutated or retroactively updated.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
import hashlib
import json
import sqlite3
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("prospective_signal_journal")


class ImmutableSignalError(Exception):
    """Raised when an illegal attempt is made to overwrite or modify an immutable historical signal prediction."""
    pass


@dataclass(frozen=True)
class ProspectiveSignalRecord:
    """
    Complete, frozen prospective signal record created at generation time (T0).
    """
    # IDENTITY
    signal_id: str
    asset: str
    timeframe: str
    horizon: str
    direction: str  # "BUY", "SELL", "WAIT"
    signal_type: str  # "CALL", "PUT", "NO_TRADE"
    generated_at: str

    # CAUSALITY
    information_cutoff_time: str
    canonical_snapshot_id: str
    canonical_snapshot_hash: str
    market_data_version: str
    git_commit: str
    config_hash: str
    model_version: str
    policy_version: str

    # PRICE
    current_price: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    expiry_time: str

    # PROBABILITY
    raw_confidence: float
    calibrated_probability: float
    p_tp_first: float
    p_sl_first: float
    p_time_exit: float

    # EXPECTED VALUE
    expected_gross_r: float
    expected_net_r: float

    # SIGNAL QUALITY
    signal_strength: int  # 0 to 100
    quality_grade: str  # "A+", "A", "B", "C", "WATCH", "REJECTED"
    consensus_pct: float
    evidence_cluster_count: int
    htf_alignment_score: float
    mtf_conflict_score: float

    # CONTEXT
    market_regime: str
    session: str
    weekday: str
    event_risk: str
    volatility_regime: str
    trend_state: str
    structure_state: str
    liquidity_state: str

    # EVIDENCE
    evidence_clusters: Dict[str, Any]

    # DECISION
    decision: str  # "TAKE_NOW", "WATCHLIST", "NO_TRADE"
    decision_trace: Dict[str, Any]
    rejection_reason: Optional[str] = None

    # PROVENANCE
    content_hash: str = field(default="")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass(frozen=True)
class ProspectiveOutcomeRecord:
    """
    Append-only resolution outcome record for a prospective signal evaluated post-T0.
    """
    signal_id: str
    outcome: str  # "WON", "LOST", "TIME_EXIT", "AMBIGUOUS"
    exit_price: float
    exit_time: str
    resolution_reason: str
    gross_pnl: float
    spread_paid: float
    slippage_paid: float
    fees_paid: float
    realized_net_r: float
    mfe_r: float  # Maximum Favorable Excursion in R-multiples
    mae_r: float  # Maximum Adverse Excursion in R-multiples
    time_in_trade_minutes: float
    resolved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProspectiveSignalJournal:
    """
    Permanent append-only journal and outcome manager for prospective signals.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path
        self._journal_cache: Dict[str, ProspectiveSignalRecord] = {}
        self._outcome_cache: Dict[str, ProspectiveOutcomeRecord] = {}
        self._initialize_tables()
        self._load_from_db()

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        for candidate in [self.db_path, "trading_fallback.db", "app/database/trading_fallback.db"]:
            if os.path.exists(candidate):
                try:
                    conn = sqlite3.connect(candidate, timeout=30.0, check_same_thread=False)
                    conn.execute("PRAGMA busy_timeout=30000;")
                    return conn
                except Exception:
                    pass
        return None

    def _initialize_tables(self):
        """Creates the permanent journal and outcome tables with strict integrity indexes."""
        conn = self._get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS prospective_signal_journal (
                        signal_id TEXT PRIMARY KEY,
                        asset TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        horizon TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        generated_at TEXT NOT NULL,
                        information_cutoff_time TEXT NOT NULL,
                        canonical_snapshot_id TEXT NOT NULL,
                        canonical_snapshot_hash TEXT NOT NULL,
                        market_data_version TEXT NOT NULL,
                        git_commit TEXT NOT NULL,
                        config_hash TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        policy_version TEXT NOT NULL,
                        current_price REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        stop_loss REAL NOT NULL,
                        take_profit REAL NOT NULL,
                        risk_reward REAL NOT NULL,
                        expiry_time TEXT NOT NULL,
                        raw_confidence REAL NOT NULL,
                        calibrated_probability REAL NOT NULL,
                        p_tp_first REAL NOT NULL,
                        p_sl_first REAL NOT NULL,
                        p_time_exit REAL NOT NULL,
                        expected_gross_r REAL NOT NULL,
                        expected_net_r REAL NOT NULL,
                        signal_strength INTEGER NOT NULL,
                        quality_grade TEXT NOT NULL,
                        consensus_pct REAL NOT NULL,
                        evidence_cluster_count INTEGER NOT NULL,
                        htf_alignment_score REAL NOT NULL,
                        mtf_conflict_score REAL NOT NULL,
                        market_regime TEXT NOT NULL,
                        session TEXT NOT NULL,
                        weekday TEXT NOT NULL,
                        event_risk TEXT NOT NULL,
                        volatility_regime TEXT NOT NULL,
                        trend_state TEXT NOT NULL,
                        structure_state TEXT NOT NULL,
                        liquidity_state TEXT NOT NULL,
                        evidence_clusters TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        decision_trace TEXT NOT NULL,
                        rejection_reason TEXT,
                        content_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS prospective_outcomes (
                        signal_id TEXT PRIMARY KEY,
                        outcome TEXT NOT NULL,
                        exit_price REAL NOT NULL,
                        exit_time TEXT NOT NULL,
                        resolution_reason TEXT NOT NULL,
                        gross_pnl REAL NOT NULL,
                        spread_paid REAL NOT NULL,
                        slippage_paid REAL NOT NULL,
                        fees_paid REAL NOT NULL,
                        realized_net_r REAL NOT NULL,
                        mfe_r REAL NOT NULL,
                        mae_r REAL NOT NULL,
                        time_in_trade_minutes REAL NOT NULL,
                        resolved_at TEXT NOT NULL,
                        FOREIGN KEY(signal_id) REFERENCES prospective_signal_journal(signal_id)
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_psj_asset ON prospective_signal_journal(asset)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_psj_timeframe ON prospective_signal_journal(timeframe)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_psj_grade ON prospective_signal_journal(quality_grade)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_psj_generated ON prospective_signal_journal(generated_at)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pso_outcome ON prospective_outcomes(outcome)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_pso_resolved ON prospective_outcomes(resolved_at)")
                conn.commit()
            except Exception as e:
                logger.debug(f"Error initializing journal tables: {e}")
            finally:
                conn.close()

    def _load_from_db(self):
        """Loads records from database on startup."""
        conn = self._get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT signal_id, outcome, exit_price, exit_time, resolution_reason, gross_pnl, spread_paid, slippage_paid, fees_paid, realized_net_r, mfe_r, mae_r, time_in_trade_minutes, resolved_at FROM prospective_outcomes")
                for row in cur.fetchall():
                    self._outcome_cache[row[0]] = ProspectiveOutcomeRecord(
                        signal_id=row[0], outcome=row[1], exit_price=row[2], exit_time=row[3],
                        resolution_reason=row[4], gross_pnl=row[5], spread_paid=row[6], slippage_paid=row[7],
                        fees_paid=row[8], realized_net_r=row[9], mfe_r=row[10], mae_r=row[11],
                        time_in_trade_minutes=row[12], resolved_at=row[13]
                    )
            except Exception as e:
                logger.debug(f"Error loading outcomes: {e}")
            finally:
                conn.close()

    def journal_signal(self, record: ProspectiveSignalRecord) -> ProspectiveSignalRecord:
        """
        Appends a newly generated signal into the permanent prospective journal.
        Guarantees idempotency and rejects attempts to modify existing prediction records.
        """
        if record.signal_id in self._journal_cache:
            existing = self._journal_cache[record.signal_id]
            # Check for immutable prediction parameter modification attempt
            if (
                existing.entry_price != record.entry_price or
                existing.stop_loss != record.stop_loss or
                existing.take_profit != record.take_profit or
                existing.direction != record.direction or
                existing.calibrated_probability != record.calibrated_probability
            ):
                raise ImmutableSignalError(
                    f"IMMUTABLE_SIGNAL_VIOLATION: Attempted to mutate historical prediction fields of signal {record.signal_id}!"
                )
            return existing

        self._journal_cache[record.signal_id] = record
        conn = self._get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT OR IGNORE INTO prospective_signal_journal (
                        signal_id, asset, timeframe, horizon, direction, signal_type,
                        generated_at, information_cutoff_time, canonical_snapshot_id,
                        canonical_snapshot_hash, market_data_version, git_commit, config_hash,
                        model_version, policy_version, current_price, entry_price, stop_loss,
                        take_profit, risk_reward, expiry_time, raw_confidence, calibrated_probability,
                        p_tp_first, p_sl_first, p_time_exit, expected_gross_r, expected_net_r,
                        signal_strength, quality_grade, consensus_pct, evidence_cluster_count,
                        htf_alignment_score, mtf_conflict_score, market_regime, session, weekday,
                        event_risk, volatility_regime, trend_state, structure_state, liquidity_state,
                        evidence_clusters, decision, decision_trace, rejection_reason,
                        content_hash, created_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        record.signal_id, record.asset, record.timeframe, record.horizon,
                        record.direction, record.signal_type, record.generated_at,
                        record.information_cutoff_time, record.canonical_snapshot_id,
                        record.canonical_snapshot_hash, record.market_data_version,
                        record.git_commit, record.config_hash, record.model_version,
                        record.policy_version, record.current_price, record.entry_price,
                        record.stop_loss, record.take_profit, record.risk_reward,
                        record.expiry_time, record.raw_confidence, record.calibrated_probability,
                        record.p_tp_first, record.p_sl_first, record.p_time_exit,
                        record.expected_gross_r, record.expected_net_r, record.signal_strength,
                        record.quality_grade, record.consensus_pct, record.evidence_cluster_count,
                        record.htf_alignment_score, record.mtf_conflict_score, record.market_regime,
                        record.session, record.weekday, record.event_risk, record.volatility_regime,
                        record.trend_state, record.structure_state, record.liquidity_state,
                        json.dumps(record.evidence_clusters), record.decision,
                        json.dumps(record.decision_trace), record.rejection_reason,
                        record.content_hash, record.created_at
                    ),
                )
                conn.commit()
            except Exception as e:
                logger.debug(f"Error persisting prospective signal {record.signal_id}: {e}")
            finally:
                conn.close()

        return record

    def record_outcome(self, outcome: ProspectiveOutcomeRecord) -> ProspectiveOutcomeRecord:
        """
        Appends post-T0 outcome resolution data into the prospective outcomes ledger.
        """
        self._outcome_cache[outcome.signal_id] = outcome
        conn = self._get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT OR REPLACE INTO prospective_outcomes (
                        signal_id, outcome, exit_price, exit_time, resolution_reason,
                        gross_pnl, spread_paid, slippage_paid, fees_paid, realized_net_r,
                        mfe_r, mae_r, time_in_trade_minutes, resolved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        outcome.signal_id, outcome.outcome, outcome.exit_price, outcome.exit_time,
                        outcome.resolution_reason, outcome.gross_pnl, outcome.spread_paid,
                        outcome.slippage_paid, outcome.fees_paid, outcome.realized_net_r,
                        outcome.mfe_r, outcome.mae_r, outcome.time_in_trade_minutes, outcome.resolved_at
                    ),
                )
                conn.commit()
            except Exception as e:
                logger.debug(f"Error persisting outcome for {outcome.signal_id}: {e}")
            finally:
                conn.close()

        return outcome

    def get_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a prospective signal combined with its outcome if resolved."""
        if signal_id in self._journal_cache:
            sig_dict = self._journal_cache[signal_id].to_dict()
            if signal_id in self._outcome_cache:
                sig_dict["outcome_details"] = self._outcome_cache[signal_id].to_dict()
                sig_dict["status"] = self._outcome_cache[signal_id].outcome
            else:
                sig_dict["status"] = "LIVE"
            return sig_dict
        return None

    def get_all_signals(
        self,
        asset: Optional[str] = None,
        timeframe: Optional[str] = None,
        quality: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Returns filtered list of prospective signals."""
        signals_list = []
        for sig_id, sig in list(self._journal_cache.items())[-limit * 2:]:
            if asset and asset != "ALL" and sig.asset != asset:
                continue
            if timeframe and timeframe != "ALL" and sig.timeframe != timeframe:
                continue
            if quality and quality != "ALL" and sig.quality_grade != quality:
                continue

            current_status = self._outcome_cache[sig_id].outcome if sig_id in self._outcome_cache else "LIVE"
            if status and status != "ALL" and current_status != status:
                continue

            sig_dict = sig.to_dict()
            sig_dict["status"] = current_status
            if sig_id in self._outcome_cache:
                sig_dict["outcome_details"] = self._outcome_cache[sig_id].to_dict()
                sig_dict["realized_net_r"] = self._outcome_cache[sig_id].realized_net_r
            signals_list.append(sig_dict)

        return signals_list[-limit:]


prospective_signal_journal = ProspectiveSignalJournal()
