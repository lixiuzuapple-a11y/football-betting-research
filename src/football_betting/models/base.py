"""Prediction interface.

This module defines the *shape* of a predictor and nothing else. There is no
model here, working or pretended. See ``baseline.py`` for the stub that stands
in for one until a real model is built.

Why an interface with no implementation: the project's failure mode is not
"no model", it is "a model that looks like it works". A named, typed seam makes
the absence explicit and keeps the eventual model replaceable without touching
the layers around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from ..domain.errors import FutureInformationError
from ..domain.models import Match, Prediction
from ..domain.validation import require_aware
from ..features.build import FeatureSet


@dataclass(frozen=True, slots=True)
class PredictionRequest:
    """Everything a predictor is allowed to see, and nothing more.

    A predictor receives scheduled fixtures and pre-match features. It does not
    receive a ``DataSnapshot``, a store handle, or a result table: if it cannot
    reach post-match data, it cannot leak it.
    """

    match: Match
    features: FeatureSet
    as_of: datetime
    created_at: datetime
    data_version: str

    def __post_init__(self) -> None:
        require_aware(self.as_of, "as_of")
        require_aware(self.created_at, "created_at")
        if self.features.match_id != self.match.match_id:
            raise FutureInformationError(
                f"features belong to match {self.features.match_id!r}, not {self.match.match_id!r}"
            )
        if self.features.as_of > self.as_of:
            raise FutureInformationError(
                f"features were built at as_of {self.features.as_of.isoformat()}, which is "
                f"later than the requested as_of {self.as_of.isoformat()}"
            )


@runtime_checkable
class Predictor(Protocol):
    """A 1X2 forecaster.

    Implementations must be pure with respect to time: given the same request
    they return the same probabilities, and they read nothing that was not
    handed to them in the request.
    """

    #: Identifies the model, its version and its configuration. Stored on every
    #: prediction it produces so results stay attributable.
    version: str

    def predict(self, request: PredictionRequest) -> Prediction:
        """Return a 1X2 forecast for ``request.match``."""
        ...
