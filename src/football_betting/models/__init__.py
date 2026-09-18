"""Model layer: prediction only.

Responsibility boundary
-----------------------
This layer answers *"what does the model think will happen?"*. It does not read
market prices, does not decide whether a bet is worth taking, and does not see
outcomes.

**Status: no model implemented.** ``available_predictors()`` is empty.
"""

from __future__ import annotations

from .base import PredictionRequest, Predictor
from .baseline import UnimplementedPredictor, available_predictors

__all__ = [
    "PredictionRequest",
    "Predictor",
    "UnimplementedPredictor",
    "available_predictors",
]
