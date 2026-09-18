"""Core data contracts.

These objects are the auditable spine of the system. Two design rules apply
throughout and are enforced in ``__post_init__`` rather than documented only:

1. **Nothing is naive.** Every timestamp carries a timezone.
2. **Time order is explicit.** An object that was created at time *t* may only
   depend on data available at or before *t* (``as_of <= created_at``), and an
   observation may never be collected before the moment it describes
   (``data_time <= collected_at``).

The objects are frozen: a recorded prediction or recommendation is a fact, and
corrections are made by appending a new record, never by editing an old one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Any

from .enums import (
    ONE_X_TWO_SELECTIONS,
    BetRecordStatus,
    Decision,
    ExperimentStatus,
    Market,
    MatchPhase,
    MatchStatus,
    Selection,
)
from .errors import NotImplementedYetError, ValidationError
from .validation import (
    require_aware,
    require_enum,
    require_non_empty_text,
    require_positive,
    require_probability,
    require_probability_vector,
)

#: Conservative upper bound used to decide when a fixture stops being "live".
#: Regulation is 90 minutes plus stoppage, half-time and a safety margin.
MATCH_DURATION = timedelta(hours=3)

#: Tolerance for the ``implied_probability == 1 / odds`` consistency check.
IMPLIED_PROBABILITY_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class Team:
    """A club or national team."""

    team_id: str
    name: str
    league: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.team_id, "team_id")
        require_non_empty_text(self.name, "name")


@dataclass(frozen=True, slots=True)
class Match:
    """A fixture. Existence and schedule only - never a scoreline."""

    match_id: str
    league: str
    season: str
    kickoff_at: datetime
    home_team_id: str
    away_team_id: str
    status: MatchStatus = MatchStatus.SCHEDULED
    venue: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.match_id, "match_id")
        require_non_empty_text(self.league, "league")
        require_non_empty_text(self.season, "season")
        require_non_empty_text(self.home_team_id, "home_team_id")
        require_non_empty_text(self.away_team_id, "away_team_id")
        require_aware(self.kickoff_at, "kickoff_at")
        require_enum(self.status, MatchStatus, "status")
        if self.home_team_id == self.away_team_id:
            raise ValidationError("home_team_id and away_team_id must differ")

    def phase_at(self, when: datetime) -> MatchPhase:
        """Which phase the fixture is in at ``when``.

        This is the primitive every look-ahead guard is built on. It answers
        "was this fixture already under way?" without needing a scoreline.
        """
        require_aware(when, "when")
        if when < self.kickoff_at:
            return MatchPhase.PRE_MATCH
        if when < self.kickoff_at + MATCH_DURATION:
            return MatchPhase.LIVE
        return MatchPhase.POST_MATCH


@dataclass(frozen=True, slots=True)
class OddsSnapshot:
    """One quoted price for one selection, captured at one moment.

    ``data_time`` is when the price was *true*; ``collected_at`` is when we
    received it. Both are required, because a feed can deliver a stale or
    delayed quote and only the pair together is auditable.
    """

    snapshot_id: str
    match_id: str
    market: Market
    selection: Selection
    decimal_odds: float
    data_time: datetime
    collected_at: datetime
    source: str
    bookmaker: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.snapshot_id, "snapshot_id")
        require_non_empty_text(self.match_id, "match_id")
        require_non_empty_text(self.source, "source")
        require_enum(self.market, Market, "market")
        require_enum(self.selection, Selection, "selection")
        require_positive(self.decimal_odds, "decimal_odds")
        if self.decimal_odds <= 1.0:
            raise ValidationError(
                f"decimal_odds must be > 1.0 for a decimal-odds quote, got {self.decimal_odds!r}"
            )
        require_aware(self.data_time, "data_time")
        require_aware(self.collected_at, "collected_at")
        if self.data_time > self.collected_at:
            raise ValidationError(
                f"data_time ({self.data_time.isoformat()}) must not be later than "
                f"collected_at ({self.collected_at.isoformat()})"
            )


@dataclass(frozen=True, slots=True)
class Prediction:
    """A 1X2 forecast produced by a specific model version.

    ``as_of`` is the information cutoff: the model saw nothing later than this
    instant. It is what makes the question "what did this prediction actually
    know?" answerable months later.
    """

    prediction_id: str
    match_id: str
    created_at: datetime
    model_version: str
    data_version: str
    as_of: datetime
    probability_home: float
    probability_draw: float
    probability_away: float
    notes: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.prediction_id, "prediction_id")
        require_non_empty_text(self.match_id, "match_id")
        require_non_empty_text(self.model_version, "model_version")
        require_non_empty_text(self.data_version, "data_version")
        require_aware(self.created_at, "created_at")
        require_aware(self.as_of, "as_of")
        if self.as_of > self.created_at:
            raise ValidationError(
                f"as_of ({self.as_of.isoformat()}) must not be later than "
                f"created_at ({self.created_at.isoformat()})"
            )
        require_probability_vector(
            (self.probability_home, self.probability_draw, self.probability_away),
            ("probability_home", "probability_draw", "probability_away"),
        )

    def probabilities(self) -> tuple[float, float, float]:
        """Return ``(home, draw, away)``."""
        return (self.probability_home, self.probability_draw, self.probability_away)

    def probability_for(self, selection: Selection) -> float:
        """Map a 1X2 selection onto its forecast probability.

        Raises :class:`NotImplementedYetError` for markets this model does not
        forecast, rather than inventing a number.
        """
        if selection not in ONE_X_TWO_SELECTIONS:
            raise NotImplementedYetError(
                f"the 1X2 forecast cannot price selection {selection.value!r}; "
                "no model output exists for that market yet"
            )
        return {
            Selection.HOME: self.probability_home,
            Selection.DRAW: self.probability_draw,
            Selection.AWAY: self.probability_away,
        }[selection]


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A research output: a priced opinion at a specific moment.

    ``decision == BUY`` means "record this as a candidate". It is *not* an
    instruction, and nothing in this system acts on it.

    ``implied_probability`` is the raw, margin-inclusive ``1 / odds``.
    ``market_probability``, when present, is the de-vigged market estimate.
    """

    recommendation_id: str
    match_id: str
    prediction_id: str
    created_at: datetime
    as_of: datetime
    market: Market
    selection: Selection
    odds: float
    implied_probability: float
    model_probability: float
    decision: Decision
    reason: str
    market_probability: float | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.recommendation_id, "recommendation_id")
        require_non_empty_text(self.match_id, "match_id")
        require_non_empty_text(self.prediction_id, "prediction_id")
        require_non_empty_text(self.reason, "reason")
        require_enum(self.market, Market, "market")
        require_enum(self.selection, Selection, "selection")
        require_enum(self.decision, Decision, "decision")
        require_aware(self.created_at, "created_at")
        require_aware(self.as_of, "as_of")
        if self.as_of > self.created_at:
            raise ValidationError("as_of must not be later than created_at")
        require_positive(self.odds, "odds")
        if self.odds <= 1.0:
            raise ValidationError(f"odds must be > 1.0, got {self.odds!r}")
        implied = require_probability(self.implied_probability, "implied_probability")
        require_probability(self.model_probability, "model_probability")
        if self.market_probability is not None:
            require_probability(self.market_probability, "market_probability")
        expected = 1.0 / self.odds
        if abs(implied - expected) > IMPLIED_PROBABILITY_TOLERANCE:
            raise ValidationError(
                f"implied_probability ({implied!r}) must equal 1 / odds ({expected!r}); "
                "use market_probability if you mean a de-vigged estimate"
            )

    @property
    def edge(self) -> float:
        """Expected return per unit staked, using the model's own probability."""
        return self.model_probability * self.odds - 1.0


