"""Decimal-odds arithmetic and margin removal.

This module is pure arithmetic on numbers the caller supplies. It holds no
opinion about what to bet and imports nothing from the decision layer: odds in,
probabilities out.

Conventions
-----------
* Decimal (European) odds throughout. A quote of ``2.50`` returns ``2.50`` per
  unit staked, stake included.
* "Implied probability" is the raw, margin-inclusive ``1 / odds``. It is not a
  fair probability and is never presented as one.
* A set of implied probabilities from one book sums to more than 1. The excess
  is the ``overround``, also called the book's margin.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeVar

from ..domain.errors import ValidationError
from ..domain.validation import require_probability

_K = TypeVar("_K")

#: Smallest decimal odds that can be quoted. ``1.0`` is a stake returned with
#: no profit and is treated as invalid rather than as a zero-edge price.
MIN_DECIMAL_ODDS = 1.0


def validate_decimal_odds(decimal_odds: float) -> float:
    """Return ``decimal_odds`` if it is a usable quote, else raise."""
    if isinstance(decimal_odds, bool) or not isinstance(decimal_odds, (int, float)):
        raise ValidationError(f"decimal odds must be a number, got {type(decimal_odds).__name__}")
    decimal_odds = float(decimal_odds)
    if decimal_odds != decimal_odds:
        raise ValidationError("decimal odds must not be NaN")
    if decimal_odds <= MIN_DECIMAL_ODDS:
        raise ValidationError(f"decimal odds must be > {MIN_DECIMAL_ODDS}, got {decimal_odds!r}")
    return decimal_odds


def implied_probability(decimal_odds: float) -> float:
    """Raw implied probability ``1 / decimal_odds`` (margin still included)."""
    return 1.0 / validate_decimal_odds(decimal_odds)


def fair_decimal_odds(probability: float) -> float:
    """Odds that would make a bet with this probability exactly break even."""
    probability = require_probability(probability, "probability")
    if probability == 0.0:
        raise ValidationError("a zero-probability outcome has no finite fair odds")
    return 1.0 / probability


def overround(probabilities: Sequence[float]) -> float:
    """Sum of ``probabilities`` minus 1.

    Positive means the book has a margin; zero means a fair book; negative
    means an arbitrage exists (and almost certainly means bad data).
    """
    if not probabilities:
        raise ValidationError("overround needs at least one probability")
    checked = [require_probability(p, "probability") for p in probabilities]
    return sum(checked) - 1.0


def overround_from_odds(decimal_odds: Sequence[float]) -> float:
    """Book margin implied by a complete set of quotes."""
    return overround([implied_probability(o) for o in decimal_odds])


def devig_multiplicative(probabilities: Sequence[float]) -> tuple[float, ...]:
    """Remove the margin by proportional normalisation.

    Also known as the multiplicative or basic method: each raw probability is
    divided by the total. It assumes the book's margin is spread evenly across
    outcomes, which is an assumption worth stating out loud, not a fact.

    Raises if the probabilities cannot be normalised.
    """
    if not probabilities:
        raise ValidationError("devig needs at least one probability")
    checked = [require_probability(p, "probability") for p in probabilities]
    total = sum(checked)
    if total <= 0.0:
        raise ValidationError("cannot remove margin from an all-zero probability vector")
    return tuple(p / total for p in checked)


def devig_from_odds(decimal_odds: Mapping[_K, float]) -> dict[_K, float]:
    """Margin-free probabilities for a complete market quoted as decimal odds.

    Keys are preserved, so a mapping keyed by selection comes back keyed the
    same way.
    """
    if not decimal_odds:
        raise ValidationError("devig needs at least one quote")
    keys = list(decimal_odds)
    raw = [implied_probability(decimal_odds[k]) for k in keys]
    normalised = devig_multiplicative(raw)
    return dict(zip(keys, normalised, strict=True))


def expected_value_per_unit(model_probability: float, decimal_odds: float) -> float:
    """Expected profit per unit staked under the model's own probability.

    ``p * odds - 1``. Positive means the model believes the price is generous.
    This is an estimate conditional on the model being right, not a promise.
    """
    model_probability = require_probability(model_probability, "model_probability")
    return model_probability * validate_decimal_odds(decimal_odds) - 1.0
