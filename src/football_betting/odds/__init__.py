"""Odds layer: decimal-odds arithmetic and margin removal.

Responsibility boundary
-----------------------
This layer answers *"what does the market's price imply?"*. It does not decide
anything and does not know what a model thinks. Comparing the two is the
decision layer's job.
"""

from __future__ import annotations

from .implied import (
    MIN_DECIMAL_ODDS,
    devig_from_odds,
    devig_multiplicative,
    expected_value_per_unit,
    fair_decimal_odds,
    implied_probability,
    overround,
    overround_from_odds,
    validate_decimal_odds,
)

__all__ = [
    "MIN_DECIMAL_ODDS",
    "devig_from_odds",
    "devig_multiplicative",
    "expected_value_per_unit",
    "fair_decimal_odds",
    "implied_probability",
    "overround",
    "overround_from_odds",
    "validate_decimal_odds",
]
