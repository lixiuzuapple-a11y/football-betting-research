"""EV-Lab data factory v1: verified immutable official captures -> candidate event store.

Research only: output is NOT a tradable book, model forecast, result join or BUY signal.
All source roots are opened read-only. Chronology is global across source runs.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import heapq
import json
import math
import os
import sqlite3
import tempfile
from contextlib import ExitStack, closing
from pathlib import Path

from tools.task0028_timeline_gate import POOLS, parse_time, provider_time, price_vector
from tools.task0029_quote_candidates import transition

BEIJING = dt.timezone(dt.timedelta(hours=8))
SCHEMA = """
CREATE TABLE source_captures(
 source_root TEXT NOT NULL, source_capture_id INTEGER NOT NULL,
 observed_utc TEXT NOT NULL, result TEXT NOT NULL,
 raw_sha256 TEXT, fixture_count INTEGER,
 PRIMARY KEY(source_root, source_capture_id)
);
CREATE TABLE fixtures(
 match_id TEXT PRIMARY KEY, home_team_id TEXT NOT NULL,
 away_team_id TEXT NOT NULL, match_date TEXT NOT NULL,
 kickoff_utc TEXT NOT NULL
);
CREATE TABLE quote_candidates(
 id INTEGER PRIMARY KEY,
 match_id TEXT NOT NULL REFERENCES fixtures(match_id),
 pool TEXT NOT NULL, observed_utc TEXT NOT NULL,
 provider_updated_utc TEXT NOT NULL, kickoff_utc TEXT NOT NULL,
 event_kind TEXT NOT NULL, odds_json TEXT NOT NULL,
 handicap TEXT NOT NULL, raw_sha256 TEXT NOT NULL,
 source_root TEXT NOT NULL, source_capture_id INTEGER NOT NULL,
 FOREIGN KEY(source_root, source_capture_id)
   REFERENCES source_captures(source_root, source_capture_id)
);
CREATE INDEX quote_by_match_cutoff
 ON quote_candidates(match_id, pool, observed_utc);
