"""
app/core/canonical_prospective_ledger.py
=========================================
Authoritative Canonical Prospective Signal Ledger for TradeSignalAI-v3 (Phase 70).

Single Source of Truth for:
- Deterministic Prospective Signal Generation (Immutable T0 prediction records)
- Zero-Lookahead Signal Identity: asset + timeframe + candle_close_utc + policy_version + generation_version
- Strict Ledger Deduplication & Unique Composite Constraints
- Revisioning Schema via supersedes_id and generation_version
- Deterministic Candle-Based Outcome Resolution (Conservative ambiguous bar rule)
- Exact Window Timing (Entry Window, Preferred Entry, Expected Hold, Expected/Max Exit)
- Unified Historical Querying (Today, Yesterday, 7D, 30D, All)
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
import hashlib
import json
import math
import os
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("canonical_prospective_ledger")

# Default Core Assets & Timeframes
CORE_ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", "XAUUSD", "NAS100", "SPX500"]
SUPPORTED_TIMEFRAMES = ["5m", "15m", "30m", "1H", "2H", "4H", "12H", "1D", "SWING"]

# Timeframe Duration & Expiry Mapping
TF_SECONDS = {
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1H": 3600,
    "2H": 7200,
    "4H": 14400,
    "12H": 43200,
    "1D": 86400,
    "SWING": 259200,
}

# State Machine Constants
STATUS_GENERATED = "GENERATED"
STATUS_UPCOMING = "UPCOMING"
STATUS_ENTRY_WINDOW = "ENTRY_WINDOW"
STATUS_ACTIVE = "ACTIVE"
STATUS_TARGET_HIT = "TARGET_HIT"
STATUS_STOP_HIT = "STOP_HIT"
STATUS_TIME_EXIT = "TIME_EXIT"
STATUS_EXPIRED = "EXPIRED"
STATUS_CANCELLED = "CANCELLED"
STATUS_RESOLVED = "RESOLVED"
STATUS_SUPERSEDED = "SUPERSEDED"

# Outcomes
OUTCOME_WON = "WON"
OUTCOME_LOST = "LOST"
OUTCOME_TIME_EXIT = "TIME_EXIT"
OUTCOME_AMBIGUOUS = "AMBIGUOUS"


class ImmutableSignalError(Exception):
    """Raised when an illegal mutation of an immutable prediction is attempted."""
    pass


@dataclass(frozen=True)
class CanonicalProspectiveSignal:
    """
    Complete immutable prospective signal record created at generation time (T0).
    """
    # 1. Identification
    signal_id: str
    campaign_id: str
    generated_at_utc: str
    generated_at_ist: str
    asset: str
    timeframe: str
    direction: str  # "BUY", "SELL", "WAIT"

    # 2. Provenance & Snapshots
    market_snapshot_hash: str
    policy_version: str
    model_version: str
    config_hash: str

    # 3. Exact Timing & Entry Parameters
    entry_window_start: str
    entry_window_end: str
    preferred_entry_time: str
    entry_price: float
    stop_loss: float
    take_profit: float
    expected_hold_seconds: int
    expected_exit_time: str
    max_exit_time: str

    # 4. Statistical Values & Quality
    probability: float  # Calibrated probability
    signal_strength: int  # 0 to 100
    quality_grade: str  # A+, A, B, C, WATCH, REJECTED
    expected_r: float  # Expected net R

    # 5. Market Context & Evidence
    regime: str
    mtf_alignment: float
    risk_state: str
    evidence_clusters: Dict[str, Any] = field(default_factory=dict)
    mtf_confirmation: Dict[str, str] = field(default_factory=dict)  # {"5m": "NO_SIGNAL", "15m": "SELL", ...}

    # 6. Qualification & Status Machine
    qualification_status: str = "QUALIFIED"  # "QUALIFIED", "WATCHLIST", "NO_TRADE", "REJECTED"
    signal_status: str = STATUS_UPCOMING
    no_trade_reason: Optional[str] = None
    supersedes_id: Optional[str] = None
    generation_version: int = 1

    # 7. Realized Outcomes (populated upon deterministic resolution)
    actual_entry_time: Optional[str] = None
    actual_entry_price: Optional[float] = None
    actual_exit_time: Optional[str] = None
    actual_exit_price: Optional[float] = None
    outcome: Optional[str] = None  # "WON", "LOST", "TIME_EXIT", "AMBIGUOUS"
    resolution_reason: Optional[str] = None  # "TP_HIT", "SL_HIT", "EXPIRY_EXIT", "AMBIGUOUS_CANDLE_CONSERVATIVE_SL"
    gross_r: Optional[float] = None
    friction_r: float = 0.05
    net_r: Optional[float] = None
    mfe: Optional[float] = None
    mae: Optional[float] = None

    # 8. Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class CanonicalProspectiveLedger:
    """
    Authoritative Single Source of Truth for prospective signals.
    Enforces persistent SQLite storage, strict immutability, deterministic resolution,
    unique composite deduplication, and unified time-window grouping.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path
        self._initialize_db()
        self._cleanse_duplicate_signals()

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
        """Creates the canonical_prospective_signal_ledger table and indexes."""
        conn = self._get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS canonical_prospective_signal_ledger (
                    signal_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    generated_at_utc TEXT NOT NULL,
                    generated_at_ist TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    
                    market_snapshot_hash TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    
                    entry_window_start TEXT NOT NULL,
                    entry_window_end TEXT NOT NULL,
                    preferred_entry_time TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    expected_hold_seconds INTEGER NOT NULL,
                    expected_exit_time TEXT NOT NULL,
                    max_exit_time TEXT NOT NULL,
                    
                    probability REAL NOT NULL,
                    signal_strength INTEGER NOT NULL,
                    quality_grade TEXT NOT NULL,
                    expected_r REAL NOT NULL,
                    
                    regime TEXT NOT NULL,
                    mtf_alignment REAL NOT NULL,
                    risk_state TEXT NOT NULL,
                    evidence_clusters TEXT,
                    mtf_confirmation TEXT,
                    
                    qualification_status TEXT NOT NULL,
                    signal_status TEXT NOT NULL,
                    no_trade_reason TEXT,
                    supersedes_id TEXT,
                    generation_version INTEGER DEFAULT 1,
                    
                    actual_entry_time TEXT,
                    actual_entry_price REAL,
                    actual_exit_time TEXT,
                    actual_exit_price REAL,
                    outcome TEXT,
                    resolution_reason TEXT,
                    gross_r REAL,
                    friction_r REAL,
                    net_r REAL,
                    mfe REAL,
                    mae REAL,
                    
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
                """
            )
            # Ensure supersedes_id and generation_version columns exist if table was created previously
            cur.execute("PRAGMA table_info(canonical_prospective_signal_ledger)")
            cols = [c[1] for c in cur.fetchall()]
            if "supersedes_id" not in cols:
                cur.execute("ALTER TABLE canonical_prospective_signal_ledger ADD COLUMN supersedes_id TEXT")
            if "generation_version" not in cols:
                cur.execute("ALTER TABLE canonical_prospective_signal_ledger ADD COLUMN generation_version INTEGER DEFAULT 1")

            cur.execute("CREATE INDEX IF NOT EXISTS idx_cpsl_asset ON canonical_prospective_signal_ledger(asset)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cpsl_timeframe ON canonical_prospective_signal_ledger(timeframe)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cpsl_status ON canonical_prospective_signal_ledger(signal_status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cpsl_outcome ON canonical_prospective_signal_ledger(outcome)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cpsl_gen_utc ON canonical_prospective_signal_ledger(generated_at_utc)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cpsl_qual ON canonical_prospective_signal_ledger(qualification_status)")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uidx_cpsl_identity ON canonical_prospective_signal_ledger(asset, timeframe, generated_at_utc, policy_version, generation_version)")
            conn.commit()
        except Exception as e:
            logger.debug(f"Error initializing canonical prospective ledger: {e}")
        finally:
            conn.close()

    def generate_signal_id(self, asset: str, timeframe: str, dt_utc: datetime, policy_version: str = "POL-70-v1", generation_version: int = 1, counter: Optional[int] = None) -> str:
        """
        Creates an immutable, canonical, deterministic signal_id.
        Format: SIG-YYYYMMDD-HHMMSS-ASSET-TF-POLVERSION-v1
        """
        version = counter if counter is not None else generation_version
        ts_str = dt_utc.strftime("%Y%m%d-%H%M%S")
        clean_pol = policy_version.replace("-", "").replace(".", "")
        return f"SIG-{ts_str}-{asset}-{timeframe}-{clean_pol}-v{version}"

    def compute_exact_timing(self, dt_utc: datetime, timeframe: str) -> Dict[str, Any]:
        """
        Calculates deterministic exact timing windows:
        - entry_window_start: dt_utc
        - entry_window_end: dt_utc + 10% of candle timeframe (or min 5 mins)
        - preferred_entry_time: dt_utc + 2% of candle timeframe (or 2 mins)
        - expected_hold_seconds: candle duration (e.g. 4H = 14400s)
        - expected_exit_time: preferred_entry_time + expected_hold_seconds
        - max_exit_time: expected_exit_time + 10% of timeframe buffer
        """
        hold_secs = TF_SECONDS.get(timeframe, 3600)
        window_duration = max(300, int(hold_secs * 0.10))
        pref_delay = max(120, int(hold_secs * 0.02))

        entry_start = dt_utc
        entry_end = dt_utc + timedelta(seconds=window_duration)
        preferred_entry = dt_utc + timedelta(seconds=pref_delay)
        expected_exit = preferred_entry + timedelta(seconds=hold_secs)
        max_exit = expected_exit + timedelta(seconds=window_duration)

        return {
            "entry_window_start": entry_start.isoformat(),
            "entry_window_end": entry_end.isoformat(),
            "preferred_entry_time": preferred_entry.isoformat(),
            "expected_hold_seconds": hold_secs,
            "expected_exit_time": expected_exit.isoformat(),
            "max_exit_time": max_exit.isoformat(),
        }

    def persist_signal(self, signal: CanonicalProspectiveSignal, allow_revision: bool = False, supersedes_id: Optional[str] = None) -> bool:
        """
        Persists a newly generated prospective signal.
        Enforces strict deduplication and immutability.
        If allow_revision is True and supersedes_id is provided, archives previous signal as SUPERSEDED.
        """
        conn = self._get_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            
            # Check if exact signal_id already exists
            cur.execute("SELECT signal_id FROM canonical_prospective_signal_ledger WHERE signal_id = ?", (signal.signal_id,))
            if cur.fetchone():
                return True

            # Check if matching (asset, timeframe, generated_at_utc, policy_version, generation_version) already exists
            cur.execute(
                """
                SELECT signal_id FROM canonical_prospective_signal_ledger 
                WHERE asset = ? AND timeframe = ? AND generated_at_utc = ? AND policy_version = ? AND generation_version = ?
                """,
                (signal.asset, signal.timeframe, signal.generated_at_utc, signal.policy_version, signal.generation_version)
            )
            existing = cur.fetchone()
            if existing:
                if not allow_revision:
                    logger.debug(f"Signal already exists with id {existing[0]} - deduplication enforced.")
                    return True

            # Handle superseding of previous revision
            if supersedes_id:
                cur.execute(
                    "UPDATE canonical_prospective_signal_ledger SET signal_status = ? WHERE signal_id = ?",
                    (STATUS_SUPERSEDED, supersedes_id)
                )

            cur.execute(
                """
                INSERT INTO canonical_prospective_signal_ledger (
                    signal_id, campaign_id, generated_at_utc, generated_at_ist, asset, timeframe, direction,
                    market_snapshot_hash, policy_version, model_version, config_hash,
                    entry_window_start, entry_window_end, preferred_entry_time, entry_price, stop_loss, take_profit,
                    expected_hold_seconds, expected_exit_time, max_exit_time,
                    probability, signal_strength, quality_grade, expected_r,
                    regime, mtf_alignment, risk_state, evidence_clusters, mtf_confirmation,
                    qualification_status, signal_status, no_trade_reason, supersedes_id, generation_version,
                    actual_entry_time, actual_entry_price, actual_exit_time, actual_exit_price,
                    outcome, resolution_reason, gross_r, friction_r, net_r, mfe, mae,
                    created_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.signal_id, signal.campaign_id, signal.generated_at_utc, signal.generated_at_ist,
                    signal.asset, signal.timeframe, signal.direction,
                    signal.market_snapshot_hash, signal.policy_version, signal.model_version, signal.config_hash,
                    signal.entry_window_start, signal.entry_window_end, signal.preferred_entry_time,
                    signal.entry_price, signal.stop_loss, signal.take_profit,
                    signal.expected_hold_seconds, signal.expected_exit_time, signal.max_exit_time,
                    signal.probability, signal.signal_strength, signal.quality_grade, signal.expected_r,
                    signal.regime, signal.mtf_alignment, signal.risk_state,
                    json.dumps(signal.evidence_clusters), json.dumps(signal.mtf_confirmation),
                    signal.qualification_status, signal.signal_status, signal.no_trade_reason,
                    supersedes_id or signal.supersedes_id, signal.generation_version,
                    signal.actual_entry_time, signal.actual_entry_price, signal.actual_exit_time, signal.actual_exit_price,
                    signal.outcome, signal.resolution_reason, signal.gross_r, signal.friction_r, signal.net_r,
                    signal.mfe, signal.mae, signal.created_at, signal.resolved_at
                )
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error persisting canonical signal {signal.signal_id}: {e}")
            return False
        finally:
            conn.close()

    def resolve_signal_outcome(
        self,
        signal_id: str,
        outcome: str,
        resolution_reason: str,
        actual_exit_price: float,
        actual_exit_time: str,
        gross_r: float,
        net_r: float,
        mfe: float = 0.0,
        mae: float = 0.0,
        actual_entry_price: Optional[float] = None,
        actual_entry_time: Optional[str] = None,
    ) -> bool:
        """
        Deterministically resolves a prospective signal without modifying any of its original prediction fields.
        """
        conn = self._get_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            resolved_at = datetime.now(timezone.utc).isoformat()
            
            cur.execute(
                """
                UPDATE canonical_prospective_signal_ledger
                SET outcome = ?,
                    resolution_reason = ?,
                    actual_exit_price = ?,
                    actual_exit_time = ?,
                    gross_r = ?,
                    net_r = ?,
                    mfe = ?,
                    mae = ?,
                    actual_entry_price = COALESCE(?, actual_entry_price, entry_price),
                    actual_entry_time = COALESCE(?, actual_entry_time, preferred_entry_time),
                    signal_status = ?,
                    resolved_at = ?
                WHERE signal_id = ?
                """,
                (
                    outcome,
                    resolution_reason,
                    actual_exit_price,
                    actual_exit_time,
                    gross_r,
                    net_r,
                    mfe,
                    mae,
                    actual_entry_price,
                    actual_entry_time,
                    STATUS_RESOLVED,
                    resolved_at,
                    signal_id,
                )
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error resolving signal {signal_id}: {e}")
            return False
        finally:
            conn.close()

    # Alias for convenient API usage
    resolve_signal = resolve_signal_outcome

    def resolve_against_candle(
        self,
        signal: CanonicalProspectiveSignal,
        candle_open: float,
        candle_high: float,
        candle_low: float,
        candle_close: float,
        candle_time: str,
    ) -> Tuple[Optional[str], Optional[str], Optional[float], Optional[float]]:
        """
        Conservative deterministic resolution against a market candle.
        Conservative rule: If both TP and SL are touched in the same candle bar,
        assume SL is hit first (conservative downside protection).
        Returns: (outcome, resolution_reason, exit_price, net_r)
        """
        is_buy = signal.direction.upper() in ["BUY", "LONG"]
        entry = signal.entry_price
        sl = signal.stop_loss
        tp = signal.take_profit
        friction = signal.friction_r

        if is_buy:
            risk_dist = abs(entry - sl) if abs(entry - sl) > 0 else 0.0010
            hit_tp = candle_high >= tp
            hit_sl = candle_low <= sl

            if hit_tp and hit_sl:
                gross_r = -1.0
                net_r = round(gross_r - friction, 2)
                return OUTCOME_LOST, "AMBIGUOUS_CANDLE_CONSERVATIVE_SL", sl, net_r
            elif hit_tp:
                gross_r = round(abs(tp - entry) / risk_dist, 2)
                net_r = round(gross_r - friction, 2)
                return OUTCOME_WON, "TP_HIT", tp, net_r
            elif hit_sl:
                gross_r = -1.0
                net_r = round(gross_r - friction, 2)
                return OUTCOME_LOST, "SL_HIT", sl, net_r
        else:
            risk_dist = abs(sl - entry) if abs(sl - entry) > 0 else 0.0010
            hit_tp = candle_low <= tp
            hit_sl = candle_high >= sl

            if hit_tp and hit_sl:
                gross_r = -1.0
                net_r = round(gross_r - friction, 2)
                return OUTCOME_LOST, "AMBIGUOUS_CANDLE_CONSERVATIVE_SL", sl, net_r
            elif hit_tp:
                gross_r = round(abs(entry - tp) / risk_dist, 2)
                net_r = round(gross_r - friction, 2)
                return OUTCOME_WON, "TP_HIT", tp, net_r
            elif hit_sl:
                gross_r = -1.0
                net_r = round(gross_r - friction, 2)
                return OUTCOME_LOST, "SL_HIT", sl, net_r

        return None, None, None, None

    def resolve_pending_expired_signals(self, reference_dt: Optional[datetime] = None) -> int:
        """
        Automatic Outcome Resolution Engine.
        Scans for unresolved prospective signals whose max_exit_time has passed.
        Fetches the exact historical candles from historical_candles across the trade window.
        Deterministically evaluates TP, SL, conservative same-candle ambiguity, or time exit.
        Immutably stores outcome, exit price, exit timestamp, and realized R.
        """
        now = reference_dt or datetime.now(timezone.utc)
        now_str = now.isoformat()

        conn = self._get_connection()
        if not conn:
            return 0

        resolved_count = 0
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT signal_id, asset, timeframe, direction, entry_price, stop_loss, take_profit,
                       entry_window_start, preferred_entry_time, max_exit_time, friction_r
                FROM canonical_prospective_signal_ledger
                WHERE (outcome IS NULL OR signal_status != 'RESOLVED')
                  AND max_exit_time <= ?
                """,
                (now_str,)
            )
            pending = cur.fetchall()

            for row in pending:
                (sig_id, asset, tf, direction, entry_price, sl, tp,
                 entry_start, pref_entry, max_exit, friction) = row

                t_start = (entry_start or pref_entry or "").replace("T", " ")[:19]
                t_end = (max_exit or "").replace("T", " ")[:19]

                cur.execute(
                    """
                    SELECT open, high, low, close, timestamp
                    FROM historical_candles
                    WHERE symbol = ?
                      AND timestamp >= ?
                      AND timestamp <= ?
                    ORDER BY timestamp ASC
                    """,
                    (asset, t_start, t_end)
                )
                candles = cur.fetchall()
                if not candles:
                    cur.execute(
                        """
                        SELECT open, high, low, close, timestamp
                        FROM historical_candles
                        WHERE symbol = ?
                          AND timestamp >= ?
                          AND timestamp <= ?
                        ORDER BY timestamp ASC
                        """,
                        (asset, entry_start, max_exit)
                    )
                    candles = cur.fetchall()

                if not candles:
                    continue

                outcome = None
                exit_price = None
                exit_time = None
                res_reason = None
                net_r = None
                gross_r = None

                is_buy = direction.upper() in ["BUY", "LONG"]
                risk_dist = abs(entry_price - sl) if abs(entry_price - sl) > 0 else (entry_price * 0.01)

                for c_open, c_high, c_low, c_close, c_time in candles:
                    c_open, c_high, c_low, c_close = float(c_open), float(c_high), float(c_low), float(c_close)
                    if is_buy:
                        tp_hit = c_high >= tp
                        sl_hit = c_low <= sl
                        if tp_hit and sl_hit:
                            outcome = OUTCOME_LOST
                            res_reason = "AMBIGUOUS_CANDLE_CONSERVATIVE_SL"
                            exit_price = sl
                            exit_time = str(c_time)
                            gross_r = -1.0
                            net_r = round(gross_r - friction, 2)
                            break
                        elif tp_hit:
                            outcome = OUTCOME_WON
                            res_reason = "TP_HIT"
                            exit_price = tp
                            exit_time = str(c_time)
                            gross_r = round(abs(tp - entry_price) / risk_dist, 2)
                            net_r = round(gross_r - friction, 2)
                            break
                        elif sl_hit:
                            outcome = OUTCOME_LOST
                            res_reason = "SL_HIT"
                            exit_price = sl
                            exit_time = str(c_time)
                            gross_r = -1.0
                            net_r = round(gross_r - friction, 2)
                            break
                    else:
                        tp_hit = c_low <= tp
                        sl_hit = c_high >= sl
                        if tp_hit and sl_hit:
                            outcome = OUTCOME_LOST
                            res_reason = "AMBIGUOUS_CANDLE_CONSERVATIVE_SL"
                            exit_price = sl
                            exit_time = str(c_time)
                            gross_r = -1.0
                            net_r = round(gross_r - friction, 2)
                            break
                        elif tp_hit:
                            outcome = OUTCOME_WON
                            res_reason = "TP_HIT"
                            exit_price = tp
                            exit_time = str(c_time)
                            gross_r = round(abs(entry_price - tp) / risk_dist, 2)
                            net_r = round(gross_r - friction, 2)
                            break
                        elif sl_hit:
                            outcome = OUTCOME_LOST
                            res_reason = "SL_HIT"
                            exit_price = sl
                            exit_time = str(c_time)
                            gross_r = -1.0
                            net_r = round(gross_r - friction, 2)
                            break

                if outcome is None:
                    last_c_close = float(candles[-1][3])
                    last_c_time = str(candles[-1][4])
                    outcome = OUTCOME_TIME_EXIT
                    res_reason = "EXPIRY_EXIT"
                    exit_price = last_c_close
                    exit_time = last_c_time
                    gross_pnl = (last_c_close - entry_price) if is_buy else (entry_price - last_c_close)
                    gross_r = round(gross_pnl / risk_dist, 2)
                    net_r = round(gross_r - friction, 2)

                resolved_at = datetime.now(timezone.utc).isoformat()
                cur.execute(
                    """
                    UPDATE canonical_prospective_signal_ledger
                    SET outcome = ?,
                        resolution_reason = ?,
                        actual_exit_price = ?,
                        actual_exit_time = ?,
                        gross_r = ?,
                        net_r = ?,
                        signal_status = ?,
                        resolved_at = ?
                    WHERE signal_id = ?
                    """,
                    (outcome, res_reason, exit_price, exit_time, gross_r, net_r, STATUS_RESOLVED, resolved_at, sig_id)
                )
                resolved_count += 1

            conn.commit()
            return resolved_count
        except Exception as e:
            logger.error(f"Error in resolve_pending_expired_signals: {e}")
            return resolved_count
        finally:
            conn.close()


    def get_signal(self, signal_id: str) -> Optional[CanonicalProspectiveSignal]:
        """Fetches a canonical signal record by signal_id."""
        conn = self._get_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM canonical_prospective_signal_ledger WHERE signal_id = ?", (signal_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_signal(row, cur.description)
        finally:
            conn.close()

    def get_signals_by_filter(
        self,
        date_filter: str = "TODAY",  # "TODAY", "YESTERDAY", "7D", "30D", "ALL"
        asset: Optional[str] = None,
        timeframe: Optional[str] = None,
        direction: Optional[str] = None,
        quality: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        reference_dt: Optional[datetime] = None,
    ) -> List[CanonicalProspectiveSignal]:
        """
        Authoritative retrieval of canonical prospective signals with precise date boundary filtering.
        Excludes superseded revisions by default unless specifically requested.
        """
        now = reference_dt or datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        seven_d_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        thirty_d_str = (now - timedelta(days=30)).strftime("%Y-%m-%d")

        conn = self._get_connection()
        if not conn:
            return []

        try:
            cur = conn.cursor()
            query = "SELECT * FROM canonical_prospective_signal_ledger WHERE signal_status != 'SUPERSEDED'"
            params: List[Any] = []

            # Date Filter
            if date_filter.upper() == "TODAY":
                query += " AND (generated_at_utc LIKE ? OR generated_at_ist LIKE ?)"
                params.extend([f"{today_str}%", f"{today_str}%"])
            elif date_filter.upper() == "YESTERDAY":
                cur.execute("SELECT COUNT(*) FROM canonical_prospective_signal_ledger WHERE (generated_at_utc LIKE ? OR generated_at_ist LIKE ?)", (f"{yesterday_str}%", f"{yesterday_str}%"))
                cnt = cur.fetchone()[0]
                if cnt == 0:
                    cur.execute("SELECT SUBSTR(generated_at_utc, 1, 10) FROM canonical_prospective_signal_ledger WHERE SUBSTR(generated_at_utc, 1, 10) < ? ORDER BY generated_at_utc DESC LIMIT 1", (today_str,))
                    row = cur.fetchone()
                    if row and row[0]:
                        yesterday_str = row[0]
                    else:
                        cur.execute("SELECT SUBSTR(generated_at_utc, 1, 10) FROM canonical_prospective_signal_ledger ORDER BY generated_at_utc DESC LIMIT 1")
                        row = cur.fetchone()
                        if row and row[0]:
                            yesterday_str = row[0]
                query += " AND (generated_at_utc LIKE ? OR generated_at_ist LIKE ?)"
                params.extend([f"{yesterday_str}%", f"{yesterday_str}%"])
            elif date_filter.upper() == "7D":
                query += " AND generated_at_utc >= ?"
                params.append(f"{seven_d_str}T00:00:00")
            elif date_filter.upper() == "30D":
                query += " AND generated_at_utc >= ?"
                params.append(f"{thirty_d_str}T00:00:00")

            # Parametric Filters
            if asset and asset.upper() != "ALL":
                query += " AND asset = ?"
                params.append(asset.upper())
            if timeframe and timeframe.upper() != "ALL":
                query += " AND timeframe = ?"
                params.append(timeframe)
            if direction and direction.upper() != "ALL":
                query += " AND direction = ?"
                params.append(direction.upper())
            if quality and quality.upper() != "ALL":
                query += " AND quality_grade = ?"
                params.append(quality.upper())
            if status and status.upper() != "ALL":
                if status.upper() in ["WON", "LOST", "TIME_EXIT", "AMBIGUOUS"]:
                    query += " AND outcome = ?"
                    params.append(status.upper())
                else:
                    query += " AND (signal_status = ? OR qualification_status = ?)"
                    params.extend([status.upper(), status.upper()])

            query += " ORDER BY generated_at_utc DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cur.execute(query, params)
            rows = cur.fetchall()
            return [self._row_to_signal(r, cur.description) for r in rows]
        finally:
            conn.close()

    def get_today_time_windows(self, reference_dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Groups today's active/qualified signals into actionable time windows (e.g. '18:00 SIGNAL WINDOW').
        """
        today_signals = self.get_signals_by_filter(date_filter="TODAY", limit=200, reference_dt=reference_dt)
        
        # Group by HH:MM window
        windows_map: Dict[str, List[CanonicalProspectiveSignal]] = {}
        for sig in today_signals:
            t_str = sig.generated_at_utc[11:16] if len(sig.generated_at_utc) >= 16 else "00:00"
            if t_str not in windows_map:
                windows_map[t_str] = []
            windows_map[t_str].append(sig)

        result: List[Dict[str, Any]] = []
        for t_window, sigs in sorted(windows_map.items(), reverse=True):
            qualified = [s.to_dict() for s in sigs if s.qualification_status == "QUALIFIED"]
            no_trade = [s.to_dict() for s in sigs if s.qualification_status != "QUALIFIED"]

            result.append({
                "time_window": t_window,
                "window_title": f"{t_window} SIGNAL WINDOW",
                "total_signals": len(sigs),
                "qualified_count": len(qualified),
                "no_trade_count": len(no_trade),
                "signals": qualified,
                "no_trade_signals": no_trade,
            })

        return result

    def _row_to_signal(self, row: tuple, description: tuple) -> CanonicalProspectiveSignal:
        """Converts a database row into a CanonicalProspectiveSignal instance."""
        col_names = [d[0] for d in description]
        d = dict(zip(col_names, row))

        evidence = json.loads(d.get("evidence_clusters") or "{}") if isinstance(d.get("evidence_clusters"), str) else (d.get("evidence_clusters") or {})
        mtf_conf = json.loads(d.get("mtf_confirmation") or "{}") if isinstance(d.get("mtf_confirmation"), str) else (d.get("mtf_confirmation") or {})

        return CanonicalProspectiveSignal(
            signal_id=d["signal_id"],
            campaign_id=d["campaign_id"],
            generated_at_utc=d["generated_at_utc"],
            generated_at_ist=d["generated_at_ist"],
            asset=d["asset"],
            timeframe=d["timeframe"],
            direction=d["direction"],
            market_snapshot_hash=d["market_snapshot_hash"],
            policy_version=d["policy_version"],
            model_version=d["model_version"],
            config_hash=d["config_hash"],
            entry_window_start=d["entry_window_start"],
            entry_window_end=d["entry_window_end"],
            preferred_entry_time=d["preferred_entry_time"],
            entry_price=float(d["entry_price"]),
            stop_loss=float(d["stop_loss"]),
            take_profit=float(d["take_profit"]),
            expected_hold_seconds=int(d["expected_hold_seconds"]),
            expected_exit_time=d["expected_exit_time"],
            max_exit_time=d["max_exit_time"],
            probability=float(d["probability"]),
            signal_strength=int(d["signal_strength"]),
            quality_grade=d["quality_grade"],
            expected_r=float(d["expected_r"]),
            regime=d["regime"],
            mtf_alignment=float(d["mtf_alignment"]),
            risk_state=d["risk_state"],
            evidence_clusters=evidence,
            mtf_confirmation=mtf_conf,
            qualification_status=d["qualification_status"],
            signal_status=d["signal_status"],
            no_trade_reason=d.get("no_trade_reason"),
            supersedes_id=d.get("supersedes_id"),
            generation_version=int(d.get("generation_version") or 1),
            actual_entry_time=d.get("actual_entry_time"),
            actual_entry_price=float(d["actual_entry_price"]) if d.get("actual_entry_price") is not None else None,
            actual_exit_time=d.get("actual_exit_time"),
            actual_exit_price=float(d["actual_exit_price"]) if d.get("actual_exit_price") is not None else None,
            outcome=d.get("outcome"),
            resolution_reason=d.get("resolution_reason"),
            gross_r=float(d["gross_r"]) if d.get("gross_r") is not None else None,
            friction_r=float(d["friction_r"]) if d.get("friction_r") is not None else 0.05,
            net_r=float(d["net_r"]) if d.get("net_r") is not None else None,
            mfe=float(d["mfe"]) if d.get("mfe") is not None else None,
            mae=float(d["mae"]) if d.get("mae") is not None else None,
            created_at=d["created_at"],
            resolved_at=d.get("resolved_at"),
        )

    def _cleanse_duplicate_signals(self):
        """
        Cleanses duplicate and test signals from the canonical ledger,
        preserving only canonical entries with valid unique identities.
        """
        conn = self._get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # 1. Delete test artifacts with explicit TEST prefixes
            cur.execute(
                """
                DELETE FROM canonical_prospective_signal_ledger 
                WHERE signal_id LIKE 'SIG-TEST-%' 
                   OR signal_id LIKE 'SIG-E2E-TEST-%' 
                   OR signal_id LIKE 'SIG-TIMEOUT-%'
                """
            )
            # 2. Retain only one canonical record per (asset, timeframe, generated_at_utc, policy_version)
            cur.execute(
                """
                DELETE FROM canonical_prospective_signal_ledger
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM canonical_prospective_signal_ledger
                    GROUP BY asset, timeframe, generated_at_utc, policy_version
                )
                """
            )
            conn.commit()
            logger.info("Ledger deduplication cleanse completed successfully.")
        except Exception as e:
            logger.debug(f"Ledger cleanse note: {e}")
        finally:
            conn.close()


# Global Singleton Instance
canonical_prospective_ledger = CanonicalProspectiveLedger()
