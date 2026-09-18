"""Decision layer: compare a forecast against a market price.

Responsibility boundary
-----------------------
This layer answers exactly one question: *given what the model thinks and what
the price implies, does this selection clear the policy threshold?* It produces
a ``Recommendation`` - a recorded opinion, not an instruction.

It does not place bets, does not size stakes, and does not know how to reach a
wagering venue. ``BUY`` is a label on a row in a table. Nothing in this package
consumes it as a command; see ``docs/project-charter.md`` section 6.3.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from ..domain.enums import ONE_X_TWO_MARKETS, Decision, Market, MatchPhase, Selection
from ..domain.errors import FutureInformationError, NotImplementedYetError, ValidationError
from ..domain.models import Match, Prediction, Recommendation
from ..domain.validation import require_aware
from ..odds.implied import implied_probability, validate_decimal_odds

#: Bookmaker margin tolerance when a raw quote is used as a market estimate.
DEFAULT_MIN_EDGE = 0.0


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    """The rule that turns an edge into a decision.

    Deliberately tiny and explicit. Stage 1 has no stake sizing, no Kelly
    fraction and no bankroll model - those are strategy, and strategy comes
    after the pipeline can be trusted.
    """

    #: Minimum expected return per unit staked required to record a ``BUY``.
    min_edge: float = DEFAULT_MIN_EDGE
    #: Quotes outside this band are treated as unusable and give a ``PASS``.
    min_odds: float = 1.01
    max_odds: float = 1000.0

    def __post_init__(self) -> None:
        if isinstance(self.min_edge, bool) or not isinstance(self.min_edge, (int, float)):
            raise ValidationError("min_edge must be a number")
        if self.min_edge < 0.0:
            raise ValidationError(
                f"min_edge must be >= 0, got {self.min_edge!r}: a negative threshold would "
                "record negative-expectation recommendations"
            )
        validate_decimal_odds(self.min_odds)
        validate_decimal_odds(self.max_odds)
        if self.max_odds < self.min_odds:
            raise ValidationError("max_odds must not be below min_odds")

    def allows(self, odds: float) -> bool:
        """Whether a quote is inside the accepted band."""
        return self.min_odds <= odds <= self.max_odds


def make_recommendation_id(
    *,
    prediction_id: str,
    match_id: str,
    market: Market,
    selection: Selection,
    odds: float,
    as_of: datetime,
) -> str:
    """Derive a stable identifier from the inputs that produced the decision.

    Deterministic on purpose: re-running the same decision must be able to
    produce the same id, so a duplicate is detectable rather than silently
    appended as a second row.
    """
    payload = "|".join(
        [
            prediction_id,
            match_id,
            market.value,
            selection.value,
            f"{odds:.6f}",
            as_of.isoformat(),
        ]
    )
    return "rec_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def decide(
    *,
    match: Match,
    prediction: Prediction,
    market: Market,
    selection: Selection,
    odds: float,
    as_of: datetime,
    created_at: datetime,
    policy: DecisionPolicy | None = None,
    market_probability: float | None = None,
    recommendation_id: str | None = None,
) -> Recommendation:
    """Compare ``prediction`` against ``odds`` and record the outcome.

    Raises
    ------
    FutureInformationError
        If the decision moment is not strictly before kickoff, if the forecast
        is newer than the decision, or if the forecast was created after the
        decision was taken.
    NotImplementedYetError
        If ``market`` is not one a 1X2 forecast can price.
    ValidationError
        If the prediction does not belong to ``match``, or ``odds`` is unusable.
    """
    policy = policy or DecisionPolicy()
    require_aware(as_of, "as_of")
    require_aware(created_at, "created_at")

    if match.phase_at(as_of) is not MatchPhase.PRE_MATCH:
        raise FutureInformationError(
            f"as_of ({as_of.isoformat()}) is not before kickoff "
            f"({match.kickoff_at.isoformat()}): decisions are pre-match only"
        )
    if prediction.match_id != match.match_id:
        raise ValidationError(
            f"prediction {prediction.prediction_id!r} belongs to match "
            f"{prediction.match_id!r}, not {match.match_id!r}"
        )
    if prediction.as_of > as_of:
        raise FutureInformationError(
            f"prediction was built at as_of {prediction.as_of.isoformat()}, later than the "
            f"decision time {as_of.isoformat()}: the forecast used information we did not "
            "have when we decided"
        )
    if prediction.created_at > created_at:
        raise FutureInformationError(
            f"prediction was created at {prediction.created_at.isoformat()}, later than the "
            f"decision at {created_at.isoformat()}"
        )
    if market not in ONE_X_TWO_MARKETS:
        raise NotImplementedYetError(
            f"market {market.value!r} cannot be priced from a 1X2 forecast; it needs its own "
            "model and its own experiment record"
        )

    odds = validate_decimal_odds(odds)
    implied = implied_probability(odds)
    model_probability = prediction.probability_for(selection)
    edge = model_probability * odds - 1.0

    if not policy.allows(odds):
        decision = Decision.PASS
        reason = (
            f"odds {odds:.4f} outside accepted band [{policy.min_odds:.4f}, {policy.max_odds:.4f}]"
        )
    elif edge >= policy.min_edge:
        decision = Decision.BUY
        reason = (
            f"model {model_probability:.6f} vs implied {implied:.6f} at odds {odds:.4f} "
            f"gives edge {edge:+.6f} >= min_edge {policy.min_edge:.6f}"
        )
    else:
        decision = Decision.PASS
        reason = (
            f"edge {edge:+.6f} below min_edge {policy.min_edge:.6f} "
            f"(model {model_probability:.6f} vs implied {implied:.6f} at odds {odds:.4f})"
        )

    return Recommendation(
        recommendation_id=recommendation_id
        or make_recommendation_id(
            prediction_id=prediction.prediction_id,
            match_id=match.match_id,
            market=market,
            selection=selection,
            odds=odds,
            as_of=as_of,
        ),
        match_id=match.match_id,
        prediction_id=prediction.prediction_id,
        created_at=created_at,
        as_of=as_of,
        market=market,
        selection=selection,
        odds=odds,
        implied_probability=implied,
        model_probability=model_probability,
        decision=decision,
        reason=reason,
        market_probability=market_probability,
    )