CREATE INDEX quote_by_pool_time ON quote_candidates(pool, observed_utc);
"""

def _iso_utc(value: str) -> dt.datetime:
    parsed = parse_time(value)
    if parsed is None or parsed.utcoffset() is None:
        raise ValueError("missing or naive capture timestamp")
    return parsed.astimezone(dt.timezone.utc)

def _kickoff(m: dict) -> dt.datetime:
    raw = str(m.get("matchDate", "")) + "T" + str(m.get("matchTime", ""))
    try:
        return dt.datetime.fromisoformat(raw).replace(tzinfo=BEIJING).astimezone(dt.timezone.utc)
    except ValueError as exc:
        raise ValueError("invalid kickoff date/time") from exc

def _safe_raw(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel.startswith("raw/") or not rel.endswith(".json.gz"):
        raise ValueError("noncanonical raw path")
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise ValueError("raw path escaped root or missing")
    return candidate

def _capture_rows(stack: ExitStack, root: Path):
    db = root / "official.sqlite3"
    if not db.is_file():
        raise FileNotFoundError(db)
    uri = db.resolve().as_uri() + "?mode=ro"
    con = stack.enter_context(closing(sqlite3.connect(uri, uri=True, timeout=10)))
    con.execute("PRAGMA query_only=ON")
    if con.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise ValueError("source SQLite quick_check failed")
    prev = None
    for item in con.execute("""SELECT capture_id, observed_at_utc, result, raw_sha256,
                                      raw_path, match_count
                               FROM captures ORDER BY observed_at_utc, capture_id"""):
        cid, observed_text, *_ = item
        moment = _iso_utc(observed_text)
        if prev is not None and moment < prev:
            raise ValueError("source timestamps out of order")
        prev = moment
        yield moment, cid, item

def _tagged(stream, root_name: str, index: int):
    for moment, cid, item in stream:
        yield moment, root_name, cid, index, item

def _valid_finite_prices(row: dict) -> bool:
    pairs = price_vector(row)
    if not pairs:
        return False
    try:
        return all(math.isfinite(float(v)) and float(v) > 1 for _, v in pairs)
    except (ValueError, TypeError, OverflowError):
        return False

def build(roots: list[Path], output: Path, *, max_quote_age_hours: float = 6,
          max_captures: int | None = None) -> dict:
    if not roots or max_quote_age_hours <= 0 or max_captures is not None and max_captures < 1:
        raise ValueError("invalid root, quote age or capture limit")
    sources = [Path(p).resolve() for p in roots]
    if len(set(sources)) != len(sources) or len({p.name for p in sources}) != len(sources):
        raise ValueError("source roots must have unique paths and names")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("refuse to overwrite output: " + str(output))
    if any(output.is_relative_to(root) for root in sources):
        raise ValueError("output cannot live under source root")
    output.parent.mkdir(parents=True, exist_ok=True)
    counters = collections.Counter()
    classifications = {pool: collections.Counter() for pool in POOLS}
    last = {}
    with tempfile.TemporaryDirectory(prefix="evlab-factory-", dir=output.parent) as work:
        temp_db = Path(work) / "factory.sqlite3"
        with ExitStack() as stack:
            streams = [_capture_rows(stack, root) for root in sources]
            ordered = heapq.merge(*[
                _tagged(stream, root.name, index)
                for index, (root, stream) in enumerate(zip(sources, streams))
            ])
            # The heap is ordered by real receive timestamps, not the order --root was given.
            out = stack.enter_context(closing(sqlite3.connect(temp_db)))
            out.execute("PRAGMA foreign_keys=ON")
            out.executescript(SCHEMA)
            identities = {}
            for moment, root_name, cid, index, item in ordered:
                if max_captures is not None and counters["captures"] >= max_captures:
                    break
                root = sources[index]
                _, seen, status, sha, relative, stated_count = item
                counters["captures"] += 1
                counters["result_" + str(status)] += 1
                out.execute("INSERT INTO source_captures VALUES(?,?,?,?,?,?)",
                            (root_name, cid, moment.isoformat(), status, sha, stated_count))
                if not relative:
                    if status == "ok":
                        raise ValueError("ok capture missing raw")
                    continue
                raw = gzip.open(_safe_raw(root, relative), "rb").read()
                if hashlib.sha256(raw).hexdigest() != sha:
                    raise ValueError("source raw SHA256 mismatch: " + root_name + "/" + str(cid))
                counters["verified_raw"] += 1
                if status != "ok":
                    continue
                payload = json.loads(raw)
                if payload.get("success") is not True:
                    raise ValueError("marked ok, provider says unsuccessful")
                groups = payload["value"]["matchInfoList"]
                matches = [m for group in groups for m in group["subMatchList"]]
                if len(matches) != stated_count:
                    raise ValueError("source match count mismatch")
                seen_ids = set()
                for m in matches:
                    mid = str(m["matchId"])
                    if mid in seen_ids:
                        raise ValueError("duplicate match ID inside capture")
                    seen_ids.add(mid)
                    kickoff = _kickoff(m)
                    identity = (str(m.get("homeTeamId")), str(m.get("awayTeamId")),
                                str(m.get("matchDate")), kickoff.isoformat())
                    if mid in identities and identities[mid] != identity:
                        raise ValueError("fixture identity changed: " + mid)
                    if mid not in identities:
                        identities[mid] = identity
                        out.execute("INSERT INTO fixtures VALUES(?,?,?,?,?)", (mid, *identity))
                    counters["fixture_observations"] += 1
                    for pool in POOLS:
                        row = m.get(pool)
                        if not isinstance(row, dict) or not row:
                            continue
                        classifications[pool]["observations"] += 1
                        if moment >= kickoff:
                            classifications[pool]["at_or_after_kickoff"] += 1
                            continue
                        if not _valid_finite_prices(row):
                            classifications[pool]["invalid_price"] += 1
                            continue
                        stamp = provider_time(row)
                        if stamp is None:
                            classifications[pool]["missing_provider_timestamp"] += 1
                            continue
                        if (moment - stamp).total_seconds() > max_quote_age_hours * 3600:
                            classifications[pool]["stale_provider_quote"] += 1
                            continue
                        key = (mid, pool)
                        kind, state = transition(last.get(key), row, moment, pool, m)
                        classifications[pool][kind] += 1
                        if state is None:
                            continue
                        last[key] = state
                        if kind not in ("initial", "advance_change"):
                            continue
                        out.execute(
                            """INSERT INTO quote_candidates
                            (match_id,pool,observed_utc,provider_updated_utc,kickoff_utc,
                             event_kind,odds_json,handicap,raw_sha256,source_root,source_capture_id)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                            (mid, pool, moment.isoformat(), stamp.astimezone(dt.timezone.utc).isoformat(),
                             kickoff.isoformat(), kind, json.dumps(price_vector(row)),
                             str(row.get("goalLine", "")), sha, root_name, cid))
                        counters["quote_events"] += 1
                if counters["captures"] % 1000 == 0:
                    out.commit()
            out.commit()
            if out.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("output SQLite failed quick_check")
        summary = {
            "schema_version": 1, "scope": "research candidate quotes, NOT executable odds",
            "source_roots": [str(p) for p in sources],
            "max_provider_age_hours": max_quote_age_hours,
            "partial_scan": max_captures is not None,
            "counts": dict(sorted(counters.items())),
            "distinct_fixtures": len(identities),
            "pools": {name: dict(sorted(stats.items())) for name, stats in classifications.items()},
            "no_results_or_bet_execution": True,
        }
        os.replace(temp_db, output)
    return summary

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, required=True)
    parser.add_argument("--out-db", required=True, type=Path)
    parser.add_argument("--out-summary", required=True, type=Path)
    parser.add_argument("--max-quote-age-hours", type=float, default=6.0)
    parser.add_argument("--max-captures", type=int)
    args = parser.parse_args()
    summary = Path(args.out_summary).resolve()
    if summary.exists() or summary == args.out_db.resolve():
        parser.error("summary exists or conflicts with output database")
    result = build(args.root, args.out_db, max_quote_age_hours=args.max_quote_age_hours,
                   max_captures=args.max_captures)
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
