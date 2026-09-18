"""Append-only record store.

Every write is an append. There is no ``update`` and no ``delete``, because a
research record that can be quietly rewritten is not evidence. Corrections are
new rows that supersede old ones, and the old ones stay visible.

``state_as_of`` is the point of the whole layer: it reconstructs what the system
knew at a past instant, which is what makes a backtest honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..domain.enums import MatchPhase
from ..domain.errors import (
    DuplicateRecordError,
    FutureInformationError,
    UnknownReferenceError,
)
from ..domain.models import BetRecord, Match, MatchResult, Prediction, Recommendation
from ..domain.validation import require_aware


@dataclass(frozen=True, slots=True)
class KnownState:
    """A reconstruction of everything knowable at one instant.

    This is the answer to the charter's question *"what did this prediction
    actually know?"*: at ``as_of``, exactly these rows existed and no others.
    """

    as_of: datetime
    matches: tuple[Match, ...] = ()
    predictions: tuple[Prediction, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    results: tuple[MatchResult, ...] = ()
    bets: tuple[BetRecord, ...] = ()

    def __len__(self) -> int:
        return (
            len(self.matches)
            + len(self.predictions)
            + len(self.recommendations)
            + len(self.results)
            + len(self.bets)
        )


class RecordStore:
    """In-memory, append-only record store.

    A process-local store, not a database. It exists to make the append-only
    contract and the ``as_of`` reconstruction executable and testable; a durable
    backend arrives when there is real data worth persisting.
    """

    def __init__(self) -> None:
        self._matches: dict[str, Match] = {}
        self._predictions: dict[str, Prediction] = {}
        self._recommendations: dict[str, Recommendation] = {}
        self._results: dict[str, MatchResult] = {}
        self._bets: dict[str, BetRecord] = {}

    # -- writes ------------------------------------------------------------

    def record_match(self, match: Match) -> Match:
        """Register a fixture."""
        self._reject_duplicate(self._matches, match.match_id, "match")
        self._matches[match.match_id] = match
        return match

    def record_prediction(self, prediction: Prediction) -> Prediction:
        """Store a forecast.

        A prediction must be pre-match: a forecast stamped at or after kickoff
        is not a forecast.
        """
        self._reject_duplicate(self._predictions, prediction.prediction_id, "prediction")
        match = self._require_match(prediction.match_id, "prediction")
        if match.phase_at(prediction.created_at) is not MatchPhase.PRE_MATCH:
            raise FutureInformationError(
                f"prediction {prediction.prediction_id!r} was created at "
                f"{prediction.created_at.isoformat()}, which is not before kickoff "
                f"{match.kickoff_at.isoformat()}"
            )
        self._predictions[prediction.prediction_id] = prediction
        return prediction

    def record_recommendation(self, recommendation: Recommendation) -> Recommendation:
        """Store a recommendation, checking it is pre-match and traceable."""
        self._reject_duplicate(
            self._recommendations, recommendation.recommendation_id, "recommendation"
        )
        match = self._require_match(recommendation.match_id, "recommendation")
        if recommendation.prediction_id not in self._predictions:
            raise UnknownReferenceError(
                f"recommendation {recommendation.recommendation_id!r} references unknown "
                f"prediction {recommendation.prediction_id!r}"
            )
        if match.phase_at(recommendation.created_at) is not MatchPhase.PRE_MATCH:
            raise FutureInformationError(
                f"recommendation {recommendation.recommendation_id!r} was created at "
                f"{recommendation.created_at.isoformat()}, which is not before kickoff"
            )
        self._recommendations[recommendation.recommendation_id] = recommendation
        return recommendation

    def record_result(self, result: MatchResult) -> MatchResult:
        """Store a final score as an evaluation label."""
        self._reject_duplicate(self._results, result.match_id, "result")
        match = self._require_match(result.match_id, "result")
        if result.recorded_at < match.kickoff_at:
            raise FutureInformationError(
                f"result for {result.match_id!r} claims to have been recorded at "
                f"{result.recorded_at.isoformat()}, before kickoff "
                f"{match.kickoff_at.isoformat()}"
            )
        self._results[result.match_id] = result
        return result

    def record_bet(self, bet: BetRecord) -> BetRecord:
        """Store a bet a human placed.

        This records reality for reconciliation. It does not place anything.
        """
        self._reject_duplicate(self._bets, bet.bet_record_id, "bet record")
        self._require_match(bet.match_id, "bet record")
        if bet.recommendation_id not in self._recommendations:
            raise UnknownReferenceError(
                f"bet record {bet.bet_record_id!r} references unknown recommendation "
                f"{bet.recommendation_id!r}"
            )
        self._bets[bet.bet_record_id] = bet
        return bet

    # -- reads -------------------------------------------------------------

    def match(self, match_id: str) -> Match:
        """Return a fixture, or raise."""
        return self._require_match(match_id, "lookup")

    def prediction(self, prediction_id: str) -> Prediction:
        """Return a forecast, or raise."""
        try:
            return self._predictions[prediction_id]
        except KeyError as exc:
            raise UnknownReferenceError(f"unknown prediction {prediction_id!r}") from exc

    def state_as_of(self, as_of: datetime) -> KnownState:
        """Everything knowable at ``as_of``.

        Rows are included only if they existed by then:

        * predictions and recommendations by ``created_at``;
        * results by ``recorded_at``, not ``finished_at`` - we may learn a
          scoreline well after the final whistle;
        * bets by ``recorded_at``.

        Fixtures are included by kickoff: a fixture whose kickoff is in the
        future was still on the calendar at ``as_of``.
        """
        require_aware(as_of, "as_of")
        return KnownState(
            as_of=as_of,
            matches=tuple(m for m in self._matches.values() if m.kickoff_at <= as_of),
            predictions=tuple(p for p in self._predictions.values() if p.created_at <= as_of),
            recommendations=tuple(
                r for r in self._recommendations.values() if r.created_at <= as_of
            ),
            results=tuple(r for r in self._results.values() if r.recorded_at <= as_of),
            bets=tuple(b for b in self._bets.values() if b.recorded_at <= as_of),
        )

    def counts(self) -> dict[str, int]:
        """Row counts by collection. Handy for reports and tests."""
        return {
            "matches": len(self._matches),
            "predictions": len(self._predictions),
            "recommendations": len(self._recommendations),
            "results": len(self._results),
            "bets": len(self._bets),
        }

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _reject_duplicate(store: dict, key: str, label: str) -> None:
        if key in store:
            raise DuplicateRecordError(
                f"a {label} with id {key!r} already exists; the store is append-only"
            )

    def _require_match(self, match_id: str, label: str) -> Match:
        try:
            return self._matches[match_id]
        except KeyError as exc:
            raise UnknownReferenceError(f"{label} references unknown match {match_id!r}") from exc
