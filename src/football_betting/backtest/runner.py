"""Walk-forward splitting and the backtest entry point.

Implemented and tested here: window generation with an explicit train/test gap,
which is the structural half of preventing look-ahead in a historical replay.

Not implemented: the actual replay. A replay needs features and a model, and
neither exists. ``run_backtest`` validates its inputs and then refuses, rather
than returning an empty result set that would look like a clean run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..decision.engine import DecisionPolicy
from ..domain.errors import NotImplementedYetError, ValidationError
from ..domain.validation import require_aware, require_non_empty_text
from ..models.base import Predictor


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    """One train/test split in a historical replay.

    The ordering constraint is the whole point: ``train_end`` is never later than
    ``test_as_of``, so a window can never train on the period it is predicting.
    """

    train_start: datetime
    train_end: datetime
    test_as_of: datetime

    def __post_init__(self) -> None:
        require_aware(self.train_start, "train_start")
        require_aware(self.train_end, "train_end")
        require_aware(self.test_as_of, "test_as_of")
        if self.train_end <= self.train_start:
            raise ValidationError("train_end must be later than train_start")
        if self.test_as_of < self.train_end:
            raise ValidationError(
                f"test_as_of ({self.test_as_of.isoformat()}) must not be earlier than "
                f"train_end ({self.train_end.isoformat()}): that would predict from the "
                "future"
            )

    @property
    def gap(self) -> timedelta:
        """Separation between the training cutoff and the decision instant."""
        return self.test_as_of - self.train_end


def walk_forward_windows(
    *,
    start: datetime,
    end: datetime,
    step: timedelta,
    train_span: timedelta,
    gap: timedelta = timedelta(0),
) -> tuple[WalkForwardWindow, ...]:
    """Generate successive train/test splits over ``[start, end]``.

    Parameters
    ----------
    start, end
        Bounds of the replay period.
    step
        How far the decision instant advances between windows.
    train_span
        How much history each window trains on.
    gap
        Embargo between the end of training and the decision instant. Zero is
        the minimum; a positive gap is how you avoid a window trained on data
        that overlaps the thing it is predicting.

    Returns windows in ascending ``test_as_of`` order. The first decision
    instant is ``start + train_span + gap``.
    """
    require_aware(start, "start")
    require_aware(end, "end")
    if step <= timedelta(0):
        raise ValidationError(f"step must be positive, got {step!r}")
    if train_span <= timedelta(0):
        raise ValidationError(f"train_span must be positive, got {train_span!r}")
    if gap < timedelta(0):
        raise ValidationError(f"gap must not be negative, got {gap!r}")
    if end <= start:
        raise ValidationError("end must be later than start")

    windows: list[WalkForwardWindow] = []
    test_as_of = start + train_span + gap
    while test_as_of <= end:
        windows.append(
            WalkForwardWindow(
                train_start=test_as_of - gap - train_span,
                train_end=test_as_of - gap,
                test_as_of=test_as_of,
            )
        )
        test_as_of += step
    return tuple(windows)


@dataclass(frozen=True, slots=True)
class BacktestSpec:
    """What a replay is supposed to do, written down before it runs."""

    name: str
    data_version: str
    feature_version: str
    model_version: str
    windows: tuple[WalkForwardWindow, ...]
    policy: DecisionPolicy

    def __post_init__(self) -> None:
        require_non_empty_text(self.name, "name")
        require_non_empty_text(self.data_version, "data_version")
        require_non_empty_text(self.feature_version, "feature_version")
        require_non_empty_text(self.model_version, "model_version")
        if not self.windows:
            raise ValidationError("a backtest needs at least one window")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Placeholder for the replay output. Nothing produces one yet."""

    spec_name: str
    windows: int
    recommendations: int
    metrics: dict[str, float]


def run_backtest(
    spec: BacktestSpec,
    *,
    predictor: Predictor,
) -> BacktestResult:
    """Replay ``spec`` over history.

    Raises
    ------
    ValidationError
        If ``predictor`` does not implement the ``Predictor`` interface.
    NotImplementedYetError
        Always, at present, after the input checks pass.

    The checks come first so that the failure message distinguishes "you wired
    this up wrong" from "this is not built yet".
    """
    if not isinstance(predictor, Predictor):
        raise ValidationError(
            f"{type(predictor).__name__} does not implement the Predictor interface "
            "(a version attribute and a predict method)"
        )
    raise NotImplementedYetError(
        f"backtest replay is not implemented (spec={spec.name!r}, "
        f"model_version={spec.model_version!r}). It requires featurisation and a real "
        "model, neither of which exists yet; see docs/architecture.md."
    )
