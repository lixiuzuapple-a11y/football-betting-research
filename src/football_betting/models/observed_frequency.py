"""Independent 1X2 historical-outcome frequency benchmark (no market input).

This is intentionally a WEAK baseline, not competitive evidence.
Fit from a source-verified prior-results snapshot before new fixture kickoffs.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from ..domain.models import Prediction
from ..domain.errors import ValidationError, FutureInformationError
from .base import PredictionRequest


@dataclass(frozen=True)
class ObservedFrequencyPredictor:
    counts: tuple[int, int, int]
    train_source_sha256: str
    latest_training_match_date: str
    trained_as_of: datetime
    version: str = "observed-frequency-dirichlet-1-v1"

    def __post_init__(self) -> None:
        if len(self.counts) != 3 or any(type(n) is not int or n < 0 for n in self.counts):
            raise ValidationError("counts must contain three nonnegative integer outcomes")
        if sum(self.counts) < 20:
            raise ValidationError("insufficient independent prior labels")
        if len(self.train_source_sha256) != 64:
            raise ValidationError("training source SHA256 required")
        if self.trained_as_of.tzinfo is None or self.trained_as_of.utcoffset() is None:
            raise ValidationError("training source time must be timezone-aware")

    @property
    def probabilities(self) -> tuple[float, float, float]:
        size = sum(self.counts) + 3
        return tuple((value + 1) / size for value in self.counts)

    def predict(self, request: PredictionRequest) -> Prediction:
        if self.trained_as_of > request.as_of:
            raise FutureInformationError("training snapshot became available after prediction as_of")
        if request.as_of >= request.match.kickoff_at or request.created_at >= request.match.kickoff_at:
            raise FutureInformationError("cannot backdate a forecast at or after kickoff")
        if request.created_at < request.as_of:
            raise FutureInformationError("creation before source arrival")
        # Check training match was played before target event; not just before the audit date.
        if self.latest_training_match_date >= request.match.kickoff_at.date().isoformat():
            raise FutureInformationError("training match date overlaps or follows target")
        # No market odds, bookmakers, quote status or implied probabilities are read here.
        payload = json.dumps({
            "match": request.match.match_id,
            "model": self.version, "as_of": request.as_of.isoformat(),
            "training": self.train_source_sha256, "counts": self.counts,
        }, sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        p = self.probabilities
        return Prediction(
            prediction_id=digest,
            match_id=request.match.match_id,
            created_at=request.created_at,
            model_version=self.version,
            data_version=request.data_version,
            as_of=request.as_of,
            probability_home=p[0],
            probability_draw=p[1],
            probability_away=p[2],
            notes="weak independent historical base rate; no market prices used",
        )