@dataclass(frozen=True, slots=True)
class MatchResult:
    """The outcome of a finished fixture.

    This object is post-match by construction: its ``phase`` is always
    ``POST_MATCH``, and the feature layer rejects it as an input. It is an
    evaluation label, never a predictor.

    ``finished_at`` is when the match ended; ``recorded_at`` is when *we*
    entered the scoreline. Both are needed, because "the match finished at 17:00"
    does not mean "we knew the score at 17:00" - the second date is the one that
    governs what a historical replay may claim to have known.
    """

    match_id: str
    kickoff_at: datetime
    finished_at: datetime
    recorded_at: datetime
    home_goals: int
    away_goals: int
    status: MatchStatus = MatchStatus.PLAYED

    def __post_init__(self) -> None:
        require_non_empty_text(self.match_id, "match_id")
        require_aware(self.kickoff_at, "kickoff_at")
        require_aware(self.finished_at, "finished_at")
        require_aware(self.recorded_at, "recorded_at")
        require_enum(self.status, MatchStatus, "status")
        if self.finished_at < self.kickoff_at:
            raise ValidationError("finished_at must not be earlier than kickoff_at")
        if self.recorded_at < self.finished_at:
            raise ValidationError(
                f"recorded_at ({self.recorded_at.isoformat()}) must not be earlier than "
                f"finished_at ({self.finished_at.isoformat()})"
            )
        for name, goals in (("home_goals", self.home_goals), ("away_goals", self.away_goals)):
            if isinstance(goals, bool) or not isinstance(goals, int):
                raise ValidationError(f"{name} must be an int, got {type(goals).__name__}")
            if goals < 0:
                raise ValidationError(f"{name} must be >= 0, got {goals!r}")

    @property
    def phase(self) -> MatchPhase:
        """Always :attr:`MatchPhase.POST_MATCH`."""
        return MatchPhase.POST_MATCH

    @property
    def outcome_index(self) -> int:
        """``0`` home win, ``1`` draw, ``2`` away win."""
        if self.home_goals > self.away_goals:
            return 0
        if self.home_goals == self.away_goals:
            return 1
        return 2


