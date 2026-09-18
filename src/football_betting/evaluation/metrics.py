"""Scoring rules and calibration diagnostics.

Pure functions over numbers. No data loading, no models, no decisions.

Two families live here, and they answer different questions:

* **Forecast quality** - ``brier_score``, ``log_loss``, ``accuracy``: how good
  were the probabilities, judged as probabilities?
* **Outcome quality** - ``roi``, ``profit``, ``strike_rate``: what would the
  recorded recommendations have returned?

A model can improve on the first while making the second worse, which is why
both are always reported together.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from ..domain.errors import ValidationError
from ..domain.validation import require_positive, require_probability

#: Probability floor used by the logarithmic score, to keep ``log(0)`` finite.
#: Documented rather than hidden: it makes a confidently wrong forecast costly
#: but not infinite.
LOG_LOSS_EPSILON = 1e-15

#: Number of outcomes in a 1X2 forecast.
N_OUTCOMES = 3

#: Home win.
HOME, DRAW, AWAY = 0, 1, 2


def _check_sample(probabilities: Sequence[float], outcome: int, index: int) -> tuple[float, ...]:
    if len(probabilities) != N_OUTCOMES:
        raise ValidationError(
            f"sample {index}: expected {N_OUTCOMES} probabilities, got {len(probabilities)}"
        )
    vector = tuple(
        require_probability(p, f"sample {index} probability[{k}]")
        for k, p in enumerate(probabilities)
    )
    total = sum(vector)
    if abs(total - 1.0) > 1e-6:
        raise ValidationError(f"sample {index}: probabilities sum to {total!r}, not 1.0")
    if isinstance(outcome, bool) or not isinstance(outcome, int):
        raise ValidationError(
            f"sample {index}: outcome must be an int, got {type(outcome).__name__}"
        )
    if not 0 <= outcome < N_OUTCOMES:
        raise ValidationError(f"sample {index}: outcome must be in 0..2, got {outcome!r}")
    return vector


def _pairs(
    probabilities: Iterable[Sequence[float]],
    outcomes: Sequence[int],
) -> list[tuple[tuple[float, ...], int]]:
    rows = list(probabilities)
    if len(rows) != len(outcomes):
        raise ValidationError(f"got {len(rows)} probability rows but {len(outcomes)} outcomes")
    if not rows:
        raise ValidationError("no samples supplied")
    return [
        (_check_sample(row, outcome, index), outcome)
        for index, (row, outcome) in enumerate(zip(rows, outcomes, strict=True))
    ]


def brier_score(
    probabilities: Iterable[Sequence[float]],
    outcomes: Sequence[int],
) -> float:
    """Mean multi-class Brier score. Lower is better; ``0`` is perfect.

    The per-sample score is ``sum_k (p_k - y_k) ** 2`` over the one-hot outcome
    vector, so it ranges over ``[0, 2]``. A forecast of ``(1, 0, 0)`` on the
    true outcome scores ``0``; the same forecast on the opposite outcome scores
    ``2``.
    """
    pairs = _pairs(probabilities, outcomes)
    total = 0.0
    for vector, outcome in pairs:
        total += sum((p - (1.0 if k == outcome else 0.0)) ** 2 for k, p in enumerate(vector))
    return total / len(pairs)


def log_loss(
    probabilities: Iterable[Sequence[float]],
    outcomes: Sequence[int],
) -> float:
    """Mean negative log-likelihood. Lower is better.

    Probabilities are clamped to ``LOG_LOSS_EPSILON`` before the logarithm, so
    an over-confident miss is heavily penalised but finite.
    """
    pairs = _pairs(probabilities, outcomes)
    total = 0.0
    for vector, outcome in pairs:
        p = max(vector[outcome], LOG_LOSS_EPSILON)
        total -= math.log(p)
    return total / len(pairs)


def accuracy(
    probabilities: Iterable[Sequence[float]],
    outcomes: Sequence[int],
) -> float:
    """Share of samples where the largest probability matched the outcome.

    Ties go to the lowest index, which in a 1X2 ordering means home. The rule is
    stated because an unstated tie rule makes the number irreproducible.
    """
    pairs = _pairs(probabilities, outcomes)
    hits = sum(1 for vector, outcome in pairs if vector.index(max(vector)) == outcome)
    return hits / len(pairs)


def calibration_curve(
    predicted: Sequence[float],
    observed: Sequence[bool],
    *,
    n_bins: int = 10,
) -> tuple[tuple[float, float, int, float, float], ...]:
    """Bin forecasts and compare predicted probability with observed frequency.

    Parameters
    ----------
    predicted
        Predicted probability of the event, one per sample.
    observed
        Whether the event happened, one per sample.
    n_bins
        Number of equal-width bins over ``[0, 1]``.

    Returns
    -------
    tuple of ``(bin_low, bin_high, count, mean_predicted, observed_frequency)``
    for non-empty bins, in ascending order. A well-calibrated forecaster has
    ``mean_predicted`` close to ``observed_frequency`` in every bin.
    """
    if n_bins < 1:
        raise ValidationError(f"n_bins must be >= 1, got {n_bins!r}")
    if len(predicted) != len(observed):
        raise ValidationError(f"got {len(predicted)} predictions but {len(observed)} observations")
    if not predicted:
        raise ValidationError("no samples supplied")

    buckets: list[list[tuple[float, bool]]] = [[] for _ in range(n_bins)]
    for i, (p, hit) in enumerate(zip(predicted, observed, strict=True)):
        probability = require_probability(p, f"predicted[{i}]")
        if not isinstance(hit, bool):
            raise ValidationError(f"observed[{i}] must be a bool, got {type(hit).__name__}")
        index = min(int(probability * n_bins), n_bins - 1)
        buckets[index].append((probability, hit))

    width = 1.0 / n_bins
    rows: list[tuple[float, float, int, float, float]] = []
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        count = len(bucket)
        mean_predicted = sum(p for p, _ in bucket) / count
        frequency = sum(1 for _, hit in bucket if hit) / count
        rows.append((index * width, (index + 1) * width, count, mean_predicted, frequency))
    return tuple(rows)


def profit(total_staked: float, total_returned: float) -> float:
    """Net profit in staked units."""
    require_positive(total_staked, "total_staked")
    if total_returned < 0:
        raise ValidationError("total_returned must be >= 0")
    return total_returned - total_staked


def roi(total_staked: float, total_returned: float) -> float:
    """Return on investment: ``(returned - staked) / staked``.

    ``0.05`` means five per cent returned per unit staked, stake included. This
    is the number that matters in the end, and the one most easily inflated by a
    handful of long-odds winners - always report it next to the sample size.
    """
    require_positive(total_staked, "total_staked")
    if total_returned < 0:
        raise ValidationError("total_returned must be >= 0")
    return (total_returned - total_staked) / total_staked


def strike_rate(wins: int, settled: int) -> float:
    """Share of settled recommendations that won."""
    if isinstance(settled, bool) or not isinstance(settled, int):
        raise ValidationError("settled must be an int")
    if settled <= 0:
        raise ValidationError(f"settled must be > 0, got {settled!r}")
    if isinstance(wins, bool) or not isinstance(wins, int) or wins < 0:
        raise ValidationError("wins must be a non-negative int")
    if wins > settled:
        raise ValidationError(f"wins ({wins}) cannot exceed settled ({settled})")
    return wins / settled
