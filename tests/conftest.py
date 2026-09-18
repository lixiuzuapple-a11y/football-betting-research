"""Shared fixtures.

All time values are timezone-aware UTC and all objects are synthetic. Synthesised
inputs are fine here - this is a unit-test boundary, and the point of these
objects is to exercise the *machinery*, not to forecast anything.

The ``prediction`` fixture is **not a model**. It is a hand-written probability
triple used to check that the decision layer's arithmetic and guards behave. The
package itself ships no predictor at all.

Timeline of the default fixture (all UTC):

===================  ==========================
``kickoff``          2026-09-20 18:00
``prediction.as_of`` 2026-09-20 10:00
``pred.created_at``  2026-09-20 11:00
``decision moment``  2026-09-20 12:00
===================  ==========================
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from football_betting.decision import DecisionPolicy, decide
from football_betting.domain import (
    BetRecord,
    Market,
    Match,
    MatchResult,
    OddsSnapshot,
    Prediction,
    Recommendation,
    Selection,
)

#: Kickoff used by the default fixtures.
KICKOFF = datetime(2026, 9, 20, 18, 0, tzinfo=timezone.utc)

#: The moment the default decision is taken.
DECISION_MOMENT = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def kickoff() -> datetime:
    return KICKOFF


@pytest.fixture
def decision_moment() -> datetime:
    return DECISION_MOMENT


@pytest.fixture
def match(kickoff: datetime) -> Match:
    return Match(
        match_id="m-0001",
        league="EPL",
        season="2026-27",
        kickoff_at=kickoff,
        home_team_id="team-home",
        away_team_id="team-away",
    )


@pytest.fixture
def prediction(kickoff: datetime) -> Prediction:
    """Hand-written 0.50 / 0.26 / 0.24 forecast. Not a model."""
    return Prediction(
        prediction_id="pred-0001",
        match_id="m-0001",
        created_at=kickoff - timedelta(hours=7),
        as_of=kickoff - timedelta(hours=8),
        model_version="synthetic-fixture-0.0.0",
        data_version="fixture-2026-09-18.1",
        probability_home=0.50,
        probability_draw=0.26,
        probability_away=0.24,
    )


@pytest.fixture
def odds_snapshot(kickoff: datetime) -> OddsSnapshot:
    """A quote for the home side, received well before kickoff."""
    return OddsSnapshot(
        snapshot_id="odds-0001",
        match_id="m-0001",
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        decimal_odds=2.20,
        data_time=kickoff - timedelta(hours=8),
        collected_at=kickoff - timedelta(hours=7, minutes=55),
        source="fixture://synthetic",
        bookmaker="synthetic-book",
    )


@pytest.fixture
def recommendation_factory(match: Match, prediction: Prediction):
    """Build recommendations with overridable odds, selection and policy."""

    def factory(
        odds: float = 2.20,
        selection: Selection = Selection.HOME,
        policy: DecisionPolicy | None = None,
        prediction_obj: Prediction | None = None,
        moment: datetime = DECISION_MOMENT,
    ) -> Recommendation:
        return decide(
            match=match,
            prediction=prediction_obj or prediction,
            market=Market.ONE_X_TWO,
            selection=selection,
            odds=odds,
            as_of=moment,
            created_at=moment,
            policy=policy,
        )

    return factory


@pytest.fixture
def recommendation(recommendation_factory) -> Recommendation:
    """The canonical BUY recommendation: 0.50 at 2.20 gives +10% edge."""
    return recommendation_factory()


@pytest.fixture
def result(kickoff: datetime) -> MatchResult:
    """A finished 2-1 home win, recorded shortly after the final whistle."""
    return MatchResult(
        match_id="m-0001",
        kickoff_at=kickoff,
        finished_at=kickoff + timedelta(hours=2),
        recorded_at=kickoff + timedelta(hours=3),
        home_goals=2,
        away_goals=1,
    )


@pytest.fixture
def bet_record(recommendation: Recommendation, kickoff: datetime) -> BetRecord:
    """A manually placed bet logged against a recommendation."""
    return BetRecord(
        bet_record_id="bet-0001",
        recommendation_id=recommendation.recommendation_id,
        match_id=recommendation.match_id,
        placed_at=kickoff - timedelta(hours=4),
        recorded_at=kickoff - timedelta(hours=3),
        stake=10.0,
        decimal_odds=recommendation.odds,
        note="logged by hand; the system did not place this bet",
    )
