"""
app/core/signal_state.py  — Phase 33
======================================
SignalStateMachine: explicit state transitions for signal lifecycle.
Every state change must be declared and validated here.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from app.logs.logger import get_logger

logger = get_logger(__name__)


class SignalState(str, Enum):
    """All valid signal states. String-compatible for DB storage."""
    DETECTED   = "DETECTED"
    ANALYZING  = "ANALYZING"
    APPROVED   = "APPROVED"
    REJECTED   = "REJECTED"
    WAITING    = "WAITING"
    ACTIVE     = "ACTIVE"
    EXPIRED    = "EXPIRED"
    TP_HIT     = "TP_HIT"
    SL_HIT     = "SL_HIT"
    TIME_EXIT  = "TIME_EXIT"
    AMBIGUOUS  = "AMBIGUOUS"
    COMPLETED  = "COMPLETED"


# Valid transitions: {from_state: {event: to_state}}
TRANSITIONS: dict[SignalState, dict[str, SignalState]] = {
    SignalState.DETECTED: {
        "start_analysis":   SignalState.ANALYZING,
        "reject":           SignalState.REJECTED,
    },
    SignalState.ANALYZING: {
        "approve":          SignalState.APPROVED,
        "reject":           SignalState.REJECTED,
        "wait":             SignalState.WAITING,
    },
    SignalState.APPROVED: {
        "activate":         SignalState.ACTIVE,
        "expire":           SignalState.EXPIRED,
    },
    SignalState.WAITING: {
        "activate":         SignalState.ACTIVE,
        "expire":           SignalState.EXPIRED,
        "reject":           SignalState.REJECTED,
    },
    SignalState.ACTIVE: {
        "tp_hit":           SignalState.TP_HIT,
        "sl_hit":           SignalState.SL_HIT,
        "time_exit":        SignalState.TIME_EXIT,
        "expire":           SignalState.EXPIRED,
        "ambiguous":        SignalState.AMBIGUOUS,
    },
    SignalState.TP_HIT: {
        "complete":         SignalState.COMPLETED,
    },
    SignalState.SL_HIT: {
        "complete":         SignalState.COMPLETED,
    },
    SignalState.TIME_EXIT: {
        "complete":         SignalState.COMPLETED,
    },
    SignalState.AMBIGUOUS: {
        "complete":         SignalState.COMPLETED,
    },
    SignalState.EXPIRED: {
        "complete":         SignalState.COMPLETED,
    },
    # Terminal states — no further transitions
    SignalState.REJECTED:  {},
    SignalState.COMPLETED: {},
}


class InvalidTransitionError(Exception):
    pass


class SignalStateMachine:
    """
    Validates and performs signal state transitions.

    Usage:
        new_state = SignalStateMachine.transition(
            current_state=SignalState.ANALYZING,
            event="approve"
        )
    """

    @staticmethod
    def transition(
        current_state: SignalState | str,
        event: str,
        strict: bool = True,
    ) -> Optional[SignalState]:
        """
        Perform a state transition.

        Parameters
        ----------
        current_state : SignalState or str
        event : str
            The event triggering the transition (e.g. "approve", "tp_hit").
        strict : bool
            If True, raise InvalidTransitionError on invalid event.
            If False, log a warning and return None.

        Returns
        -------
        SignalState or None
        """
        if isinstance(current_state, str):
            try:
                current_state = SignalState(current_state)
            except ValueError:
                msg = f"Unknown current state: '{current_state}'"
                if strict:
                    raise InvalidTransitionError(msg)
                logger.warning(msg)
                return None

        allowed = TRANSITIONS.get(current_state, {})
        next_state = allowed.get(event.lower())

        if next_state is None:
            msg = (
                f"INVALID_TRANSITION: '{current_state}' → event='{event}' "
                f"(allowed events: {list(allowed.keys())})"
            )
            if strict:
                raise InvalidTransitionError(msg)
            logger.warning(msg)
            return None

        logger.debug(f"Signal state: {current_state} → {next_state} (event: '{event}')")
        return next_state

    @staticmethod
    def is_terminal(state: SignalState | str) -> bool:
        """Returns True if the state has no further transitions."""
        if isinstance(state, str):
            try:
                state = SignalState(state)
            except ValueError:
                return False
        return len(TRANSITIONS.get(state, {})) == 0

    @staticmethod
    def is_resolved(state: SignalState | str) -> bool:
        """True if the outcome of the signal is known (positive or negative)."""
        resolved = {
            SignalState.TP_HIT, SignalState.SL_HIT, SignalState.TIME_EXIT,
            SignalState.AMBIGUOUS, SignalState.COMPLETED
        }
        if isinstance(state, str):
            try:
                state = SignalState(state)
            except ValueError:
                return False
        return state in resolved
