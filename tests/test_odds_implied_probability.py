"""Requirement 4: odds to implied probability is computed correctly."""

from __future__ import annotations

import pytest

from football_betting.domain import ValidationError
from football_betting.odds import (
    devig_from_odds,
    devig_multiplicative,
    expected_value_per_unit,
    fair_decimal_odds,
    implied_probability,
    overround,
    overround_from_odds,
    validate_decimal_odds,
)


@pytest.mark.parametrize(
    ("odds", "expected"),
    [
        (1.01, 1 / 1.01),
        (1.25, 0.8),
        (2.0, 0.5),
        (2.5, 0.4),
        (4.0, 0.25),
        (10.0, 0.1),
        (101.0, 1 / 101.0),
    ],
)
def test_implied_probability_is_the_reciprocal(odds: float, expected: float) -> None:
    assert implied_probability(odds) == pytest.approx(expected)


@pytest.mark.parametrize("bad", [1.0, 0.99, 0.0, -1.5])
def test_unusable_odds_are_rejected(bad: float) -> None:
    with pytest.raises(ValidationError):
        implied_probability(bad)


@pytest.mark.parametrize("bad", [True, "2.0", None])
def test_non_numeric_odds_are_rejected(bad: object) -> None:
    with pytest.raises(ValidationError):
        validate_decimal_odds(bad)  # type: ignore[arg-type]


def test_nan_odds_are_rejected() -> None:
    with pytest.raises(ValidationError, match="NaN"):
        implied_probability(float("nan"))


def test_fair_odds_round_trip() -> None:
    for probability in (0.1, 0.25, 0.5, 0.9):
        assert implied_probability(fair_decimal_odds(probability)) == pytest.approx(probability)


def test_fair_odds_of_a_zero_probability_is_undefined() -> None:
    with pytest.raises(ValidationError):
        fair_decimal_odds(0.0)


def test_overround_of_a_full_market() -> None:
    # A book quoting 2.10 / 3.50 / 3.60
    margin = overround_from_odds([2.10, 3.50, 3.60])
    assert margin == pytest.approx(1 / 2.10 + 1 / 3.50 + 1 / 3.60 - 1.0)
    assert margin > 0.0, "a normal book has a positive margin"


def test_overround_of_a_perfectly_fair_book_is_zero() -> None:
    assert overround([0.5, 0.3, 0.2]) == pytest.approx(0.0)


def test_overround_can_be_negative_on_an_arbitrage() -> None:
    """Implied probabilities summing below one means free money, or bad data."""
    assert overround([0.4, 0.4]) == pytest.approx(-0.2)


def test_overround_needs_at_least_one_probability() -> None:
    with pytest.raises(ValidationError):
        overround([])


def test_devig_multiplicative_normalises_to_one() -> None:
    raw = [1 / 2.10, 1 / 3.50, 1 / 3.60]
    fair = devig_multiplicative(raw)
    assert sum(fair) == pytest.approx(1.0)
    assert all(0.0 <= p <= 1.0 for p in fair)
    # Each fair probability must sit below its margin-inclusive counterpart.
    assert all(f < r for f, r in zip(fair, raw, strict=True))


def test_devig_from_odds_preserves_keys() -> None:
    quotes = {"home": 2.10, "draw": 3.50, "away": 3.60}
    fair = devig_from_odds(quotes)
    assert set(fair) == set(quotes)
    assert sum(fair.values()) == pytest.approx(1.0)


def test_devig_from_odds_rejects_an_empty_market() -> None:
    with pytest.raises(ValidationError):
        devig_from_odds({})


def test_devig_removes_exactly_the_margin() -> None:
    raw = [0.5, 0.3, 0.3]  # sums to 1.1
    fair = devig_multiplicative(raw)
    assert sum(fair) == pytest.approx(1.0)
    assert fair[0] == pytest.approx(0.5 / 1.1)


@pytest.mark.parametrize(
    ("probability", "odds", "expected"),
    [
        (0.50, 2.20, 0.10),
        (0.50, 2.00, 0.00),
        (0.50, 1.80, -0.10),
        (0.25, 4.00, 0.00),
        (0.10, 15.00, 0.50),
    ],
)
def test_expected_value_per_unit(probability: float, odds: float, expected: float) -> None:
    assert expected_value_per_unit(probability, odds) == pytest.approx(expected)


def test_implied_probability_matches_the_recommendation_field(recommendation) -> None:
    assert recommendation.implied_probability == pytest.approx(
        implied_probability(recommendation.odds)
    )
