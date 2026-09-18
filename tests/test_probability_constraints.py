"""Requirement 3: probability constraints hold."""

from __future__ import annotations

from datetime import timedelta

import pytest

from football_betting.domain import (
    PROBABILITY_TOLERANCE,
    Market,
    NotImplementedYetError,
    Prediction,
    Selection,
    ValidationError,
    require_probability_vector,
)


def _prediction(kickoff, home: float, draw: float, away: float) -> Prediction:
    return Prediction(
        prediction_id="p",
        match_id="m-0001",
        created_at=kickoff - timedelta(hours=7),
        as_of=kickoff - timedelta(hours=8),
        model_version="synthetic",
        data_version="d",
        probability_home=home,
        probability_draw=draw,
        probability_away=away,
    )


def test_a_valid_vector_is_accepted(kickoff) -> None:
    prediction = _prediction(kickoff, 0.5, 0.26, 0.24)
    assert sum(prediction.probabilities()) == pytest.approx(1.0)


def test_deterministic_certainty_is_accepted(kickoff) -> None:
    assert _prediction(kickoff, 1.0, 0.0, 0.0).probability_home == 1.0


@pytest.mark.parametrize(
    ("home", "draw", "away"),
    [
        (0.5, 0.26, 0.30),  # sums to 1.06
        (0.5, 0.26, 0.20),  # sums to 0.96
        (0.4, 0.3, 0.3),  # sums to 1.00 - valid, included as a control
    ],
)
def test_vectors_summing_away_from_one(kickoff, home: float, draw: float, away: float) -> None:
    total = home + draw + away
    if abs(total - 1.0) <= PROBABILITY_TOLERANCE:
        assert _prediction(kickoff, home, draw, away) is not None
    else:
        with pytest.raises(ValidationError, match="must sum to 1.0"):
            _prediction(kickoff, home, draw, away)


@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, -1.0])
def test_probabilities_outside_zero_one_are_rejected(kickoff, bad: float) -> None:
    with pytest.raises(ValidationError):
        _prediction(kickoff, bad, 0.5, 1.0 - bad if 0 <= bad <= 1 else 0.5)


def test_nan_is_rejected(kickoff) -> None:
    with pytest.raises(ValidationError, match="NaN"):
        _prediction(kickoff, float("nan"), 0.5, 0.5)


def test_tolerance_boundary_is_enforced() -> None:
    require_probability_vector((1 / 3, 1 / 3, 1 / 3), ("a", "b", "c"))
    with pytest.raises(ValidationError):
        require_probability_vector((0.3333, 0.3333, 0.3333), ("a", "b", "c"))


def test_probability_for_maps_one_x_two_selections(prediction: Prediction) -> None:
    assert prediction.probability_for(Selection.HOME) == pytest.approx(0.50)
    assert prediction.probability_for(Selection.DRAW) == pytest.approx(0.26)
    assert prediction.probability_for(Selection.AWAY) == pytest.approx(0.24)


@pytest.mark.parametrize("selection", [Selection.OVER, Selection.UNDER])
def test_probability_for_refuses_markets_without_model_output(
    prediction: Prediction, selection: Selection
) -> None:
    """A 1X2 forecast must not be stretched to price totals."""
    with pytest.raises(NotImplementedYetError):
        prediction.probability_for(selection)


def test_handicap_market_is_not_implicitly_priceable() -> None:
    from football_betting.domain import ONE_X_TWO_MARKETS

    assert Market.ONE_X_TWO in ONE_X_TWO_MARKETS
    assert Market.HANDICAP_ONE_X_TWO not in ONE_X_TWO_MARKETS, (
        "a handicap market needs its own model; reusing the plain 1X2 distribution "
        "would be a modelling error"
    )
