"""Feature layer: turn permitted observations into pre-match feature vectors.

Responsibility boundary
-----------------------
This layer answers *"what was knowable about this fixture before kickoff?"*.
It does not fetch data, does not predict, and does not touch outcomes.

The look-ahead guards in ``validate_observations`` are the load-bearing part of
this layer and are fully implemented. Featurisation itself is not implemented.
"""

from __future__ import annotations

from .build import (
    PERMITTED_INPUT_TYPES,
    FeatureSet,
    build_features,
    is_post_match,
    validate_observations,
)

__all__ = [
    "PERMITTED_INPUT_TYPES",
    "FeatureSet",
    "build_features",
    "is_post_match",
    "validate_observations",
]
