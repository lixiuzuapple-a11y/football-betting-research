"""TASK0058: read-only, SHA-gated audit of the existing official offer supply.

Purpose: test whether additional collection times would have found MORE
preapproved identity+league prospects than the 11:15 daily publisher.
This tool is retrospective diagnostics ONLY. It never creates forecasts,
promotes a new identity, changes model gates, commits, or places bets.

Use only completed TASK0045 collector cycles; all source bytes remain off-Git.
The 11:15 TASK0046 one-shot results are checked independently elsewhere.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from tools.task0017_official_only import ENDPOINT
from tools.task0043_prospective_multimodel_freeze import (
    EXPECTED_BRIDGE_SHA, frozen_team_bridge,
    qualify_fixtures,
)

UTC = dt.timezone.utc
BJT = dt.timezone(dt.timedelta(hours=8))
RUN_PATTERN = re.compile(r"run-(\d{8})T\d{6}\d{6}Z-[a-z0-9]+")
# This is NOT the current mutable production catalog. The original Nov10
# TASK0058 experiment was frozen under exactly these two leagues. Future
# prospective policy expansions must not rewrite its earlier 34/3/1 result.
TASK0058_FROZEN_LEAGUES = {
    "挪超": (23, "Eliteserien", "Norway"),
    "法甲": (9, "Ligue 1", "France"),
}


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_completed_roots(collector_runs: Path, frozen: dict) -> list[Path]:
    """Reproduce a previous as-of audit, never ingest later-completed runs.

    The original 2026-11-10 report was built while a two-hour collection was
    still active. That cycle finished LATER and contains earlier timestamps.
    A time-window filter alone therefore changes the cohort on replay.
    """
    if (frozen.get("task") != "TASK0058"
            or frozen.get("status") != "DESCRIPTIVE_OFFICIAL_SUPPLY_AUDIT_NO_FORECAST"
            or not isinstance(frozen.get("source_run_receipts"), list)
            or not frozen["source_run_receipts"]):
        raise ValueError("not a valid previously frozen source cohort report")
    roots = []
    seen = set()
    base = collector_runs.resolve()
    for receipt in frozen["source_run_receipts"]:
        name = receipt.get("run_id")
        if (not isinstance(name, str) or not RUN_PATTERN.fullmatch(name)
                or name in seen):
            raise ValueError("invalid/duplicate frozen source cycle ID")
        seen.add(name)
        root = (base / name).resolve()
        if not root.is_relative_to(base):
            raise ValueError("unsafe frozen cycle path")
        for rel, key in (
            ("CYCLE_OUTCOME.json", "completed_cycle_outcome_sha256"),
            ("official.sqlite3", "source_sqlite_sha256"),
        ):
            recorded = receipt.get(key)
            if not isinstance(recorded, str) or len(recorded) != 64:
                raise ValueError("missing frozen cycle SHA")
            if hash_file(root / rel) != recorded:
                raise ValueError("frozen completed cycle file SHA mismatch")
        roots.append(root)
    return roots


def as_utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("naive official observation timestamp")
    return parsed.astimezone(UTC)


def unpack_source(root: Path, relative: str, sha: str, size: int) -> list[dict]:
    """Source SHA refers to the *decompressed* HTTP body, not the gzip file."""
    if (not relative.startswith("raw/") or not relative.endswith(".json.gz")
            or "\\" in relative or ".." in Path(relative).parts):
        raise ValueError("unsafe source path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("raw source missing/outside evidence root")
    raw = gzip.decompress(path.read_bytes())
    if hashlib.sha256(raw).hexdigest() != sha or len(raw) != size:
        raise ValueError("official gzip source bytes/SHA mismatch")
    doc = json.loads(raw)
    if (doc.get("success") is not True
            or doc.get("errorCode") not in (0, "0", None)
            or not isinstance(doc.get("value"), dict)
            or not isinstance(doc["value"].get("matchInfoList"), list)):
        raise ValueError("invalid official provider response")
    fixtures = []
    for group in doc["value"]["matchInfoList"]:
        if not isinstance(group, dict) or not isinstance(group.get("subMatchList"), list):
            raise ValueError("invalid provider fixture group")
        fixtures.extend(group["subMatchList"])
    ids = [str(x["matchId"]) for x in fixtures]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate official fixture identity within one snapshot")
    return fixtures


def read_completed_cycle(root: Path, *, expected_endpoint: str = ENDPOINT):
    root = root.resolve()
    complete = root / "CYCLE_OUTCOME.json"
    if not complete.exists():
        raise ValueError("live/uncompleted collector cycle excluded")
    outcome = json.loads(complete.read_bytes())
    config = json.loads((root / "CONFIG.json").read_bytes())
    if (outcome.get("task") != "TASK0045"
            or outcome.get("collector_exit") != 0
            or outcome.get("sqlite") != "ok"
            or config.get("mode") != "QUALIFICATION_OFFICIAL_ONLY"
            or config.get("url") != expected_endpoint
            or outcome.get("source_commit") != config.get("source_commit")):
        raise ValueError("untrusted completed source cycle")
    path = root / "official.sqlite3"
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        conn.execute("PRAGMA query_only=ON")
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("source SQLite integrity failed")
        rows = conn.execute(
            "SELECT capture_id, observed_at_utc, request_url, http_status,"
            " result, match_count, raw_sha256, raw_path, raw_length, source_commit"
            " FROM captures ORDER BY capture_id"
        ).fetchall()
    finally:
        conn.close()
    if len(rows) != outcome.get("captures"):
        raise ValueError("completed collector capture count disagrees with SQLite")
    if not rows:
        raise ValueError("completed collector with no source captures")
    statuses = collections.Counter(r[4] for r in rows)
    if dict(statuses) != outcome.get("status_counts"):
        raise ValueError("status counts disagree with signed-off collector cycle")
    cache = {}
    for cid, observed, url, http, status, count, sha, rel, length, commit in rows:
        when = as_utc(observed)
        if url != expected_endpoint or commit != config["source_commit"]:
            raise ValueError("official endpoint or source commit changed")
        if status not in ("ok", "no_offer") or http != 200:
            # A completed two-hour collector cycle may include individual
            # transport errors. Count them, but NEVER impute match coverage.
            if status in ("ok", "no_offer"):
                raise ValueError("claim of valid source with HTTP failure")
            yield when, [], status, None
            continue
        if status == "no_offer":
            if count != 0:
                raise ValueError("no_offer with nonzero fixture count")
            fixtures = []
        else:
            if not sha or not rel or length is None:
                raise ValueError("missing source SHA/bytes/locator")
            if rel not in cache:
                cache[rel] = (sha, length, unpack_source(root, rel, sha, length))
            old_sha, old_length, fixtures = cache[rel]
            if old_sha != sha or old_length != length:
                raise ValueError("same source path reused with conflicting SHA/length")
            if len(fixtures) != count:
                raise ValueError("source fixture count mismatch")
        yield when, fixtures, status, sha


def audit_runs(roots: list[Path], bridge: Path, *,
               first_utc: dt.datetime, last_utc: dt.datetime) -> dict:
    if not first_utc < last_utc or first_utc.tzinfo is None or last_utc.tzinfo is None:
        raise ValueError("bounded UTC time interval required")
    if hash_file(bridge) != EXPECTED_BRIDGE_SHA:
        raise ValueError("strict preapproved team mapping SHA changed")
    crosswalk, _ = frozen_team_bridge(bridge)
    daily = {}
    unique_all = set()
    unique_future = set()
    unique_league = set()
    eligible_window = {}
    cycle_receipts = []
    seen_roots = set()
    for root in sorted(roots):
        root = root.resolve()
        if root in seen_roots:
            raise ValueError("duplicate collector root")
        seen_roots.add(root)
        cycle = json.loads((root / "CYCLE_OUTCOME.json").read_bytes())
        if (as_utc(cycle["last_utc"]) < first_utc
                or as_utc(cycle["first_utc"]) >= last_utc):
            continue
        captures = 0
        first_seen, last_seen = None, None
        row_counts = collections.Counter()
        for observed, fixtures, status, sha in read_completed_cycle(root):
            if not (first_utc <= observed < last_utc):
                continue
            first_seen = min(first_seen or observed, observed)
            last_seen = max(last_seen or observed, observed)
            captures += 1
            day = observed.astimezone(BJT).date().isoformat()
            d = daily.setdefault(day, {
                "captures": 0, "ok": 0, "no_offer": 0,
                "unusable_capture_count": 0,
                "observed_fixture_instances": 0,
                "_all_ids": set(), "_future_ids": set(),
                "_eligible_league_ids": set(), "_strict_ids": set(),
                "rejection_observations": collections.Counter(),
                "league_approved_observations": 0,
            })
            d["captures"] += 1
            d[status] = d.get(status, 0) + 1
            if status not in ("ok", "no_offer"):
                d["unusable_capture_count"] += 1
            d["observed_fixture_instances"] += len(fixtures)
            allowed, rejected = qualify_fixtures(
                fixtures, crosswalk, observed, approved_leagues=TASK0058_FROZEN_LEAGUES
            )
            d["rejection_observations"].update(rejected)
            row_counts[status] += 1
            for row in fixtures:
                mid = str(row["matchId"])
                d["_all_ids"].add(mid)
                unique_all.add(mid)
                kickoff = dt.datetime.fromisoformat(
                    str(row["matchDate"]) + "T" + str(row["matchTime"])
                ).replace(tzinfo=BJT).astimezone(UTC)
                if observed >= kickoff:
                    continue
                unique_future.add(mid)
                d["_future_ids"].add(mid)
                if str(row.get("leagueAbbName")) in TASK0058_FROZEN_LEAGUES:
                    unique_league.add(mid)
                    d["_eligible_league_ids"].add(mid)
                    d["league_approved_observations"] += 1
            for row in allowed:
                mid = row["matchId"]
                d["_strict_ids"].add(mid)
                obj = eligible_window.setdefault(mid, {
                    "league": row["league"], "kickoff_utc": row["kickoff_utc"],
                    "first_seen_utc": observed.isoformat(),
                    "last_seen_utc": observed.isoformat(),
                    "observations": 0,
                })
                if (obj["league"] != row["league"]
                        or obj["kickoff_utc"] != row["kickoff_utc"]):
                    raise ValueError("provider identity/league/kickoff varied across captures")
                obj["last_seen_utc"] = observed.isoformat()
                obj["observations"] += 1
        if captures:
            cycle_receipts.append({
                "run_id": root.name, "captures_in_window": captures,
                "first_observed_utc": first_seen.isoformat(),
                "last_observed_utc": last_seen.isoformat(),
                "completed_cycle_outcome_sha256": hash_file(root / "CYCLE_OUTCOME.json"),
                "source_sqlite_sha256": hash_file(root / "official.sqlite3"),
                "status_counts_in_window": dict(sorted(row_counts.items())),
            })
    if not cycle_receipts:
        raise ValueError("no completed official collector cycles within requested interval")
    formatted_daily = {}
    for day, d in sorted(daily.items()):
        formatted_daily[day] = {
            k: (len(v) if k in ("_all_ids", "_future_ids",
                                "_eligible_league_ids", "_strict_ids") else
                dict(sorted(v.items())) if k == "rejection_observations" else v)
            for k, v in d.items()
        }
    return {
        "task": "TASK0058",
        "status": "DESCRIPTIVE_OFFICIAL_SUPPLY_AUDIT_NO_FORECAST",
        "interval_utc": [first_utc.isoformat(), last_utc.isoformat()],
        "identity_ledger_sha256": EXPECTED_BRIDGE_SHA,
        "approved_leagues": sorted(TASK0058_FROZEN_LEAGUES),
        "completed_runs_used": len(cycle_receipts),
        "source_captures_observed": sum(d["captures"] for d in formatted_daily.values()),
        "verified_captures": sum(
            d["ok"] + d["no_offer"] for d in formatted_daily.values()
        ),
        "unusable_source_captures": sum(
            d["unusable_capture_count"] for d in formatted_daily.values()
        ),
        "unique_fixture_ids_any_status": len(unique_all),
        "unique_fixture_ids_observed_before_kickoff": len(unique_future),
        "unique_ids_in_approved_leagues_before_kickoff": len(unique_league),
        "unique_ids_strict_identity_and_league_preapproved": len(eligible_window),
        "eligible_observation_windows": dict(sorted(eligible_window.items())),
        "by_beijing_date": formatted_daily,
        "source_run_receipts": cycle_receipts,
        "limits": [
            "Repeated minute captures are not independent match observations.",
            "Completed TASK0045 cycles only: this is not the entire bookmaker/football universe.",
            "Historical capture times are the original server clock, not independent notarization.",
            "Identity+league approval is a necessary, not sufficient, condition for all four model forecasts.",
            "A retrospectively observed fixture without a prior Git commit can NEVER be scored as prospective.",
            "No additional league, identity, bookmaker odds, bets, model selection or positive EV inferred.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collector-runs", required=True, type=Path)
    ap.add_argument("--identity", required=True, type=Path)
    ap.add_argument("--start-utc", required=True)
    ap.add_argument("--end-utc", required=True)
    ap.add_argument("--pinned-source-report", type=Path,
                    help="Use exact original completed run IDs and verify their SHA; "
                         "prevents late-completed cycles from altering historical N")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    frozen = None
    if args.pinned_source_report:
        frozen = json.loads(args.pinned_source_report.read_bytes())
        roots = pinned_completed_roots(args.collector_runs, frozen)
    else:
        roots = [x for x in args.collector_runs.iterdir()
                 if x.is_dir() and RUN_PATTERN.fullmatch(x.name)
                 and (x / "CYCLE_OUTCOME.json").is_file()]
    result = audit_runs(roots, args.identity,
                        first_utc=as_utc(args.start_utc), last_utc=as_utc(args.end_utc))
    if frozen and result != frozen:
        raise ValueError("frozen completed-cycle replay arithmetic/receipts mismatch")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as file:
        json.dump(result, file, indent=2, sort_keys=True, ensure_ascii=False)
        file.write("\n")
    # Compact output only. Complete source receipts go into create-only JSON.
    print(json.dumps({k: result[k] for k in (
        "status", "completed_runs_used", "source_captures_observed",
        "verified_captures", "unusable_source_captures",
        "unique_fixture_ids_any_status",
        "unique_fixture_ids_observed_before_kickoff",
        "unique_ids_in_approved_leagues_before_kickoff",
        "unique_ids_strict_identity_and_league_preapproved",
        "eligible_observation_windows",
        "by_beijing_date",
    )}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
