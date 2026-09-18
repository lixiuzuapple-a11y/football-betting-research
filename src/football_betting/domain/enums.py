"""Enumerations used across the research system.

These are deliberately small. Anything that represents a research choice
(model family, stake sizing, ...) belongs in a document or a record, not in an
enum that would need to be edited on every experiment.
"""

from __future__ import annotations

from enum import Enum


class MatchPhase(str, Enum):
    """When a piece of information exists relative to kickoff.

    The three phases must never be conflated. ``POST_MATCH`` information is
    forbidden inside a pre-match artefact.
    """

    PRE_MATCH = "pre_match"
    LIVE = "live"
    POST_MATCH = "post_match"


class MatchStatus(str, Enum):
    """Lifecycle of a fixture, independent of any wagering market."""

    SCHEDULED = "scheduled"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    PLAYED = "played"
    ABANDONED = "abandoned"


class Market(str, Enum):
    """Wagering markets. Only the ones a model can currently forecast appear here."""

    #: Full-time home / draw / away.
    ONE_X_TWO = "1x2"
    #: Full-time home / draw / away after applying an official handicap.
    HANDICAP_ONE_X_TWO = "handicap_1x2"
    #: Total goals, over / under a line.
    TOTAL_GOALS = "total_goals"


class Selection(str, Enum):
    """A pick inside a market."""

    HOME = "home"
    DRAW = "draw"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"


#: Selections that carry a probability straight out of a 1X2 forecast.
ONE_X_TWO_SELECTIONS: frozenset[Selection] = frozenset(
    {Selection.HOME, Selection.DRAW, Selection.AWAY}
)

#: Markets that a plain 1X2 forecast may price directly.
#:
#: ``HANDICAP_ONE_X_TWO`` is deliberately **absent**. Applying a handicap
#: shifts the outcome distribution, so a handicap market priced straight off an
#: unhandicapped 1X2 forecast would be a modelling error dressed up as data.
#: It needs its own model before it can appear here.
ONE_X_TWO_MARKETS: frozenset[Market] = frozenset({Market.ONE_X_TWO})


class Decision(str, Enum):
    """Output of the decision layer.

    ``BUY`` means "this is a recordable recommendation at these odds".
    It is never an instruction to place a bet. See
    ``docs/project-charter.md`` section 6.3.
    """

    BUY = "BUY"
    PASS = "PASS"


class ExperimentStatus(str, Enum):
    """Lifecycle of a research experiment.

    ``FAILED`` is a first-class, permanent state: failed experiments are kept.
    """

    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


class BetRecordStatus(str, Enum):
    """Lifecycle of a *manually placed* bet, recorded after the fact."""

    RECORDED = "RECORDED"
    SETTLED = "SETTLED"
    VOID = "VOID"
