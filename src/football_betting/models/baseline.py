"""Placeholder predictors.

**Status: not implemented - deliberately.**

The generic application registry still has no configured production predictor.
The separately audited observed-frequency research baseline lives in
``observed_frequency.py`` and must be created from a prior official result
snapshot; this placeholder intentionally stays unimplemented.

Rules for this file:

* It contains no coefficients, no heuristics and no "reasonable defaults".
* It never returns a ``Prediction``. It raises.
* It must not be extended into a real model by copy-paste-and-tweak. A real
  model arrives as its own module, with its own hypothesis, its own experiment
  record and its own documented validation.

A uniform ``0.40 / 0.28 / 0.32`` forecast would be trivial to write and would
make the pipeline appear to run end to end. It would also be indistinguishable
from a real model in every downstream report, which is exactly why it is not
here.
"""

from __future__ import annotations

from ..domain.errors import NotImplementedYetError
from .base import PredictionRequest, Predictor


class UnimplementedPredictor:
    """A predictor-shaped placeholder that refuses to predict."""

    version = "unimplemented-0.0.0"

    def predict(self, request: PredictionRequest) -> None:
        """Always raises :class:`NotImplementedYetError`."""
        raise NotImplementedYetError(
            "no configured application predictor is registered (requested "
            f"match={request.match.match_id!r}, model_version={self.version!r}). "
            "Stage 1 builds infrastructure only; see docs/project-charter.md."
        )


def available_predictors() -> dict[str, Predictor]:
    """Registered predictors, keyed by ``version``.

    Empty: nothing is registered, and the placeholder above is not a model.
    """
    return {}
