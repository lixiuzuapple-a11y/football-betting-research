"""Unattended prospective collector (TASK-0005).

This package is engineering scaffolding for continuous, provenance-stamped
observation of the Sporttery official feed alongside the BetExplorer
``reference_proxy``. It writes only to an append-only ledger outside the Git
working tree and produces no research conclusion, EV, model or recommendation.

Modules
-------
``ledger``
    Append-only SQLite store plus content-addressed gzip raw captures.
``collector``
    The dual-leg loop: 60-second cadence, concurrent legs, change detection and
    immediate Sporttery confirmation captures.
"""

from __future__ import annotations

from .collector import CollectorConfig, ProspectiveCollector, run_forever

__all__ = ["CollectorConfig", "ProspectiveCollector", "run_forever"]
