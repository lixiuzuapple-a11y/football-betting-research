"""Requirement 5: a recommendation can be generated."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from football_betting.decision import DecisionPolicy, decide, make_recommendation_id
from football_betting.domain import (
    Decision,
    FutureInformationError,
    Market,
    Match,
    NotImplementedYetError,
    Prediction,
    Selection,
    ValidationError,
)


def test_a_buy_is_generated_when_the_edge_clears_the_threshold(recommendation) -> None:
    assert recommendation.decision is Decision.BUY
    assert recommendation.model_probability == pytest.approx(0.50)
    assert recommendation.edge == pytest.approx(0.10)
    assert "edge" in recommendation.reason


def test_a_pass_is_generated_when_the_edge_is_negative(recommendation_factory) -> None:
    rec = recommendation_factory(odds=1.80)  # 0.50 * 1.80 - 1 = -0.10
    assert rec.decision is Decision.PASS
    assert rec.edge == pytest.approx(-0.10)


def test_the_threshold_is_respected(recommendation_factory) -> None:
    strict = DecisionPolicy(min_edge=0.20)
    assert recommendation_factory(odds=2.20, policy=strict).decision is Decision.PASS
    assert recommendation_factory(odds=2.60, policy=strict).decision is Decision.BUY


def test_the_threshold_boundary_is_inclusive(recommendation_factory) -> None:
    # 0.50 * 2.00 - 1 = exactly 0.0, and min_edge defaults to 0.0
    assert recommendation_factory(odds=2.00).decision is Decision.BUY


def test_quotes_outside_the_accepted_band_pass(recommendation_factory) -> None:
    policy = DecisionPolicy(min_edge=0.0, min_odds=1.50, max_odds=5.00)
    rec = recommendation_factory(odds=12.00, policy=policy)
    assert rec.decision is Decision.PASS
    assert "outside accepted band" in rec.reason


def test_a_negative_threshold_is_refused() -> None:
    with pytest.raises(ValidationError, match="min_edge"):
        DecisionPolicy(min_edge=-0.01)


def test_the_recommendation_id_is_deterministic(recommendation_factory) -> None:
    first = recommendation_factory(odds=2.20)
    second = recommendation_factory(odds=2.20)
    assert first.recommendation_id == second.recommendation_id

    different = recommendation_factory(odds=2.25)
    assert different.recommendation_id != first.recommendation_id


def test_make_recommendation_id_is_stable_and_readable() -> None:
    kwargs = {
        "prediction_id": "pred-0001",
        "match_id": "m-0001",
        "market": Market.ONE_X_TWO,
        "selection": Selection.HOME,
        "odds": 2.2,
        "as_of": datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
    }
    identifier = make_recommendation_id(**kwargs)
    assert identifier == make_recommendation_id(**kwargs)
    assert identifier.startswith("rec_")
    assert len(identifier) == len("rec_") + 16


@pytest.mark.parametrize("market", [Market.HANDICAP_ONE_X_TWO, Market.TOTAL_GOALS])
def test_markets_without_a_model_refuse_to_be_priced(match, prediction, market) -> None:
    moment = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(NotImplementedYetError):
        decide(
            match=match,
            prediction=prediction,
            market=market,
            selection=Selection.HOME,
            odds=2.20,
            as_of=moment,
            created_at=moment,
        )


def test_a_decision_cannot_be_made_after_kickoff(match, prediction, kickoff) -> None:
    with pytest.raises(FutureInformationError, match="pre-match only"):
        decide(
            match=match,
            prediction=prediction,
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            odds=2.20,
            as_of=kickoff + timedelta(minutes=1),
            created_at=kickoff + timedelta(minutes=1),
        )


def test_a_forecast_from_another_match_is_refused(match, prediction, kickoff) -> None:
    other = Match(
        match_id="m-9999",
        league="EPL",
        season="2026-27",
        kickoff_at=kickoff,
        home_team_id="x",
        away_team_id="y",
    )
    moment = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError, match="belongs to match"):
        decide(
            match=other,
            prediction=prediction,
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            odds=2.20,
            as_of=moment,
            created_at=moment,
        )


def test_a_forecast_from_the_future_is_refused(match, kickoff) -> None:
    """The forecast must not have used information we lacked when deciding."""
    later = Prediction(
        prediction_id="pred-late",
        match_id="m-0001",
        created_at=kickoff - timedelta(hours=1),
        as_of=kickoff - timedelta(hours=1, minutes=30),
        model_version="synthetic",
        data_version="d",
        probability_home=0.5,
        probability_draw=0.3,
        probability_away=0.2,
    )
    moment = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(FutureInformationError, match="later than the decision time"):
        decide(
            match=match,
            prediction=later,
            market=Market.ONE_X_TWO,
            selection=Selection.HOME,
            odds=2.20,
            as_of=moment,
            created_at=moment,
        )


def test_each_selection_uses_its_own_probability(recommendation_factory) -> None:
    assert recommendation_factory(selection=Selection.HOME).model_probability == pytest.approx(0.50)
    assert recommendation_factory(selection=Selection.DRAW).model_probability == pytest.approx(0.26)
    assert recommendation_factory(selection=Selection.AWAY).model_probability == pytest.approx(0.24)


def test_a_de_vigged_market_probability_is_recorded_when_supplied(match, prediction) -> None:
    moment = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    rec = decide(
        match=match,
        prediction=prediction,
        market=Market.ONE_X_TWO,
        selection=Selection.HOME,
        odds=2.20,
        as_of=moment,
        created_at=moment,
        market_probability=0.44,
    )
    assert rec.market_probability == pytest.approx(0.44)
    assert rec.implied_probability == pytest.approx(1 / 2.20), (
        "implied_probability stays the raw 1/odds; the de-vigged figure is separate"
    )


def test_the_decision_policy_band_helper() -> None:
    policy = DecisionPolicy(min_odds=1.5, max_odds=5.0)
    assert policy.allows(1.5) and policy.allows(5.0) and policy.allows(3.0)
    assert not policy.allows(1.49) and not policy.allows(5.01)
