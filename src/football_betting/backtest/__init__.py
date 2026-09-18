"""Backtest layer: historical replay under strict time discipline.

Responsibility boundary
-----------------------
This layer answers *"would this have worked, using only what was known at the
time?"*. It orchestrates the other layers over history; it does not itself
model, decide or score.

Window generation is implemented and tested. The replay itself is not.
"""

from __future__ import annotations

from .runner import (
    BacktestResult,
    BacktestSpec,
    WalkForwardWindow,
    run_backtest,
    walk_forward_windows,
)

__all__ = [
    "BacktestResult",
    "BacktestSpec",
    "WalkForwardWindow",
    "run_backtest",
    "walk_forward_windows",
]
