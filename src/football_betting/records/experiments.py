"""Experiment registry.

The charter requires that every formal experiment carry an id, a hypothesis, the
data version, the model version, its parameters, its result and its status - and
that failures are retained.

That last requirement is why this class has no ``delete`` method and no
``update_in_place`` method. An experiment is registered once and then moves
forward through its lifecycle. ``FAILED`` is a terminal state that stays in the
listing forever.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from ..domain.enums import ExperimentStatus
from ..domain.errors import DuplicateRecordError, UnknownReferenceError, ValidationError
from ..domain.models import Experiment
from ..domain.validation import require_aware, require_non_empty_text


def new_experiment_id() -> str:
    """A fresh experiment identifier."""
    return "exp_" + uuid.uuid4().hex[:12]


class ExperimentRegistry:
    """Append-mostly registry of research experiments.

    Status may only move forward: ``PLANNED -> RUNNING -> COMPLETED | FAILED |
    ABANDONED``. Once an experiment has a result it is frozen, so that a result
    cannot be adjusted after the fact.
    """

    #: Statuses that end an experiment's life.
    TERMINAL_STATUSES: frozenset[ExperimentStatus] = frozenset(
        {ExperimentStatus.COMPLETED, ExperimentStatus.FAILED, ExperimentStatus.ABANDONED}
    )

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}

    def register(
        self,
        *,
        hypothesis: str,
        data_version: str,
        model_version: str,
        created_at: datetime,
        parameters: Mapping[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> Experiment:
        """Pre-register an experiment before it is run.

        Registering first, then running, is the difference between a test and a
        story told afterwards about a number that was already on screen.
        """
        experiment_id = experiment_id or new_experiment_id()
        require_non_empty_text(experiment_id, "experiment_id")
        if experiment_id in self._experiments:
            raise DuplicateRecordError(f"experiment {experiment_id!r} is already registered")
        experiment = Experiment(
            experiment_id=experiment_id,
            hypothesis=hypothesis,
            data_version=data_version,
            model_version=model_version,
            created_at=created_at,
            status=ExperimentStatus.PLANNED,
            parameters=parameters or {},
        )
        self._experiments[experiment_id] = experiment
        return experiment

    def start(self, experiment_id: str, *, at: datetime) -> Experiment:
        """Mark a pre-registered experiment as running."""
        experiment = self._require_planned(experiment_id)
        return self._replace(
            experiment_id,
            experiment.with_result(result={}, status=ExperimentStatus.RUNNING, updated_at=at),
        )

    def complete(
        self,
        experiment_id: str,
        *,
        result: Mapping[str, Any],
        at: datetime,
    ) -> Experiment:
        """Attach a result and mark the experiment completed."""
        return self._resolve(experiment_id, result, ExperimentStatus.COMPLETED, at)

    def fail(
        self,
        experiment_id: str,
        *,
        result: Mapping[str, Any],
        at: datetime,
    ) -> Experiment:
        """Attach a failure and mark the experiment failed.

        The record is kept. There is no path from here to deletion.
        """
        return self._resolve(experiment_id, result, ExperimentStatus.FAILED, at)

    def abandon(self, experiment_id: str, *, at: datetime) -> Experiment:
        """Mark an experiment abandoned without a result."""
        return self._resolve(
            experiment_id,
            {"reason": "abandoned without a result"},
            ExperimentStatus.ABANDONED,
            at,
        )

    def get(self, experiment_id: str) -> Experiment:
        """Return one experiment, or raise."""
        try:
            return self._experiments[experiment_id]
        except KeyError as exc:
            raise UnknownReferenceError(f"unknown experiment {experiment_id!r}") from exc

    def all(self) -> tuple[Experiment, ...]:
        """Every registered experiment, including failed ones."""
        return tuple(self._experiments.values())

    def counts_by_status(self) -> dict[str, int]:
        """Experiment counts keyed by status value."""
        counts: dict[str, int] = {status.value: 0 for status in ExperimentStatus}
        for experiment in self._experiments.values():
            counts[experiment.status.value] += 1
        return counts

    # -- internals ---------------------------------------------------------

    def _require_planned(self, experiment_id: str) -> Experiment:
        experiment = self.get(experiment_id)
        if experiment.status in self.TERMINAL_STATUSES:
            raise ValidationError(
                f"experiment {experiment_id!r} is already {experiment.status.value} and "
                "cannot be restarted; register a new experiment instead"
            )
        if experiment.status is ExperimentStatus.RUNNING:
            raise ValidationError(f"experiment {experiment_id!r} is already running")
        return experiment

    def _resolve(
        self,
        experiment_id: str,
        result: Mapping[str, Any],
        status: ExperimentStatus,
        at: datetime,
    ) -> Experiment:
        experiment = self.get(experiment_id)
        if experiment.status in self.TERMINAL_STATUSES:
            raise ValidationError(
                f"experiment {experiment_id!r} is already {experiment.status.value}; "
                "results are frozen once recorded"
            )
        require_aware(at, "at")
        if at < experiment.created_at:
            raise ValidationError("a result cannot be recorded before the experiment was created")
        return self._replace(
            experiment_id,
            experiment.with_result(result=result, status=status, updated_at=at),
        )

    def _replace(self, experiment_id: str, experiment: Experiment) -> Experiment:
        self._experiments[experiment_id] = experiment
        return experiment
