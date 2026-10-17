"""Read-only, reproducible fixture coverage and replay diagnostics for bounded official collectors.

Counts are structural observations, NOT independently verified price moves or ROI.
"""
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
import statistics
from pathlib import Path

POOLS = ("had", "hhad", "ttg", "crs", "hafu")


def audit(roots):
    matches = collections.defaultdict(list)
    run_stats = []
    for root in roots:
        root = Path(root)
        con = sqlite3.connect(f"file:{(root / 'official.sqlite3').resolve().as_posix()}?mode=ro", uri=True)
        try:
            if con.execute("pragma integrity_check").fetchone()[0] != "ok":
                raise ValueError(f"sqlite corrupt: {root}")
            counts = collections.Counter()
            for cid, timestamp, result, sha, path in con.execute(
                "select capture_id,observed_at_utc,result,raw_sha256,raw_path from captures order by capture_id"
            ):
                counts[result] += 1
                if path is None:
                    if result != "transport_error":
                        raise ValueError(f"missing payload {root} {cid}")
                    continue
                raw = gzip.open(root / path, "rb").read()
                if hashlib.sha256(raw).hexdigest() != sha:
                    raise ValueError(f"hash mismatch {root} {cid}")
                document = json.loads(raw)
                if result != "ok":
                    continue
                groups = document["value"]["matchInfoList"]
                for group in groups:
                    for match in group["subMatchList"]:
                        mid = str(match["matchId"])
                        matches[mid].append((timestamp, match))
            run_stats.append({"root": str(root), "counts": dict(counts)})
        finally:
            con.close()
    lengths = [len(v) for v in matches.values()]
    durations = []
    per_pool = {}
    for series in matches.values():
        start = dt.datetime.fromisoformat(series[0][0])
        end = dt.datetime.fromisoformat(series[-1][0])
        durations.append((end - start).total_seconds() / 3600)
    for pool in POOLS:
        n_present = n_transitions = n_prior_returns = 0
        for series in matches.values():
            values = [json.dumps(m.get(pool), sort_keys=True, ensure_ascii=False, separators=(",", ":")) for _, m in series]
            n_present += int(any(m.get(pool) not in (None, {}, []) for _, m in series))
            seen = set()
            previous = None
            for value in values:
                if previous is not None and value != previous:
                    n_transitions += 1
                    n_prior_returns += int(value in seen)
                seen.add(value)
                previous = value
        per_pool[pool] = {"matches_with_nonempty_field": n_present,
                          "raw_field_transitions": n_transitions,
                          "returns_to_earlier_seen_state": n_prior_returns}
    return {
        "run_stats": run_stats,
        "distinct_matches": len(matches),
        "total_match_observations": sum(lengths),
        "observations_min_median_max": [min(lengths), statistics.median(lengths), max(lengths)] if lengths else [],
        "matches_with_at_most_3_observations": sum(x <= 3 for x in lengths),
        "duration_hours_median": statistics.median(durations) if durations else None,
        "matches_observed_less_than_1_hour": sum(x < 1 for x in durations),
        "matches_observed_at_least_6_hours": sum(x >= 6 for x in durations),
        "pool_diagnostics": per_pool,
        "outcome_results_verified": 0,
        "caveat": "Structural replay/state-change audit only; not validated odds vectors, prices, or EV.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    value = audit(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(value, ensure_ascii=False))


if __name__ == "__main__":
    main()
