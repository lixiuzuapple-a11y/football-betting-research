"""Dataset acquisition.

**Status: not implemented.** No data source is configured. This module
deliberately contains no fixture data, no sample rows and no downloader: stage 1
of the project builds the container, not the contents.

A loader is only added together with a concrete, licensed, traceable source and
a documented schema. See ``docs/data-policy.md`` for the bar a source must clear
before it may be wired in here.
"""

from __future__ import annotations

from datetime import datetime

from ..domain.errors import NotImplementedYetError
from .provenance import DataSnapshot


def available_sources() -> tuple[str, ...]:
    """Identifiers of configured data sources.

    Returns an empty tuple: nothing is wired up yet. Callers should treat an
    empty result as "the system has no data" rather than falling back to
    generated or placeholder rows.
    """
    return ()


def load_snapshot(
    source: str,
    version: str,
    *,
    collected_at: datetime | None = None,
) -> DataSnapshot:
    """Load one immutable snapshot from ``source``.

    Raises
    ------
    NotImplementedYetError
        Always, at present. Kept as an explicit, machine-detectable signal so
        that no caller can mistake a stub for a working loader.
    """
    raise NotImplementedYetError(
        "data acquisition is not implemented in stage 1 "
        f"(requested source={source!r}, version={version!r}, collected_at={collected_at!r}). "
        "Configure a traceable source and schema first; see docs/data-policy.md."
    )