@dataclass(frozen=True, slots=True)
class BetRecord:
    """A bet that a **human** placed, logged after the fact, for accounting.

    The system does not place bets and does not talk to any wagering venue
    (see ``docs/project-charter.md`` section 6.3). This record exists so that
    real-world outcomes can be reconciled against recommendations during
    evaluation.
    """

    bet_record_id: str
    recommendation_id: str
    match_id: str
    recorded_at: datetime
    placed_at: datetime
    stake: float
    decimal_odds: float
    status: BetRecordStatus = BetRecordStatus.RECORDED
    payout: float | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.bet_record_id, "bet_record_id")
        require_non_empty_text(self.recommendation_id, "recommendation_id")
        require_non_empty_text(self.match_id, "match_id")
        require_aware(self.recorded_at, "recorded_at")
        require_aware(self.placed_at, "placed_at")
        require_enum(self.status, BetRecordStatus, "status")
        if self.placed_at > self.recorded_at:
            raise ValidationError("placed_at must not be later than recorded_at")
        require_positive(self.stake, "stake")
        require_positive(self.decimal_odds, "decimal_odds")
        if self.decimal_odds <= 1.0:
            raise ValidationError(f"decimal_odds must be > 1.0, got {self.decimal_odds!r}")
        if self.payout is not None and self.payout < 0:
            raise ValidationError("payout must be >= 0 when provided")

    @property
    def profit(self) -> float | None:
        """Net profit, or ``None`` while the bet is unsettled."""
        if self.payout is None:
            return None
        return self.payout - self.stake


def _freeze(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a read-only snapshot of ``mapping``.

    Parameters and results must be captured as they were, so they are stored
    behind a read-only proxy: later mutation of the caller's dict can then
    never rewrite research history.
    """
    return MappingProxyType(dict(mapping))


@dataclass(frozen=True, slots=True)
class Experiment:
    """A pre-registered research experiment and its outcome.

    ``FAILED`` experiments are kept, always. There is no delete path in the
    registry, by design (``docs/experiment-protocol.md``).
    """

    experiment_id: str
    hypothesis: str
    data_version: str
    model_version: str
    created_at: datetime
    status: ExperimentStatus = ExperimentStatus.PLANNED
    parameters: Mapping[str, Any] = field(default_factory=dict)
    result: Mapping[str, Any] | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        require_non_empty_text(self.experiment_id, "experiment_id")
        require_non_empty_text(self.hypothesis, "hypothesis")
        require_non_empty_text(self.data_version, "data_version")
        require_non_empty_text(self.model_version, "model_version")
        require_aware(self.created_at, "created_at")
        require_enum(self.status, ExperimentStatus, "status")
        if self.updated_at is not None:
            require_aware(self.updated_at, "updated_at")
            if self.updated_at < self.created_at:
                raise ValidationError("updated_at must not be earlier than created_at")
        object.__setattr__(self, "parameters", _freeze(self.parameters))
        if self.result is not None:
            object.__setattr__(self, "result", _freeze(self.result))

    def with_result(
        self,
        result: Mapping[str, Any],
        status: ExperimentStatus,
        updated_at: datetime,
    ) -> Experiment:
        """Return a copy carrying ``result``. The original stays untouched."""
        if status is ExperimentStatus.PLANNED:
            raise ValidationError("a completed experiment cannot go back to PLANNED")
        require_aware(updated_at, "updated_at")
        return Experiment(
            experiment_id=self.experiment_id,
            hypothesis=self.hypothesis,
            data_version=self.data_version,
            model_version=self.model_version,
            created_at=self.created_at,
            status=status,
            parameters=self.parameters,
            result=result,
            updated_at=updated_at,
        )
