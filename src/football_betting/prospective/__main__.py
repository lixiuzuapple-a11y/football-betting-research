"""Command-line entry point for the prospective collector.

Usage::

    python -m football_betting.prospective --data-root /home/ubuntu/evlab-data/task0005

The module is intentionally thin: it parses arguments, builds a
:class:`CollectorConfig`, and hands control to the collector loop. All the
interesting behaviour lives in :mod:`football_betting.prospective.collector`.

TASK-0006 adds a sealed mode. Exactly two extra steps happen before the loop
starts, and nothing else about the accepted TASK-0005 behaviour changes:

1. the immutable run manifest is read - or, once, written - so the 120-hour
   deadline is a wall-clock instant rather than a process uptime counter
   (§5.2/§5.3);
2. the dataset phase is passed through explicitly so every formal row is stamped
   ``PROSPECTIVE_SEALED`` (§5.1).
"""

from __future__ import annotations

import argparse
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from football_betting.data.betexplorer import REFERENCE_PROXY_LABEL

from .collector import COLLECTOR_VERSION, CollectorConfig, run_forever
from .ledger import (
    DATASET_PHASE,
    PHASE_PROSPECTIVE_SEALED,
    SCHEMA_VERSION,
    VALID_DATASET_PHASES,
    schema_hash,
)
from .manifest import (
    RUN_MANIFEST_FILENAME,
    build_manifest,
    manifest_sha256,
    read_manifest,
    write_manifest,
)


def _default_commit() -> str:
    """Resolve the deployed commit without shelling out to git.

    TASK-0005 §8 requires the service to record the exact commit it runs. The
    deployment writes it into the environment or a sibling file; falling back to
    ``unknown`` is honest rather than inventing a hash.
    """
    from_env = os.environ.get("EVLAB_DEPLOYED_COMMIT")
    if from_env:
        return from_env.strip()
    # __file__ = <root>/src/football_betting/prospective/__main__.py
    marker = Path(__file__).resolve().parents[3] / ".deployed_commit"
    if marker.is_file():
        return marker.read_text(encoding="utf-8").strip() or "unknown"
    return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="prospective dual-market collector")
    parser.add_argument(
        "--data-root",
        required=True,
        help="runtime data root; must live outside the Git working tree",
    )
    parser.add_argument("--round-interval", type=float, default=60.0)
    parser.add_argument("--http-timeout", type=float, default=50.0)
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="stop after N rounds (used by the qualification soak harness)",
    )
    parser.add_argument("--deployed-commit", default=None)
    parser.add_argument(
        "--dataset-phase",
        default=DATASET_PHASE,
        choices=sorted(VALID_DATASET_PHASES),
        help="dataset phase stamped on every row (TASK-0006: PROSPECTIVE_SEALED)",
    )
    parser.add_argument("--run-id", default=None, help="sealed run identifier")
    parser.add_argument("--task-id", default="TASK-0006")
    parser.add_argument("--service-unit", default="evlab-task0006.service")
    parser.add_argument(
        "--planned-start-utc",
        default=None,
        help="ISO-8601 instant with an offset; defaults to now (UTC)",
    )
    parser.add_argument(
        "--write-manifest-only",
        action="store_true",
        help="create the sealed run manifest and exit without collecting",
    )
    return parser


def _resolve_sealed_deadline(args: argparse.Namespace, config: CollectorConfig) -> datetime:
    """Read the sealed deadline from the manifest, or create the manifest once.

    Fails closed: sealed mode never starts on a root without a manifest, because
    that would mean collecting formal data whose end time nobody had fixed.
    """
    root = Path(config.data_root)
    manifest_path = root / RUN_MANIFEST_FILENAME

    if manifest_path.is_file():
        data = read_manifest(root)
        end = data.get("planned_end_utc")
        if not end:
            raise SystemExit(f"{manifest_path} is missing planned_end_utc")
        if args.write_manifest_only:
            # Say so explicitly: a silent no-op here would let an operator
            # believe a fresh contract had been written when the original is
            # still in force (§5.2 immutability).
            print(f"run manifest already exists and was NOT rewritten: {manifest_path}")
            print(f"run manifest sha256: {manifest_sha256(manifest_path)}")
            print(f"run_id: {data.get('run_id')}")
            print(f"planned_start_utc: {data.get('planned_start_utc')}")
            print(f"planned_end_utc: {data.get('planned_end_utc')}")
        return datetime.fromisoformat(end)

    if not args.write_manifest_only:
        raise SystemExit(
            f"sealed mode requires {manifest_path}; create it first with "
            f"--write-manifest-only --run-id <RUN_ID>"
        )
    if not args.run_id:
        raise SystemExit("--run-id is required to create a sealed run manifest")

    if args.planned_start_utc:
        start = datetime.fromisoformat(args.planned_start_utc)
        if start.tzinfo is None:
            raise SystemExit("--planned-start-utc must include a timezone offset")
    else:
        start = datetime.now(timezone.utc)

    manifest = build_manifest(
        task_id=args.task_id,
        run_id=args.run_id,
        dataset_phase=config.dataset_phase,
        frozen_commit=config.deployed_commit,
        collector_version=COLLECTOR_VERSION,
        parser_version=config.parser_version,
        data_root=str(root),
        planned_start_utc=start,
        sporttery_endpoint=config.sporttery_url,
        betexplorer_endpoint=config.betexplorer_url,
        reference_label=REFERENCE_PROXY_LABEL,
        cadence_seconds=config.round_interval_seconds,
        http_timeout_seconds=config.http_timeout_seconds,
        schema_version=SCHEMA_VERSION,
        schema_hash=schema_hash(),
        service_unit=args.service_unit,
    )
    path, digest = write_manifest(root, manifest)
    print(f"run manifest written: {path}")
    print(f"run manifest sha256: {digest}")
    print(f"run_id: {manifest.run_id}")
    print(f"dataset_phase: {manifest.dataset_phase}")
    print(f"frozen_commit: {manifest.frozen_commit}")
    print(f"planned_start_utc: {manifest.planned_start_utc}")
    print(f"planned_end_utc: {manifest.planned_end_utc}")
    return datetime.fromisoformat(manifest.planned_end_utc)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CollectorConfig(
        data_root=args.data_root,
        deployed_commit=args.deployed_commit or _default_commit(),
        round_interval_seconds=args.round_interval,
        http_timeout_seconds=args.http_timeout,
        max_rounds=args.max_rounds,
        dataset_phase=args.dataset_phase,
    )

    if config.dataset_phase == PHASE_PROSPECTIVE_SEALED:
        deadline = _resolve_sealed_deadline(args, config)
        config = replace(config, planned_end_utc=deadline)
        if args.write_manifest_only:
            print("sealed manifest is ready; not starting the collector")
            return 0

    run_forever(config)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a module
    raise SystemExit(main())
