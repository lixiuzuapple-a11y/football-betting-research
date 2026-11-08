"""TASK0055: independently audit daily *scheduled* EV-Lab cloud task runs.

This is a read-only watchdog, NOT a forecast, model, scorer or bookmaker.
It verifies the systemd timer's actual scheduled trigger and its corresponding
STARTED / FINISHED run log. Missing or interrupted jobs fail closed and
leave an immutable JSON finding on disk. There is no notification transport.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
# China has observed UTC+08:00 without DST since 1991. All audited schedule
# dates are 2026+, so a fixed offset avoids Windows' optional tzdata package
# and agrees with the cloud systemd Asia/Shanghai calendar.
SHANGHAI = dt.timezone(dt.timedelta(hours=8), name="Asia/Shanghai")
UTC = dt.timezone.utc
CONFIG = {
    "forward": {"name": "TASK0054", "clock": "11:15",
                "unit": "evlab-task0054-cloud-forward",
                "file": "evidence/scheduler/INVOCATIONS.jsonl"},
    "score": {"name": "TASK0054-SCORE", "clock": "18:30",
              "unit": "evlab-task0054-cloud-score",
              "file": "score-evidence/scheduler/INVOCATIONS.jsonl"},
}
TRIGGER_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\b")


def systemctl_value(unit: str, property_name: str) -> str:
    result = subprocess.run(
        ["systemctl", "show", unit, f"--property={property_name}", "--value"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    return result.stdout.strip()


def load_jsonl(path: Path) -> tuple[list[dict], str]:
    original = path.read_bytes()
    if not original or not original.endswith(b"\n"):
        raise ValueError("Missing, empty or torn invocation log")
    lines = original.decode("utf-8-sig").splitlines()
    if len(lines) > 100_000:
        raise ValueError("Invocation log exceeds bounded size; rotate with QA")
    entries = [json.loads(line) for line in lines]
    if not all(isinstance(x, dict) for x in entries):
        raise ValueError("Malformed invocation records")
    return entries, hashlib.sha256(original).hexdigest()


def local_timestamp(entry: dict) -> dt.datetime:
    stamp = dt.datetime.fromisoformat(entry["at_utc"].replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Missing timezone in invocation")
    return stamp.astimezone(SHANGHAI)


def parse_trigger(text: str) -> dt.datetime | None:
    """CST is ambiguous internationally: parse from this machine's Asia/Shanghai."""
    match = TRIGGER_PATTERN.search(text)
    if not match:
        return None
    naive = dt.datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    return naive.replace(tzinfo=SHANGHAI)


def inspect_run(entries: list[dict], task: str, expected: dt.datetime) -> dict:
    """Never accept a freehand run elsewhere on the same date as the timer."""
    window_start = expected - dt.timedelta(minutes=1)
    window_end = expected + dt.timedelta(minutes=20)
    awaiting = None
    successes = []
    failures = []
    for item in entries:
        if item.get("task") != task:
            continue
        try:
            when = local_timestamp(item)
        except (KeyError, ValueError, TypeError):
            failures.append("INVALID_TIMESTAMP")
            continue
        if not window_start <= when <= window_end:
            continue
        phase = item.get("phase")
        if phase == "STARTED":
            if awaiting is not None:
                failures.append("UNFINISHED_START")
            awaiting = when
        elif phase == "FINISHED":
            if awaiting is None or when < awaiting:
                failures.append("UNPAIRED_FINISHED")
                continue
            if when - awaiting > dt.timedelta(minutes=10):
                failures.append("TOO_LONG")
            elif item.get("exit_code") == 0:
                successes.append({"started": awaiting.isoformat(),
                                  "finished": when.isoformat()})
            else:
                failures.append(f"NONZERO_EXIT:{item.get('exit_code')}")
            awaiting = None
    if awaiting is not None:
        failures.append("UNFINISHED_START")
    return {"successful_pairs": successes, "anomalies": failures,
            "has_success": bool(successes)}


