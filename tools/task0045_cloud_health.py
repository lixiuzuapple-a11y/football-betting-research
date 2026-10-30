"""EV-Lab independent systemd watchdog, full live raw SHA audit, append-only alarms.

Does not alter collector raw, databases, historical roots, or any other project.
If collector is absent/stale/corrupt, ask systemd to restart it into a NEW
immutable root; retain prior bytes and record alarms independently.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.task0041_cloud_capture_audit import audit

UTC = dt.timezone.utc
UNIT = "evlab-task0045-official.service"


def service_state(unit: str = UNIT) -> dict:
    if unit != UNIT:
        raise ValueError("watchdog may only target designated EV-Lab unit")
    proc = subprocess.run(["systemctl", "show", unit,
                           "-p", "ActiveState", "-p", "SubState",
                           "-p", "MainPID", "-p", "NRestarts",
                           "-p", "ExecMainStartTimestamp"],
                          text=True, capture_output=True, check=False, timeout=12)
    if proc.returncode:
        raise RuntimeError("systemctl show failed: " + proc.stderr[:160])
    state = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    if not {"ActiveState", "MainPID"}.issubset(state):
        raise RuntimeError("systemd status incomplete")
    return state


def latest_root(base: Path) -> Path | None:
    runbase = base / "runs"
    if not runbase.is_dir():
        return None
    runs = sorted(p for p in runbase.iterdir() if p.is_dir() and p.name.startswith("run-"))
    return runs[-1] if runs else None


def check(base: Path, parser: Path, *, now: dt.datetime | None = None,
          state: dict | None = None, max_lag_seconds: int = 360,
          min_free_gib: float = 3.0) -> dict:
    now = now or dt.datetime.now(UTC)
    if now.utcoffset() is None:
        raise ValueError("naive check timestamp")
    now = now.astimezone(UTC)
    base = base.resolve()
    status = state if state is not None else service_state()
    current = latest_root(base)
    health = {"checked_at_utc": now.isoformat(), "unit": UNIT,
              "unit_active": status["ActiveState"], "main_pid": status["MainPID"],
              "n_restarts": status.get("NRestarts"), "status": "ALERT"}
    free = shutil.disk_usage(base).free
    health["disk_free_bytes"] = free
    if free < min_free_gib * (1024 ** 3):
        health["reason"] = "low_disk_space_no_delete"
        return health
    if status["ActiveState"] != "active" or int(status["MainPID"]) <= 0:
        health["reason"] = "collector_not_running"
        return health
    if current is None:
        health["status"] = "STARTING"
        health["reason"] = "awaiting_first_epoch"
        return health
    health["latest_epoch"] = current.name
    db = current / "official.sqlite3"
    if not db.exists():
        age = (now - dt.datetime.fromtimestamp(current.stat().st_mtime, UTC)).total_seconds()
        if 0 <= age <= max_lag_seconds:
            health["status"] = "STARTING"
            health["reason"] = "awaiting_first_capture"
            return health
        health["reason"] = "no_capture_database"
        return health
    try:
        result = audit(current, parser)
    except Exception as exc:
        health["reason"] = "raw_integrity_" + type(exc).__name__ + ": " + str(exc)[:160]
        return health
    last = dt.datetime.fromisoformat(result["observed_last_utc"])
    lag = (now - last).total_seconds()
    health.update({"captures_in_epoch": result["captures"],
                   "verified_raw_captures": result["verified_sha_captures"],
                   "status_counts": result["original_result_counts"],
                   "lag_seconds": round(lag, 2),
                   "sqlite": result["sqlite_quick_check"]})
    outcomes = result["last_10_old_results"]
    recent_bad = 0
    for outcome in reversed(outcomes):
        if outcome in ("ok", "no_offer"):
            break
        recent_bad += 1
    if not -30 <= lag <= max_lag_seconds:
        health["reason"] = "collector_stale_or_future_clock"
    elif recent_bad >= 3:
        health["reason"] = "consecutive_bad_responses"
    elif recent_bad:
        health["status"] = "DEGRADED"
        health["reason"] = "latest_source_or_transport_error"
    else:
        health["status"] = "OK"
    health["consecutive_bad_responses"] = recent_bad
    return health


def record(base: Path, status: dict) -> None:
    output = base / "health"
    output.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(status, ensure_ascii=False, sort_keys=True) + "\n").encode()
    with (output / "events.jsonl").open("ab") as log:
        log.write(encoded)
        log.flush()
        os.fsync(log.fileno())
    fd, temporary = tempfile.mkstemp(prefix=".health-", dir=output)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(encoded)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, output / "LATEST.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def restart_collector(unit: str = UNIT) -> None:
    if unit != UNIT:
        raise ValueError("refuse to restart unapproved unit")
    subprocess.run(["systemctl", "restart", unit], check=True, timeout=25)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-base", required=True, type=Path)
    p.add_argument("--parser", required=True, type=Path)
    p.add_argument("--max-lag-seconds", type=int, default=360)
    args = p.parse_args()
    if args.max_lag_seconds < 180:
        p.error("stale threshold below safe minimum")
    result = check(args.data_base, args.parser, max_lag_seconds=args.max_lag_seconds)
    if result["status"] == "ALERT":
        # Preserve all evidence; service restart creates an entirely new root.
        try:
            restart_collector()
            result["watchdog_action"] = "systemd_restart_requested"
        except Exception as exc:
            result["watchdog_action"] = "restart_failed_" + type(exc).__name__
    record(args.data_base, result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 2 if result["status"] == "ALERT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
