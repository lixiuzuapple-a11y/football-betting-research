"""Record layer: persist forecasts, recommendations, outcomes and experiments.

Responsibility boundary
-----------------------
This layer answers *"what did we record, and when?"*. It stores and reconstructs;
it does not predict, does not decide, and does not evaluate.

Both stores are append-only. ``state_as_of`` reconstructs the world as it was at
a past instant, which is the mechanism that keeps backtests honest.
"""

from __future__ import annotations

from .experiments import ExperimentRegistry, new_experiment_id
from .store import KnownState, RecordStore

__all__ = [
    "ExperimentRegistry",
    "KnownState",
    "RecordStore",
    "new_experiment_id",
]