def audit(config: dict, entries: list[dict], *, day: dt.date,
          now: dt.datetime, trigger: str,
          timer_active: bool, timer_enabled: bool,
          service_result: str, service_exit: int,
          log_sha256: str) -> dict:
    """Pure evaluation; callers record findings even on failures."""
    expected = dt.datetime.combine(
        day, dt.time.fromisoformat(config["clock"]), tzinfo=SHANGHAI
    )
    local_now = now.astimezone(SHANGHAI)
    issues = []
    if local_now < expected + dt.timedelta(minutes=10):
        return {"status": "NOT_DUE", "issues": [],
                "date": day.isoformat(), "role": config["name"]}
    observed_trigger = parse_trigger(trigger)
    if observed_trigger is None or abs((observed_trigger - expected).total_seconds()) > 120:
        issues.append("MISSING_EXACT_SCHEDULED_TIMER_TRIGGER")
    if not timer_active or not timer_enabled:
        issues.append("TIMER_NOT_ENABLED_AND_ACTIVE")
    if service_result != "success" or service_exit != 0:
        issues.append("SERVICE_REPORTED_ERROR")
    checked = inspect_run(entries, config["name"], expected)
    if not checked["has_success"]:
        issues.append("NO_SUCCESSFUL_SCHEDULED_START_FINISH_PAIR")
    return {
        "task": "TASK0055",
        "status": "FAIL" if issues else ("PASS_WITH_RECOVERY" if checked["anomalies"] else "PASS"),
        "date": day.isoformat(),
        "role": config["name"],
        "expected_local": expected.isoformat(),
        "observed_timer": observed_trigger.isoformat() if observed_trigger else None,
        "timer_active": timer_active,
        "timer_enabled": timer_enabled,
        "unit_result": service_result,
        "unit_exit": service_exit,
        "invocations_sha256": log_sha256,
        "actual_runs": checked,
        "issues": issues,
        "interpretation": "Scheduled operation only; no market/PIT/EV or scoring success inferred",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=CONFIG)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--day", type=dt.date.fromisoformat,
                        default=dt.datetime.now(SHANGHAI).date())
    args = parser.parse_args()
    root = args.root.resolve()
    config = CONFIG[args.role]
    unit = config["unit"]
    try:
        entries, digest = load_jsonl(root / config["file"])
        active = systemctl_value(unit + ".timer", "ActiveState") == "active"
        enabled = systemctl_value(unit + ".timer", "UnitFileState") == "enabled"
        trigger = systemctl_value(unit + ".timer", "LastTriggerUSec")
        result = systemctl_value(unit + ".service", "Result")
        status = int(systemctl_value(unit + ".service", "ExecMainStatus"))
        finding = audit(config, entries, day=args.day,
                        now=dt.datetime.now(UTC), trigger=trigger,
                        timer_active=active, timer_enabled=enabled,
                        service_result=result, service_exit=status,
                        log_sha256=digest)
    except Exception as exc:
        finding = {"task": "TASK0055", "status": "FAIL",
                   "date": args.day.isoformat(), "role": config["name"],
                   "issues": [type(exc).__name__ + ": " + str(exc)[:300]]}

    evidence = root / "operational-audits"
    evidence.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = evidence / (
        args.day.strftime("%Y%m%d") + "-" + args.role + "-" +
        dt.datetime.now(UTC).strftime("%H%M%S%f") + "-" + uuid.uuid4().hex[:8] +
        ".json"
    )
    finding["written_at_utc"] = dt.datetime.now(UTC).isoformat()
    with path.open("x", encoding="utf-8") as file:
        json.dump(finding, file, indent=2, ensure_ascii=False, sort_keys=True)
        file.write("\n")
    print(json.dumps({"evidence": str(path), **finding}, ensure_ascii=False))
    return 0 if finding["status"] in ("PASS", "PASS_WITH_RECOVERY", "NOT_DUE") else 1


if __name__ == "__main__":
    sys.exit(main())
