"""Data layer: acquisition, standardisation and validation.

Responsibility boundary
-----------------------
This layer answers *"what rows do we have, and where did they come from?"*.
It does **not** build features, does not model, and does not evaluate.

Public surface
--------------
``DataProvenance``
    Traceability header: source, collection time, data time, version, schema.
``DataSnapshot``
    Immutable dataset plus provenance, with ``knowable_at`` time filtering.
``load_snapshot``
    Acquisition entry point. Currently a documented stub.
"""

from __future__ import annotations

from .loader import available_sources, load_snapshot
from .provenance import DataProvenance, DataSnapshot

__all__ = [
    "DataProvenance",
    "DataSnapshot",
    "available_sources",
    "load_snapshot",
]
