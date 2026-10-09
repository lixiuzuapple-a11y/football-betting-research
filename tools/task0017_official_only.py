"""TASK-0017 bounded official Sporttery-only capture.

No BetExplorer and no historical database writes. The source JSON contains all
five odds pools; downstream normalization is deliberately a separate step.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry"
HEADERS = {
    "User-Agent": "football-betting-research/0.0.1 (+sporttery-capture)",
    "Referer": "https://www.sporttery.cn/",
    "Accept": "application/json, text/plain, */*",
}
SCHEMA = """CREATE TABLE IF NOT EXISTS captures (
    capture_id INTEGER PRIMARY KEY,
    observed_at_utc TEXT NOT NULL,
    request_url TEXT NOT NULL,
    http_status INTEGER,
    result TEXT NOT NULL,
    match_count INTEGER,
    raw_sha256 TEXT,
    raw_path TEXT,
    raw_length INTEGER,
    provider_last_update TEXT,
    error TEXT,
    source_commit TEXT NOT NULL
);"""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify(body: bytes) -> tuple[str, int, str | None]:
    """Return (status, fixture count, upstream last update); no odds inference."""
    obj = json.loads(body)
    if not isinstance(obj, dict) or obj.get("success") is not True:
        return "source_error", 0, None
    value = obj.get("value") or {}
    if not isinstance(value, dict):
        return "schema_error", 0, None
    groups = value.get("matchInfoList") or []
    if not isinstance(groups, list):
        return "schema_error", 0, None
    count = 0
    for group in groups:
        if not isinstance(group, dict):
            return "schema_error", 0, None
        matches = group.get("subMatchList") or []
        if not isinstance(matches, list):
            return "schema_error", 0, None
        count += len(matches)
    return ("ok" if count else "empty"), count, value.get("lastUpdateTime")


def fetch(timeout: float) -> tuple[bytes, int]:
    req = urllib.request.Request(ENDPOINT, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.read(), int(res.status)
    except urllib.error.HTTPError as exc:
        return exc.read(), int(exc.code)


def capture_once(conn: sqlite3.Connection, root: Path, *, timeout: float, commit: str) -> dict:
    at = now_utc()
    body = b""
    http_status = None
    error = None
    result = "transport_error"
    match_count = None
    upstream = None
    try:
        body, http_status = fetch(timeout)
        if http_status != 200:
            result = "http_error"
        else:
            try:
                result, match_count, upstream = classify(body)
            except (ValueError, TypeError, KeyError) as exc:
                result = "invalid_json"
                error = f"{type(exc).__name__}: {str(exc)[:180]}"
    except (OSError, TimeoutError) as exc:
        error = f"{type(exc).__name__}: {str(exc)[:180]}"
    received = now_utc()
    raw_hash = None
    rel = None
    if body:
        raw_hash = hashlib.sha256(body).hexdigest()
        date = received[:10].replace("-", "")
        rel = f"raw/{date}/{raw_hash}.json.gz"
        file = root / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        if not file.exists():
            tmp = file.with_suffix(".tmp")
            with tmp.open("wb") as out:
                out.write(gzip.compress(body, mtime=0))
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp, file)
    with conn:
        cur = conn.execute(
            """INSERT INTO captures
               (observed_at_utc,request_url,http_status,result,match_count,
                raw_sha256,raw_path,raw_length,provider_last_update,error,source_commit)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (received, ENDPOINT, http_status, result, match_count,
             raw_hash, rel, len(body) if body else None, upstream, error, commit)
        )
    return {"capture_id": cur.lastrowid, "at": received, "http": http_status,
            "result": result, "matches": match_count, "sha256": raw_hash}


def run(root: Path, *, max_rounds: int, max_hours: float, cadence: float,
        timeout: float, max_bad: int, commit: str) -> int:
    if not commit or commit == "unknown":
        raise ValueError("source commit is required for provenance")
    root.mkdir(parents=True, exist_ok=True)
    meta = root / "CONFIG.json"
    settings = {"url": ENDPOINT, "cadence_seconds": cadence, "timeout_seconds": timeout,
                "max_rounds": max_rounds, "max_hours": max_hours,
                "max_consecutive_bad": max_bad, "source_commit": commit,
                "created_at_utc": now_utc(), "mode": "QUALIFICATION_OFFICIAL_ONLY"}
    if meta.exists():
        raise FileExistsError("Refusing to start on existing root: " + str(root))
    meta.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    conn = sqlite3.connect(str(root / "official.sqlite3"), timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute(SCHEMA)
    conn.commit()
    start = time.monotonic()
    bad = 0
    try:
        for n in range(max_rounds):
            if time.monotonic() - start >= max_hours * 3600:
                print("STOP max_hours elapsed", flush=True)
                return 0
            loop_start = time.monotonic()
            row = capture_once(conn, root, timeout=timeout, commit=commit)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            if row["result"] != "ok":
                bad += 1
                if bad >= max_bad:
                    print("STOP consecutive non-successful/empty responses", file=sys.stderr, flush=True)
                    return 2
            else:
                bad = 0
            if n + 1 < max_rounds:
                remaining = min(cadence - (time.monotonic() - loop_start),
                                max_hours * 3600 - (time.monotonic() - start))
                if remaining > 0:
                    time.sleep(remaining)
        print("STOP max_rounds reached", flush=True)
        return 0
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--max-rounds", type=int, default=720)
    p.add_argument("--max-hours", type=float, default=12)
    p.add_argument("--interval", type=float, default=60)
    p.add_argument("--timeout", type=float, default=20)
    p.add_argument("--max-bad", type=int, default=3)
    args = p.parse_args()
    if args.max_hours <= 0 or args.max_rounds <= 0 or args.interval < 30 or args.timeout <= 0 or args.max_bad < 1:
        p.error("Invalid bounded run parameters")
    return run(args.data_root, max_rounds=args.max_rounds, max_hours=args.max_hours,
               cadence=args.interval, timeout=args.timeout, max_bad=args.max_bad,
               commit=args.source_commit)


if __name__ == "__main__":
    raise SystemExit(main())
