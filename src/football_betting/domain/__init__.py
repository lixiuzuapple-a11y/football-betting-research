"""Shared, dependency-free data contracts.

``domain`` sits beneath every other layer: it defines *what a fact is*, while
the layer modules define *what may be done with a fact*. Layers import from
``domain``; ``domain`` imports from nothing inside this package. That rule is
what stops the eight functional layers from reaching into each other and
turning into one module with eight names.
"""

from __future__ import annotations

from .enums import (
    ONE_X_TWO_MARKETS,
    ONE_X_TWO_SELECTIONS,
    BetRecordStatus,
    Decision,
    ExperimentStatus,
    Market,
    MatchPhase,
    MatchStatus,
    Selection,
)
from .errors import (
    DuplicateRecordError,
    FootballBettingError,
    FutureInformationError,
    NotAnInputError,
    NotImplementedYetError,
    ProvenanceError,
    UnknownReferenceError,
    ValidationError,
)
from .models import (
    IMPLIED_PROBABILITY_TOLERANCE,
    MATCH_DURATION,
    BetRecord,
    Experiment,
    Match,
    MatchResult,
    OddsSnapshot,
    Prediction,
    Recommendation,
    Team,
)
from .validation import (
    PROBABILITY_TOLERANCE,
    require_aware,
    require_non_empty_text,
    require_positive,
    require_probability,
    require_probability_vector,
    to_utc,
)

__all__ = [
    "IMPLIED_PROBABILITY_TOLERANCE",
    "MATCH_DURATION",
    "ONE_X_TWO_MARKETS",
    "ONE_X_TWO_SELECTIONS",
    "PROBABILITY_TOLERANCE",
    "BetRecord",
    "BetRecordStatus",
    "Decision",
    "DuplicateRecordError",
    "Experiment",
    "ExperimentStatus",
    "FootballBettingError",
    "FutureInformationError",
    "Market",
    "Match",
    "MatchPhase",
    "MatchResult",
    "MatchStatus",
    "NotAnInputError",
    "NotImplementedYetError",
    "OddsSnapshot",
    "Prediction",
    "ProvenanceError",
    "Recommendation",
    "Selection",
    "Team",
    "UnknownReferenceError",
    "ValidationError",
    "require_aware",
    "require_non_empty_text",
    "require_positive",
    "require_probability",
    "require_probability_vector",
    "to_utc",
]
