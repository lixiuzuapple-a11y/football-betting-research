"""Evaluation layer: forecast quality and realised outcomes.

Responsibility boundary
-----------------------
This layer answers *"how good was it?"*. It consumes predictions, results and
settled bets; it produces numbers. It does not model, decide, or decide what to
do next.

Note that nothing here is a promise about the future. A backtest ROI is a
measurement of a sample, not an expectation of return.
"""

from __future__ import annotations

from .metrics import (
    AWAY,
    DRAW,
    HOME,
    LOG_LOSS_EPSILON,
    N_OUTCOMES,
    accuracy,
    brier_score,
    calibration_curve,
    log_loss,
    profit,
    roi,
    strike_rate,
)

__all__ = [
    "AWAY",
    "DRAW",
    "HOME",
    "LOG_LOSS_EPSILON",
    "N_OUTCOMES",
    "accuracy",
    "brier_score",
    "calibration_curve",
    "log_loss",
    "profit",
    "roi",
    "strike_rate",
]
