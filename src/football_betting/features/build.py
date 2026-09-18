"""Feature construction and the look-ahead guards.

**Status: partially implemented, honestly.**

What *is* implemented and tested here is the guard layer: the machinery that
decides whether a set of observations may legally enter a pre-match feature
vector. That machinery is the part worth building first, because a feature
builder is easy to write and a leakage bug is nearly impossible to detect after
the fact.

What is *not* implemented is the actual featurisation. There are no features,
because there is no data and no agreed feature contract yet. ``build_features``
raises rather than returning a plausible-looking vector.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any

from ..domain.enums import MatchPhase
from ..domain.errors import (
    FutureInformationError,
    NotAnInputError,
    NotImplementedYetError,
    ValidationError,
)
from ..domain.models import Match, MatchResult, OddsSnapshot
from ..domain.validation import require_aware, require_non_empty_text

#: Object types that may legally be read while building a pre-match vector.
#: Extend this deliberately, one audited source at a time - never by default.
PERMITTED_INPUT_TYPES: tuple[type, ...] = (OddsSnapshot,)


@dataclass(frozen=True, slots=True)
class FeatureSet:
    """A feature vector tied to a match and an information cutoff."""

    match_id: str
    as_of: datetime
    feature_version: str
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        require_non_empty_text(self.match_id, "match_id")
        require_non_empty_text(self.feature_version, "feature_version")
        require_aware(self.as_of, "as_of")
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def __len__(self) -> int:
        return len(self.values)

    def __contains__(self, key: object) -> bool:
        return key in self.values


def is_post_match(obj: Any) -> bool:
    """Whether ``obj`` is defined by a match that has already been played."""
    return getattr(obj, "phase", None) is MatchPhase.POST_MATCH


def validate_observations(
    match: Match,
    as_of: datetime,
    observations: Iterable[Any],
) -> tuple[OddsSnapshot, ...]:
    """Return ``observations`` if every one of them is legally usable.

    Raises
    ------
    FutureInformationError
        If ``as_of`` is not strictly before kickoff, or if any observation
        describes or arrives after ``as_of``.
    NotAnInputError
        If a post-match object (a ``MatchResult``) is passed in. Outcomes are
        labels, never inputs.
    ValidationError
        If an observation does not belong to ``match``, or is of a type the
        feature layer has not been authorised to read.

    The returned tuple is ordered by ``data_time`` so that downstream code
    cannot accidentally depend on input order.
    """
    require_aware(as_of, "as_of")

    if match.phase_at(as_of) is not MatchPhase.PRE_MATCH:
        raise FutureInformationError(
            f"as_of ({as_of.isoformat()}) is not before kickoff "
            f"({match.kickoff_at.isoformat()}): a pre-match feature vector cannot be "
            f"built from a {match.phase_at(as_of).value} state"
        )

    checked: list[OddsSnapshot] = []
    for observation in observations:
        if is_post_match(observation):
            raise NotAnInputError(
                f"{type(observation).__name__} is post-match information and can never be "
                "a model input; it is an evaluation label (docs/project-charter.md 6.1)"
            )
        if isinstance(observation, MatchResult):
            raise NotAnInputError(
                "MatchResult carries a scoreline; it must never enter a pre-match feature set"
            )
        if not isinstance(observation, PERMITTED_INPUT_TYPES):
            raise ValidationError(
                f"observation of type {type(observation).__name__} is not an authorised "
                "input; extend PERMITTED_INPUT_TYPES only after the source is documented "
                "in docs/data-policy.md"
            )
        if observation.match_id != match.match_id:
            raise ValidationError(
                f"observation {observation.snapshot_id!r} belongs to match "
                f"{observation.match_id!r}, not {match.match_id!r}"
            )
        if observation.data_time > as_of:
            raise FutureInformationError(
                f"observation {observation.snapshot_id!r} describes "
                f"{observation.data_time.isoformat()}, later than as_of "
                f"{as_of.isoformat()}"
            )
        if observation.collected_at > as_of:
            raise FutureInformationError(
                f"observation {observation.snapshot_id!r} was not received until "
                f"{observation.collected_at.isoformat()}, later than as_of "
                f"{as_of.isoformat()}"
            )
        if observation.data_time >= match.kickoff_at:
            raise FutureInformationError(
                f"observation {observation.snapshot_id!r} has data_time "
                f"{observation.data_time.isoformat()}, at or after kickoff "
                f"{match.kickoff_at.isoformat()}"
            )
        checked.append(observation)

    return tuple(sorted(checked, key=lambda o: (o.data_time, o.snapshot_id)))


def build_features(
    match: Match,
    as_of: datetime,
    observations: Iterable[Any],
    *,
    feature_version: str = "unversioned",
) -> FeatureSet:
    """Build a pre-match feature vector.

    The guards run first and raise on any violation. Once the input is
    validated there is nothing left to do, because no feature contract has been
    agreed yet, so this raises :class:`NotImplementedYetError`.

    Returning an empty ``FeatureSet`` instead would be worse than failing: an
    empty vector silently trains a model on nothing.
    """
    validate_observations(match, as_of, observations)
    raise NotImplementedYetError(
        "feature construction is not implemented: no feature contract has been "
        f"agreed (requested feature_version={feature_version!r}). The look-ahead "
        "guards are implemented and tested; see validate_observations()."
    )
