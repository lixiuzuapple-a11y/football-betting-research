"""Read-only audit of the TASK-0006 official Sporttery capture, no BetExplorer.

Usage: python tools/task0014_official_audit.py --db /path/ledger.sqlite3 --raw /path/raw
No DB writes and no outcome/profit computation. Prints compact JSON.
"""
import argparse
import collections
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

POOLS = ("HAD", "HHAD", "TTG", "CRS", "HAFU")
PRICE_KEYS = {
    "HAD": ("h", "d", "a"),
    "HHAD": ("h", "d", "a"),
    "TTG": tuple(f"s{i}" for i in range(8)),
    "CRS": ("s00s00", "s00s01", "s01s00"),  # presence sentinel, not full coverage
    "HAFU": ("hh", "hd", "ha", "dh", "dd", "da", "ah", "ad", "aa"),
}


def audit(db: Path, raw: Path):
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro&immutable=1", uri=True)
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    daily = conn.execute("""
        SELECT substr(c.response_received_at,1,10), count(DISTINCT c.capture_id),
               count(f.fact_id), count(DISTINCT f.match_id)
        FROM captures c LEFT JOIN sporttery_facts f ON c.capture_id=f.capture_id
        WHERE c.source='official_sporttery' AND c.capture_kind='regular'
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    fact_summary = conn.execute("""
        SELECT count(*), count(DISTINCT match_id), count(DISTINCT capture_id),
               sum(had_betting_single=1), count(DISTINCT CASE WHEN had_betting_single=1 THEN match_id END)
        FROM sporttery_facts
    """).fetchone()
    paths = conn.execute("""
        SELECT DISTINCT raw_file_path FROM captures
        WHERE source='official_sporttery' AND capture_kind='regular'
          AND raw_file_path IS NOT NULL
    """).fetchall()
    conn.close()

    count = collections.Counter()
    single = collections.Counter()
    priced = collections.Counter()
    missing_close = collections.Counter()
    clocks = {p: set() for p in POOLS}
    match_ids = set()
    days = collections.defaultdict(set)
    for (rel,) in paths:
        blob = gzip.open(raw / rel, "rb").read()
        payload = json.loads(blob)
        for group in (payload.get("value", {}).get("matchInfoList") or []):
            for match in group.get("subMatchList", []):
                mid = str(match.get("matchId"))
                match_ids.add(mid)
                days[(match.get("businessDate") or match.get("matchDate") or "")[:10]].add(mid)
                access = {p.get("poolCode"): p for p in match.get("poolList", [])}
                for pool in POOLS:
                    quote, perm = match.get(pool.lower()), access.get(pool)
                    if not isinstance(quote, dict) or not isinstance(perm, dict):
                        continue
                    count[pool] += 1
                    if perm.get("bettingSingle") == 1 and perm.get("poolStatus") == "Selling":
                        single[pool] += 1
                    if all(quote.get(key) not in (None, "") for key in PRICE_KEYS[pool]):
                        priced[pool] += 1
                    if not perm.get("poolCloseDate") or not perm.get("poolCloseTime"):
                        missing_close[pool] += 1
                    if quote.get("updateDate") and quote.get("updateTime"):
                        clocks[pool].add((mid, quote["updateDate"], quote["updateTime"]))
    return {
        "sqlite_integrity": integrity,
        "daily_regular_captures_and_standardized_facts": [
            {"capture_date_utc": day, "regular_captures": n,
             "had_fact_rows": facts, "distinct_matches": matches}
            for day, n, facts, matches in daily
        ],
        "had_standardized": dict(zip(
            ("fact_rows", "matches", "captured_source_rows", "single_allowed_rows", "single_allowed_matches"),
            fact_summary)),
        "unique_regular_raw_paths": len(paths),
        "raw_distinct_matches": len(match_ids),
        "raw_business_day_distinct_matches": {k: len(v) for k, v in sorted(days.items())},
        "raw_pools": {p: {
            "raw_match_occurrences": count[p],
            "selling_single_occurrences": single[p],
            "selected_price_fields_present": priced[p],
            "unique_provider_update_match_pairs": len(clocks[p]),
            "missing_close_datetime_occurrences": missing_close[p],
        } for p in POOLS},
        "cautions": [
            "A raw occurrence counts one match per distinct raw-file path, not an independent fixture or opportunity.",
            "CRS selected_price_fields_present checks only three sentinel fields, not all exact scores.",
            "A provider update timestamp is not independent proof of confirmed executable betting.",
            "An empty post-September-30 fact table does not itself prove network or API failure.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.db, args.raw), ensure_ascii=False, indent=2))
