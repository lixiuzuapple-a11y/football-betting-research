"""Walk-forward splitting, and the backtest entry point refusing to fake it."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from football_betting.backtest import (
    BacktestSpec,
    WalkForwardWindow,
    run_backtest,
    walk_forward_windows,
)
from football_betting.decision import DecisionPolicy
from football_betting.domain import NotImplementedYetError, ValidationError
from football_betting.models import UnimplementedPredictor


def test_windows_advance_by_the_step() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 4, tzinfo=timezone.utc)
    windows = walk_forward_windows(
        start=start, end=end, step=timedelta(days=1), train_span=timedelta(days=1)
    )
    assert [w.test_as_of for w in windows] == [
        start + timedelta(days=1),
        start + timedelta(days=2),
        start + timedelta(days=3),
    ]


def test_every_window_trains_before_it_tests() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    windows = walk_forward_windows(
        start=start,
        end=datetime(2026, 3, 1, tzinfo=timezone.utc),
        step=timedelta(days=7),
        train_span=timedelta(days=30),
    )
    assert windows, "the fixture should produce windows"
    for window in windows:
        assert window.train_end <= window.test_as_of
        assert window.train_start < window.train_end


def test_a_positive_gap_is_respected() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    windows = walk_forward_windows(
        start=start,
        end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        step=timedelta(days=7),
        train_span=timedelta(days=14),
        gap=timedelta(days=3),
    )
    for window in windows:
        assert window.gap == timedelta(days=3)
        assert window.train_end + timedelta(days=3) == window.test_as_of


def test_windows_are_strictly_increasing() -> None:
    windows = walk_forward_windows(
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        step=timedelta(days=2),
        train_span=timedelta(days=5),
    )
    moments = [w.test_as_of for w in windows]
    assert moments == sorted(moments)
    assert len(set(moments)) == len(moments)


def test_a_window_that_tests_before_it_trains_is_refused() -> None:
    with pytest.raises(ValidationError, match="predict from the future"):
        WalkForwardWindow(
            train_start=datetime(2026, 1, 2, tzinfo=timezone.utc),
            train_end=datetime(2026, 1, 10, tzinfo=timezone.utc),
            test_as_of=datetime(2026, 1, 5, tzinfo=timezone.utc),
        )


def test_a_window_with_no_training_period_is_refused() -> None:
    same = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError, match="train_end"):
        WalkForwardWindow(train_start=same, train_end=same, test_as_of=same)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"step": timedelta(0)}, "step"),
        ({"step": -timedelta(days=1)}, "step"),
        ({"train_span": timedelta(0)}, "train_span"),
        ({"gap": -timedelta(days=1)}, "gap"),
    ],
)
def test_nonsensical_schedules_are_refused(kwargs: dict, message: str) -> None:
    base = {
        "start": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "end": datetime(2026, 2, 1, tzinfo=timezone.utc),
        "step": timedelta(days=1),
        "train_span": timedelta(days=1),
    }
    with pytest.raises(ValidationError, match=message):
        walk_forward_windows(**{**base, **kwargs})


def test_an_inverted_period_is_refused() -> None:
    moment = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError, match="end must be later"):
        walk_forward_windows(
            start=moment,
            end=moment,
            step=timedelta(days=1),
            train_span=timedelta(days=1),
        )


def test_a_spec_needs_windows() -> None:
    with pytest.raises(ValidationError, match="at least one window"):
        BacktestSpec(
            name="empty",
            data_version="d",
            feature_version="f",
            model_version="m",
            windows=(),
            policy=DecisionPolicy(),
        )


def test_the_backtest_refuses_a_non_predictor() -> None:
    spec = _spec()
    with pytest.raises(ValidationError, match="does not implement the Predictor"):
        run_backtest(spec, predictor=object())  # type: ignore[arg-type]


def test_the_backtest_is_honestly_unimplemented() -> None:
    """A real model does not exist, so a replay cannot be produced."""
    spec = _spec()
    with pytest.raises(NotImplementedYetError, match="backtest replay is not implemented"):
        run_backtest(spec, predictor=UnimplementedPredictor())


def _spec() -> BacktestSpec:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return BacktestSpec(
        name="smoke",
        data_version="fixture-2026-09-18.1",
        feature_version="v0",
        model_version="none",
        windows=walk_forward_windows(
            start=start,
            end=datetime(2026, 1, 10, tzinfo=timezone.utc),
            step=timedelta(days=1),
            train_span=timedelta(days=1),
        ),
        policy=DecisionPolicy(),
    )
