"""Immutable sealed-run manifest for TASK-0006.

TASK-0006 §5.2 requires one immutable record, written *before* the first formal
capture, that answers "what exactly ran, from where, for how long, and was the
analysis sealed". It is deliberately plain JSON with no secrets: the single
artefact a reviewer can read to reconstruct the run's contract without trusting
either the collector's chat log or the report.

Two rules are enforced in code rather than by convention:

* the manifest is written **once** - a second write is refused, so the contract
  cannot be quietly replaced mid-run;
* it cannot be written into a root that already holds captures, so a sealed
  contract can never be retro-fitted to data that existed before it.

The planned end is derived from the planned start plus the frozen 120-hour
duration, and is stored as an absolute UTC instant. That is what lets a restarted
process stop at the same wall-clock deadline instead of restarting the clock
(TASK-0006 §5.3).
"""

from __future__ import annotations

import hashlib
import json
import socket
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

__all__ = [
    "RUN_MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_VERSION",
    "SEALED_DURATION_HOURS",
    "ANALYSIS_SEALED_STATEMENT",
    "ManifestError",
    "RunManifest",
    "build_manifest",
    "manifest_sha256",
    "read_manifest",
    "write_manifest",
]

RUN_MANIFEST_FILENAME = "RUN_MANIFEST.json"
MANIFEST_SCHEMA_VERSION = "task0006-manifest/1"

#: The sealed study duration, fixed by TASK-0006 §1. Not a tunable.
SEALED_DURATION_HOURS = 120.0

#: Carried verbatim into the manifest so the sealing intent travels with the data.
ANALYSIS_SEALED_STATEMENT = (
    "This dataset is sealed. No odds, change counts, confirmation counts or "
    "D01-B candidates may be inspected for research purposes until the 120-hour "
    "run has completed and the Reviewer explicitly authorises an analysis task."
)


class ManifestError(RuntimeError):
    """Raised when a manifest would be overwritten or written into a live root."""


@dataclass(frozen=True, slots=True)
class RunManifest:
    """The immutable contract of one sealed run (TASK-0006 §5.2)."""

    task_id: str
    run_id: str
    dataset_phase: str
    frozen_commit: str
    collector_version: str
    parser_version: str
    data_root: str
    hostname: str
    planned_start_utc: str
    planned_end_utc: str
    duration_hours: float
    sporttery_endpoint: str
    betexplorer_endpoint: str
    reference_label: str
    cadence_seconds: float
    http_timeout_seconds: float
    schema_version: str
    schema_hash: str
    service_unit: str
    manifest_schema_version: str
    analysis_sealed_statement: str
    created_at_utc: str


def build_manifest(
    *,
    task_id: str,
    run_id: str,
    dataset_phase: str,
    frozen_commit: str,
    collector_version: str,
    parser_version: str,
    data_root: str,
    planned_start_utc: datetime,
    sporttery_endpoint: str,
    betexplorer_endpoint: str,
    reference_label: str,
    cadence_seconds: float,
    http_timeout_seconds: float,
    schema_version: str,
    schema_hash: str,
    service_unit: str,
    hostname: str | None = None,
    now: datetime | None = None,
) -> RunManifest:
    """Assemble a manifest, deriving ``planned_end_utc = start + 120h``."""
    if planned_start_utc.tzinfo is None:
        raise ValueError("planned_start_utc must be timezone-aware")
    start = planned_start_utc.astimezone(timezone.utc)
    end = start + timedelta(hours=SEALED_DURATION_HOURS)
    created = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return RunManifest(
        task_id=task_id,
        run_id=run_id,
        dataset_phase=dataset_phase,
        frozen_commit=frozen_commit,
        collector_version=collector_version,
        parser_version=parser_version,
        data_root=data_root,
        hostname=hostname or socket.gethostname(),
        planned_start_utc=start.isoformat(),
        planned_end_utc=end.isoformat(),
        duration_hours=SEALED_DURATION_HOURS,
        sporttery_endpoint=sporttery_endpoint,
        betexplorer_endpoint=betexplorer_endpoint,
        reference_label=reference_label,
        cadence_seconds=cadence_seconds,
        http_timeout_seconds=http_timeout_seconds,
        schema_version=schema_version,
        schema_hash=schema_hash,
        service_unit=service_unit,
        manifest_schema_version=MANIFEST_SCHEMA_VERSION,
        analysis_sealed_statement=ANALYSIS_SEALED_STATEMENT,
        created_at_utc=created.isoformat(),
    )


def _capture_row_count(db_path: Path) -> int:
    """Read the capture count from an existing ledger without modifying it."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return 0
    try:
        row = conn.execute("SELECT COUNT(*) FROM captures").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def write_manifest(data_root: str | Path, manifest: RunManifest) -> tuple[Path, str]:
    """Write the manifest exactly once; return ``(path, sha256)``.

    Refuses a second write and refuses a root that already holds captures
    (TASK-0006 §5.2 / §6): the sealed contract must precede the sealed data.
    """
    root = Path(data_root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / RUN_MANIFEST_FILENAME
    if target.exists():
        raise ManifestError(
            f"{target} already exists; the sealed run manifest is immutable and "
            f"must not be replaced"
        )
    ledger = root / "ledger.sqlite3"
    if ledger.exists() and _capture_row_count(ledger) > 0:
        raise ManifestError(
            f"{ledger} already contains captures; a sealed manifest must be "
            f"written before the first formal capture"
        )
    payload = json.dumps(asdict(manifest), indent=2, sort_keys=True, ensure_ascii=False)
    target.write_text(payload + "\n", encoding="utf-8")
    return target, manifest_sha256(target)


def read_manifest(data_root: str | Path) -> dict:
    """Load a manifest as a plain mapping."""
    target = Path(data_root) / RUN_MANIFEST_FILENAME
    if not target.is_file():
        raise ManifestError(f"{target} does not exist")
    return json.loads(target.read_text(encoding="utf-8"))


def manifest_sha256(path: str | Path) -> str:
    """SHA-256 of the manifest file on disk."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
