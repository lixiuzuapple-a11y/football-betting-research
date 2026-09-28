#!/usr/bin/env python3
"""Operational health check for a sealed TASK-0006 run (TASK-0006 §11/§12).

Prints only the fields the task permits. There is no code path here that reads
or prints odds, reference-change counts, confirmation counts, variant price
differences or stale-window candidates: an operator watching a sealed run must
not be able to read a result out of the monitoring channel.

Two deliberate omissions look like oversights and are not:

* ``reference_changes`` and ``variant_transitions`` are never counted - a change
  count *is* a result, and a confirmation count is only a proxy for one;
* captures are never broken down by ``capture_kind``, because
  ``total - regular = confirmations`` would leak the same signal.

Usage::

    python deploy/task0006_health.py \
        --data-root /home/ubuntu/evlab-data/task0006-sealed-<RUN_ID>
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = "RUN_MANIFEST.json"
LEDGER_NAME = "ledger.sqlite3"


def _read_manifest(data_root: Path) -> dict:
    path = data_root / MANIFEST_NAME
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _cadence_seconds(conn: sqlite3.Connection) -> tuple[int, float | None]:
    """Round count and median start-to-start spacing - an operations fact.

    Derived from ``response_received_at`` grouped by ``round_id``, so it says
    nothing about what was in the payloads, only when they arrived.
    """
    rows = conn.execute(
        "SELECT MIN(response_received_at) AS started FROM captures "
        "GROUP BY round_id ORDER BY started"
    ).fetchall()
    stamps = [datetime.fromisoformat(row["started"]) for row in rows if row["started"]]
    if len(stamps) < 2:
        return len(stamps), None
    gaps = sorted((stamps[i] - stamps[i - 1]).total_seconds() for i in range(1, len(stamps)))
    middle = len(gaps) // 2
    median = gaps[middle] if len(gaps) % 2 else (gaps[middle - 1] + gaps[middle]) / 2.0
    return len(stamps), median


def ledger_health(db_path: Path) -> dict:
    """Permitted ledger statistics only (TASK-0006 §11)."""
    if not db_path.is_file():
        return {"present": False}
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        total = conn.execute("SELECT COUNT(*) AS n FROM captures").fetchone()["n"]
        bounds = conn.execute(
            "SELECT MIN(response_received_at) AS first, "
            "MAX(response_received_at) AS last FROM captures"
        ).fetchone()
        by_source = conn.execute(
            "SELECT source AS s, "
            "SUM(CASE WHEN failure_class IS NULL THEN 1 ELSE 0 END) AS ok, "
            "SUM(CASE WHEN failure_class IS NULL THEN 0 ELSE 1 END) AS bad "
            "FROM captures GROUP BY source ORDER BY source"
        ).fetchall()
        failures = conn.execute(
            "SELECT COALESCE(failure_class, 'none') AS f, COUNT(*) AS n "
            "FROM captures GROUP BY f ORDER BY n DESC"
        ).fetchall()
        phases = conn.execute(
            "SELECT COALESCE(dataset_phase, 'none') AS p, COUNT(*) AS n "
            "FROM captures GROUP BY p ORDER BY p"
        ).fetchall()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        rounds, cadence = _cadence_seconds(conn)
    finally:
        conn.close()
    return {
        "present": True,
        "total_captures": int(total),
        "first_capture_utc": bounds["first"],
        "last_capture_utc": bounds["last"],
        "by_source": [
            {"source": row["s"], "success": int(row["ok"]), "failure": int(row["bad"])}
            for row in by_source
        ],
        "failure_classes": {row["f"]: int(row["n"]) for row in failures},
        "phases": {row["p"]: int(row["n"]) for row in phases},
        "round_count": rounds,
        "cadence_median_seconds": cadence,
        "sqlite_integrity": integrity,
    }


def service_state(unit: str) -> str:
    """``systemctl is-active`` for the formal unit, or why it is unavailable."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return result.stdout.strip() or "unknown"


def worktree_state(repo_dir: Path) -> str:
    """Whether the deployed checkout is clean - a provenance check, not a metric."""
    if not (repo_dir / ".git").exists():
        return "not-a-git-worktree"
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "status", "--porcelain"],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return "clean" if not result.stdout.strip() else "dirty"


def raw_file_stats(raw_root: Path) -> dict:
    files = list(raw_root.rglob("*.gz")) if raw_root.is_dir() else []
    return {"count": len(files), "bytes": sum(path.stat().st_size for path in files)}


def _fmt_bytes(value: int | None) -> str:
    if value is None:
        return "-"
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TiB"


def build_report(data_root: Path, *, unit: str, repo: Path, now: datetime) -> str:
    """Render the permitted health view as plain text."""
    manifest = _read_manifest(data_root)
    health = ledger_health(data_root / LEDGER_NAME)
    raw = raw_file_stats(data_root / "raw")
    disk = shutil.disk_usage(data_root if data_root.exists() else Path("/"))

    lines = [
        "TASK-0006 sealed run — operational health (no market content)",
        f"  now_utc              : {now.astimezone(timezone.utc).isoformat()}",
        f"  service_unit         : {unit}",
        f"  service_state        : {service_state(unit)}",
        f"  data_root            : {data_root}",
        f"  run_id               : {manifest.get('run_id', '-')}",
        f"  dataset_phase        : {manifest.get('dataset_phase', '-')}",
        f"  frozen_commit        : {manifest.get('frozen_commit', '-')}",
        f"  planned_start_utc    : {manifest.get('planned_start_utc', '-')}",
        f"  planned_end_utc      : {manifest.get('planned_end_utc', '-')}",
    ]

    end_raw = manifest.get("planned_end_utc")
    if end_raw:
        remaining = (datetime.fromisoformat(end_raw) - now.astimezone(timezone.utc))
        lines.append(f"  remaining            : {remaining.total_seconds() / 3600.0:.2f} h")

    lines.append(f"  worktree             : {worktree_state(repo)}")

    if not health.get("present"):
        lines.append("  ledger               : not present")
    else:
        lines += [
            f"  total_captures       : {health['total_captures']}",
            f"  first_capture_utc    : {health['first_capture_utc']}",
            f"  last_capture_utc     : {health['last_capture_utc']}",
            f"  round_count          : {health['round_count']}",
            f"  cadence_median_s     : {health['cadence_median_seconds']}",
            f"  phases               : {health['phases']}",
            f"  failure_classes      : {health['failure_classes']}",
            f"  sqlite_integrity     : {health['sqlite_integrity']}",
        ]
        for entry in health["by_source"]:
            lines.append(
                f"  source[{entry['source']}] : "
                f"success={entry['success']} failure={entry['failure']}"
            )

    lines += [
        f"  raw_files            : {raw['count']} ({_fmt_bytes(raw['bytes'])})",
        f"  disk_free            : {_fmt_bytes(disk.free)} of {_fmt_bytes(disk.total)}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TASK-0006 sealed run health check")
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--unit", default="evlab-task0006.service")
    parser.add_argument("--repo", default="/home/ubuntu/football-betting-research")
    parser.add_argument(
        "--now",
        default=None,
        help="override 'now' as an ISO-8601 instant (used by tests)",
    )
    args = parser.parse_args(argv)

    now = datetime.fromisoformat(args.now) if args.now else datetime.now(timezone.utc)
    print(build_report(Path(args.data_root), unit=args.unit, repo=Path(args.repo), now=now))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
