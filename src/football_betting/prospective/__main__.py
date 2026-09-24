"""Command-line entry point for the TASK-0005 prospective collector.

Usage::

    python -m football_betting.prospective --data-root /home/ubuntu/evlab-data/task0005

The module is intentionally thin: it parses arguments, builds a
:class:`CollectorConfig`, and hands control to the collector loop. All the
interesting behaviour lives in :mod:`football_betting.prospective.collector`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .collector import CollectorConfig, run_forever


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
    parser = argparse.ArgumentParser(description="TASK-0005 prospective collector")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CollectorConfig(
        data_root=args.data_root,
        deployed_commit=args.deployed_commit or _default_commit(),
        round_interval_seconds=args.round_interval,
        http_timeout_seconds=args.http_timeout,
        max_rounds=args.max_rounds,
    )
    run_forever(config)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a module
    raise SystemExit(main())
