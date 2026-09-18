"""Scoring rules and calibration diagnostics."""

from __future__ import annotations

import math

import pytest

from football_betting.domain import ValidationError
from football_betting.evaluation import (
    accuracy,
    brier_score,
    calibration_curve,
    log_loss,
    profit,
    roi,
    strike_rate,
)

PERFECT = (1.0, 0.0, 0.0)
UNIFORM = (1 / 3, 1 / 3, 1 / 3)


def test_a_perfect_forecast_scores_zero() -> None:
    assert brier_score([PERFECT], [0]) == pytest.approx(0.0)
    assert log_loss([PERFECT], [0]) == pytest.approx(0.0)
    assert accuracy([PERFECT], [0]) == pytest.approx(1.0)


def test_a_confidently_wrong_forecast_scores_the_worst_brier() -> None:
    assert brier_score([PERFECT], [2]) == pytest.approx(2.0)


def test_a_uniform_forecast_scores_the_uniform_benchmark() -> None:
    # sum((1/3 - y)^2) = 2 * (1/3)^2 + (2/3)^2 = 6/9
    assert brier_score([UNIFORM], [0]) == pytest.approx(6 / 9)
    assert log_loss([UNIFORM], [0]) == pytest.approx(math.log(3))
    assert accuracy([UNIFORM], [0]) == pytest.approx(1.0), "ties resolve to lowest index"


@pytest.mark.parametrize("outcome", [0, 1, 2])
def test_log_loss_penalises_the_true_class_only(outcome: int) -> None:
    vector = (0.6, 0.3, 0.1)
    assert log_loss([vector], [outcome]) == pytest.approx(-math.log(vector[outcome]))


def test_an_over_confident_miss_stays_finite() -> None:
    from football_betting.evaluation import LOG_LOSS_EPSILON

    value = log_loss([PERFECT], [1])
    assert math.isfinite(value)
    assert value == pytest.approx(-math.log(LOG_LOSS_EPSILON))


def test_aggregation_is_the_mean_over_samples() -> None:
    rows = [PERFECT, (0.0, 0.0, 1.0)]
    assert brier_score(rows, [0, 2]) == pytest.approx(0.0)
    assert brier_score(rows, [0, 0]) == pytest.approx(1.0)


def test_length_mismatches_are_refused() -> None:
    with pytest.raises(ValidationError, match="outcomes"):
        brier_score([PERFECT], [0, 1])


def test_an_empty_sample_is_refused() -> None:
    with pytest.raises(ValidationError, match="no samples"):
        brier_score([], [])


def test_an_out_of_range_outcome_is_refused() -> None:
    with pytest.raises(ValidationError, match="outcome must be in 0..2"):
        brier_score([PERFECT], [3])


def test_a_non_normalised_vector_is_refused() -> None:
    with pytest.raises(ValidationError, match="sum to"):
        brier_score([(0.5, 0.5, 0.5)], [0])


def test_a_wrong_length_vector_is_refused() -> None:
    with pytest.raises(ValidationError, match="expected 3 probabilities"):
        brier_score([(0.5, 0.5)], [0])


def test_accuracy_counts_the_modal_class() -> None:
    rows = [(0.6, 0.3, 0.1), (0.2, 0.5, 0.3), (0.1, 0.3, 0.6)]
    assert accuracy(rows, [0, 1, 2]) == pytest.approx(1.0)
    assert accuracy(rows, [2, 1, 0]) == pytest.approx(1 / 3)


def test_calibration_curve_groups_by_predicted_probability() -> None:
    rows = calibration_curve([0.05, 0.15, 0.95] * 2, [False, False, True] * 2, n_bins=10)
    assert len(rows) == 3
    for low, high, count, mean_predicted, _frequency in rows:
        assert low < high
        assert count == 2
        assert low <= mean_predicted <= high
    # The 0.95 bin fires every time: well calibrated.
    assert rows[-1][4] == pytest.approx(1.0)
    assert rows[-1][3] == pytest.approx(0.95)


def test_calibration_curve_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValidationError):
        calibration_curve([0.5], [True, False])


def test_calibration_curve_puts_one_into_the_last_bin() -> None:
    rows = calibration_curve([1.0], [True], n_bins=10)
    assert rows[0][:2] == pytest.approx((0.9, 1.0))


def test_calibration_curve_needs_samples() -> None:
    with pytest.raises(ValidationError, match="no samples"):
        calibration_curve([], [])


@pytest.mark.parametrize(
    ("staked", "returned", "expected_roi", "expected_profit"),
    [
        (100.0, 110.0, 0.10, 10.0),
        (100.0, 100.0, 0.0, 0.0),
        (100.0, 85.0, -0.15, -15.0),
        (50.0, 0.0, -1.0, -50.0),
    ],
)
def test_profit_and_roi(
    staked: float, returned: float, expected_roi: float, expected_profit: float
) -> None:
    assert roi(staked, returned) == pytest.approx(expected_roi)
    assert profit(staked, returned) == pytest.approx(expected_profit)


def test_roi_needs_a_positive_stake() -> None:
    with pytest.raises(ValidationError):
        roi(0.0, 10.0)


def test_strike_rate() -> None:
    assert strike_rate(0, 10) == pytest.approx(0.0)
    assert strike_rate(5, 10) == pytest.approx(0.5)
    assert strike_rate(10, 10) == pytest.approx(1.0)


def test_strike_rate_refuses_impossible_inputs() -> None:
    with pytest.raises(ValidationError, match="cannot exceed"):
        strike_rate(11, 10)
    with pytest.raises(ValidationError, match="settled"):
        strike_rate(0, 0)
