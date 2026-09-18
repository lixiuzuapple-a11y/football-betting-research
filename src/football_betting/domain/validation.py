"""Small validation helpers shared by the domain models.

The rules encoded here exist for auditability, not for style:

* every timestamp is timezone-aware, so that "when did we know this" has one
  unambiguous answer;
* probabilities live in ``[0, 1]`` and a 1X2 forecast sums to 1.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from .errors import ValidationError

#: Tolerance used when checking that a probability vector sums to one.
PROBABILITY_TOLERANCE = 1e-6


def require_aware(value: datetime, field: str) -> datetime:
    """Return ``value`` if it is timezone-aware, else raise.

    Naive datetimes are rejected everywhere: a naive timestamp cannot be
    compared across data sources and would silently break look-ahead guards.
    """
    if not isinstance(value, datetime):
        raise ValidationError(f"{field} must be a datetime, got {type(value).__name__}")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValidationError(
            f"{field} must be timezone-aware (e.g. datetime(..., tzinfo=timezone.utc)); "
            f"got naive datetime {value.isoformat()}"
        )
    return value


def to_utc(value: datetime, field: str) -> datetime:
    """Validate awareness and normalise to UTC."""
    return require_aware(value, field).astimezone(timezone.utc)


def require_probability(value: float, field: str) -> float:
    """Return ``value`` if it is a probability in ``[0, 1]``, else raise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a number, got {type(value).__name__}")
    value = float(value)
    if value != value:  # NaN
        raise ValidationError(f"{field} must not be NaN")
    if not 0.0 <= value <= 1.0:
        raise ValidationError(f"{field} must be within [0, 1], got {value!r}")
    return value


def require_non_empty_text(value: str, field: str) -> str:
    """Return ``value`` if it is a non-blank string, else raise."""
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValidationError(f"{field} must not be empty")
    return value


def require_positive(value: float, field: str) -> float:
    """Return ``value`` if it is a strictly positive number, else raise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a number, got {type(value).__name__}")
    value = float(value)
    if value != value:
        raise ValidationError(f"{field} must not be NaN")
    if value <= 0.0:
        raise ValidationError(f"{field} must be > 0, got {value!r}")
    return value


def require_probability_vector(values: Iterable[float], fields: Iterable[str]) -> tuple[float, ...]:
    """Validate a complete set of outcome probabilities.

    Each element must be in ``[0, 1]`` and the set must sum to 1 within
    :data:`PROBABILITY_TOLERANCE`.
    """
    checked = tuple(
        require_probability(value, field) for value, field in zip(values, fields, strict=True)
    )
    total = sum(checked)
    if abs(total - 1.0) > PROBABILITY_TOLERANCE:
        label = "/".join(fields)
        raise ValidationError(
            f"{label} probabilities must sum to 1.0 (tolerance {PROBABILITY_TOLERANCE}), "
            f"got {total!r}"
        )
    return checked


def require_enum(value: object, enum_type: type, field: str) -> object:
    """Return ``value`` if it is a member of ``enum_type``, else raise.

    Enum-typed fields are checked rather than merely annotated. Because these
    enums subclass ``str``, a typo such as ``"BUY"`` instead of
    ``Decision.BUY`` would otherwise be stored verbatim and would compare
    unequal to every real member - a silent corruption of the audit trail.
    """
    if not isinstance(value, enum_type):
        raise ValidationError(
            f"{field} must be a {enum_type.__name__} member, got {type(value).__name__} ({value!r})"
        )
    return value
