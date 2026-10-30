"""EV-Lab: one immutable bounded collector epoch, systemd restarts it indefinitely.

The existing corrected official-only collector owns raw SHA, classifications
and SQLite writes. This wrapper only chooses a new root and records termination.
Never resumes or deletes earlier epochs; never changes API polling semantics.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import shutil
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

from tools.task0017_official_only import run as collector_run

UTC = dt.timezone.utc


def next_root(base: Path, *, now: dt.datetime | None = None, suffix: str | None = None) -> Path:
    now = now or dt.datetime.now(UTC)
    if now.utcoffset() is None:
        raise ValueError("UTC timestamp required")
    name = now.astimezone(UTC).strftime("run-%Y%m%dT%H%M%S%fZ-") + (suffix or uuid.uuid4().hex[:10])
    if not name.startswith("run-") or "/" in name or "\\" in name:
        raise ValueError("invalid run ID")
    return base / "runs" / name


def snapshot(root: Path) -> dict:
    path = root / "official.sqlite3"
    if not path.is_file():
        return {"captures": 0, "status_counts": {}, "sqlite": "NOT_CREATED"}
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        if quick != "ok":
            raise ValueError("collector SQLite integrity failed")
        counts = dict(conn.execute("SELECT result,COUNT(*) FROM captures GROUP BY result").fetchall())
        n = sum(counts.values())
        times = conn.execute("SELECT MIN(observed_at_utc),MAX(observed_at_utc) FROM captures").fetchone()
    return {"captures": n, "status_counts": counts, "sqlite": "ok",
            "first_utc": times[0], "last_utc": times[1]}


def one_epoch(base: Path, *, source_commit: str, max_rounds: int = 120,
              max_hours: float = 2.5, interval: float = 60.0,
              timeout: float = 20.0, max_bad: int = 3,
              min_free_gib: float = 3.0,
              now: dt.datetime | None = None) -> tuple[int, Path]:
    if (len(source_commit) != 40 or
            any(c not in "0123456789abcdef" for c in source_commit.lower())):
        raise ValueError("source_commit must be pinned Git SHA")
    if (max_rounds < 1 or not 0 < max_hours <= 24 or
            interval < 30 or not 0 < timeout <= interval or max_bad < 1 or
            min_free_gib < 0):
        raise ValueError("unsafe collector epoch parameters")
    base = base.resolve()
    base.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(base).free < min_free_gib * (1024 ** 3):
        raise OSError("low disk space: preserve old raw source, refusing new capture")
    root = next_root(base, now=now)
    root.mkdir(parents=True, exist_ok=False)
    started = dt.datetime.now(UTC).isoformat()
    result = 2
    error = None
    try:
        result = collector_run(root, max_rounds=max_rounds, max_hours=max_hours,
                               cadence=interval, timeout=timeout, max_bad=max_bad,
                               commit=source_commit)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:200]
    finally:
        outcome = {"task": "TASK0045", "root": root.name,
                   "source_commit": source_commit, "started_at_utc": started,
                   "ended_at_utc": dt.datetime.now(UTC).isoformat(),
                   "collector_exit": result, "error": error}
        try:
            outcome.update(snapshot(root))
        except (sqlite3.Error, ValueError, OSError) as exc:
            outcome["audit_error"] = type(exc).__name__ + ": " + str(exc)[:200]
            result = 2
            outcome["collector_exit"] = result
        # Create only; never replace raw data. Even failed epochs stay forensics.
        with (root / "CYCLE_OUTCOME.json").open("x", encoding="utf-8") as dest:
            json.dump(outcome, dest, ensure_ascii=False, sort_keys=True, indent=2)
        print(json.dumps({"event": "epoch_complete", **outcome}, ensure_ascii=False), flush=True)
    return result, root


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-base", required=True, type=Path)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--max-rounds", type=int, default=120)
    p.add_argument("--max-hours", type=float, default=2.5)
    p.add_argument("--interval", type=float, default=60)
    p.add_argument("--timeout", type=float, default=20)
    p.add_argument("--max-bad", type=int, default=3)
    p.add_argument("--min-free-gib", type=float, default=3.0)
    a = p.parse_args()
    result, _ = one_epoch(a.data_base, source_commit=a.source_commit,
                          max_rounds=a.max_rounds, max_hours=a.max_hours,
                          interval=a.interval, timeout=a.timeout, max_bad=a.max_bad,
                          min_free_gib=a.min_free_gib)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
