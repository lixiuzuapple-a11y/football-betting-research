"""TASK0060: source-audited additive official-to-HF club identity bridge.

Offline only. Uses 87 previously reviewed exact Sporttery-to-ESPN event links
from TASK0034/0036, rechecks their original official/ESPN SHA bytes and the
frozen historical HF club ID/name table. Never joins using match results,
prices, model output, guesses, or an automatically inferred alias.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

from tools.task0043_prospective_multimodel_freeze import (
    ELIGIBLE_LEAGUES, EXPECTED_BRIDGE_SHA, EXPECTED_HISTORY_MANIFEST,
    frozen_team_bridge,
)

UTC = dt.timezone.utc
BJT = dt.timezone(dt.timedelta(hours=8))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_unique_sha_source(roots: list[Path], ids: set[str]) -> dict:
    """Same original source as TASK0037, but inspect each SHA once, not 9500 repeats.

    Every gzip source is validated against the frozen capture SQLite's body
    SHA256, and no historical results or market odds are used.
    """
    found = {}
    inspected = set()
    for root in roots:
        db = sqlite3.connect("file:" + (root / "official.sqlite3").resolve().as_posix()
                             + "?mode=ro", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("original official SQLite failed quick_check")
            for path, source_sha in db.execute(
                "SELECT raw_path,raw_sha256 FROM captures WHERE result='ok'"
                " GROUP BY raw_path,raw_sha256 ORDER BY MIN(capture_id)"
            ):
                if len(found) == len(ids):
                    break
                if (not path.startswith("raw/") or not path.endswith(".json.gz")
                        or ".." in Path(path).parts):
                    raise ValueError("unsafe original official raw path")
                if (root.name, source_sha) in inspected:
                    continue
                inspected.add((root.name, source_sha))
                raw_path = (root / path).resolve()
                if not raw_path.is_relative_to(root.resolve()):
                    raise ValueError("source path outside official evidence")
                body = gzip.decompress(raw_path.read_bytes())
                if hashlib.sha256(body).hexdigest() != source_sha:
                    raise ValueError("original Sporttery body SHA mismatch")
                doc = json.loads(body)
                for group in doc.get("value", {}).get("matchInfoList", []):
                    for fixture in group.get("subMatchList", []):
                        mid = str(fixture.get("matchId", ""))
                        if mid not in ids or mid in found:
                            continue
                        found[mid] = {
                            "official_h_zh": fixture["homeTeamAllName"],
                            "official_a_zh": fixture["awayTeamAllName"],
                            "official_hid": str(fixture["homeTeamId"]),
                            "official_aid": str(fixture["awayTeamId"]),
                            "raw_sha256": source_sha,
                            "raw_path": path,
                            "snapshot": root.name,
                        }
        finally:
            db.close()
        if len(found) == len(ids):
            break
    if len(found) != len(ids):
        raise ValueError(f"missing original source matches {len(found)}/{len(ids)}")
    return found


def source_events(folder: Path, receipts: list, *, old: bool) -> dict:
    """Reject altered ESPN snapshots, unknown opponents and event-ID clashes."""
    events = {}
    for receipt in receipts:
        if receipt.get("http" if old else "status") != 200:
            continue
        path = folder / receipt["path" if old else "file"]
        if sha(path) != receipt["sha256"]:
            raise ValueError("archived ESPN source SHA mismatch")
        for e in read(path).get("events", []):
            pair = {z["homeAway"]: z["team"] for z in
                    e["competitions"][0]["competitors"]}
            if set(pair) != {"home", "away"}:
                raise ValueError("ESPN source home/away malformed")
            value = (str(pair["home"]["id"]), str(pair["away"]["id"]),
                     str(e["date"]))
            key = str(e["id"])
            if key in events and events[key] != value:
                raise ValueError("same ESPN fixture had differing club identity")
            events[key] = value
    return events


def utc_event(date: str, time: str, *, bjt: bool):
    instant = dt.datetime.fromisoformat(date + "T" + time)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=BJT if bjt else UTC)
    return instant.astimezone(UTC)


def validate_espn(events: dict, event_id, home_id, away_id, kickoff):
    match = events.get(str(event_id))
    if not match or match[:2] != (str(home_id), str(away_id)):
        raise ValueError("accepted match's ESPN club IDs missing or contradicted")
    when = dt.datetime.fromisoformat(match[2].replace("Z", "+00:00"))
    if when.astimezone(UTC) != kickoff:
        raise ValueError("ESPN event does not match the official kickoff")


def build(*, base: Path, identity: Path, history: Path) -> dict:
    import duckdb
    started = time.monotonic()
    def pulse(text):
        print("TASK0060_PROGRESS", text, round(time.monotonic()-started, 2),
              file=sys.stderr, flush=True)

    pulse("START")
    path34 = base / "task0034-espn-bridge-20261019"
    path36 = base / "task0036-data-source-gate-20261022"
    old34 = read(path34 / "TASK0034-IDENTITY-AUDIT.json")
    old36 = read(path36 / "TASK0036-STRICT-INCREMENTAL-BRIDGE.json")
    if len(old34["joined_fixtures"]) != 76 or len(old36["accepted"]) != 11:
        raise ValueError("accepted cross-source fixture cohort changed")
    old, original_sha = frozen_team_bridge(identity)
    if len(old) != 70 or original_sha != EXPECTED_BRIDGE_SHA:
        raise ValueError("immutable 70-club identity base changed")
    if sha(history / "hf_manifest.json") != EXPECTED_HISTORY_MANIFEST:
        raise ValueError("frozen HF training source changed")
    for item in read(history / "hf_manifest.json"):
        if sha(history / item["file"]) != item["sha256"]:
            raise ValueError("frozen historical source bytes changed")
    pulse("FROZEN_HISTORY_SHA_VERIFIED")

    matches = old34["joined_fixtures"] + old36["accepted"]
    original = base / "official-20261018"
    source_roots = [original / "task0024-official-20261010",
                    original / "task0025-official-20261015"]
    labels = collect_unique_sha_source(
        source_roots, {str(z["matchId"]) for z in matches}
    )
    pulse("OFFICIAL_GZIP_VERIFIED_87")
    if len(labels) != 87:
        raise ValueError("missing official original-source match")
    espn34 = source_events(path34, read(path34 / "TASK0034-ESPN-BRIDGE.json")["fetches"],
                           old=True)
    espn36 = source_events(path36 / "ESPN",
                           read(path36 / "ESPN" / "ESPN_PROBES.json"),
                           old=False)
    pulse("ESPN_ORIGINAL_SHA_VERIFIED")

    db = duckdb.connect()
    try:
        teams = db.execute(
            "SELECT id,name,fd_name FROM read_parquet(?)",
            [str(history / "teams.parquet")],
        ).fetchall()
        hf_teams = {int(i): str(name) for i, name, _ in teams}
        fd_index = collections.defaultdict(list)
        for i, name, fd in teams:
            if fd:
                fd_index[fd.casefold()].append((int(i), str(name)))
        # Only played fixtures strictly within frozen training dates, never
        # newly completed matches whose final labels are outside the release.
        played = db.execute(
            "SELECT league_id,team_id,SUM(n) FROM ("
            " SELECT league_id,home_team_id team_id,COUNT(*) n "
            " FROM read_parquet(?) WHERE is_played=true "
            " AND date_utc < '2026-07-05' GROUP BY league_id,home_team_id"
            " UNION ALL "
            " SELECT league_id,away_team_id team_id,COUNT(*) n "
            " FROM read_parquet(?) WHERE is_played=true "
            " AND date_utc < '2026-07-05' GROUP BY league_id,away_team_id"
            ") GROUP BY league_id,team_id",
            [str(history / "fixtures.parquet"), str(history / "fixtures.parquet")],
        ).fetchall()
        historical_n = {(int(l), int(t)): int(n) for l, t, n in played}
        hf_fixtures = {
            int(row[0]): row for row in db.execute(
                "SELECT id,league_id,home_team_id,away_team_id,date_utc"
                " FROM read_parquet(?) WHERE date_utc >= '2026-10-01' "
                " AND date_utc < '2026-11-01'",
                [str(history / "fixtures.parquet")],
            ).fetchall()
        }
    finally:
        db.close()
    pulse("HISTORICAL_ID_AND_TRAINING_JOIN_LOADED")

    candidates = collections.defaultdict(list)
    rejected = []
    reverse_old = {int(v[0]): k for k, v in old.items()}

    def add(oid, name_zh, hf_id, league, witness):
        if league not in ELIGIBLE_LEAGUES:
            rejected.append({"official_id": oid, "reason": "outside_current_14_leagues"})
            return
        if hf_id not in hf_teams:
            raise ValueError("previously accepted HF ID missing in historical data")
        n = historical_n.get((ELIGIBLE_LEAGUES[league][0], hf_id), 0)
        if n < 5:
            rejected.append({"official_id": oid, "reason": "frozen_league_training_below_5",
                             "games": n})
            return
        if oid in old:
            if old[oid] != (hf_id, name_zh):
                raise ValueError("original approved official-to-HF club conflict")
            return
        if hf_id in reverse_old:
            raise ValueError("new official ID aliases existing approved HF club")
        candidates[oid].append({
            "official_id": oid, "official_zh": name_zh,
            "hf_team_id": hf_id, "hf_team_name": hf_teams[hf_id],
            "training_matches_in_league": n, "witness": witness,
        })

    for match in old34["joined_fixtures"]:
        mid = str(match["matchId"])
        label = labels[mid]
        league = match["league"]
        validate_espn(espn34, match["espn_event_id"],
                      match["espn_home_team_id"], match["espn_away_team_id"],
                      utc_event(match["day"], match["time"], bjt=True))
        for side, short in (("home", "h"), ("away", "a")):
            oid = str(match["official_" + side + "_team_id"])
            if oid != label["official_" + short + "id"]:
                raise ValueError("Sporttery team ID contradicts independently reviewed match")
            zh = label["official_" + short + "_zh"]
            fd_name = match["fd_" + side]
            possible = [
                i for i, _ in fd_index.get(fd_name.casefold(), [])
                if league in ELIGIBLE_LEAGUES and
                historical_n.get((ELIGIBLE_LEAGUES[league][0], i), 0) > 0
            ]
            if len(possible) != 1:
                rejected.append({"official_id": oid, "reason": "HF_fd_name_not_unique",
                                 "match_id": mid, "fd_name": fd_name,
                                 "matching_ids": possible})
                continue
            add(oid, zh, possible[0], league, {
                "reviewed_cohort": "TASK0034",
                "match_id": mid, "espn_event_id": str(match["espn_event_id"]),
                "source_sha256": label["raw_sha256"], "fd_name": fd_name,
            })

    for match in old36["accepted"]:
        mid = str(match["matchId"])
        league = match["league"]
        label = labels[mid]
        validate_espn(espn36, match["ESPN_id"], match["ESPN_home_id"],
                      match["ESPN_away_id"],
                      utc_event(match["utc"][:10], match["utc"][11:19], bjt=False))
        if league not in ELIGIBLE_LEAGUES:
            continue
        hf_row = hf_fixtures.get(int(match["HF_fixture_id"]))
        if (not hf_row or int(hf_row[1]) != ELIGIBLE_LEAGUES[league][0]
                or int(hf_row[2]) != int(match["HF_home_id"])
                or int(hf_row[3]) != int(match["HF_away_id"])
                or hf_row[4].replace(tzinfo=UTC) !=
                utc_event(match["utc"][:10], match["utc"][11:19], bjt=False)):
            raise ValueError("reviewed TASK0036 HF future fixture source mismatch")
        for side, short in (("home", "h"), ("away", "a")):
            oid = str(match["official_" + side + "_id"])
            if oid != label["official_" + short + "id"]:
                raise ValueError("TASK0036 reviewed official team ID mismatch")
            add(oid, label["official_" + short + "_zh"],
                int(match["HF_" + side + "_id"]), league, {
                    "reviewed_cohort": "TASK0036",
                    "match_id": mid, "espn_event_id": str(match["ESPN_id"]),
                    "frozen_hf_fixture_id": int(match["HF_fixture_id"]),
                    "source_sha256": label["raw_sha256"],
                })

    additions, used = [], set(reverse_old)
    for oid, proofs in sorted(candidates.items(), key=lambda z: int(z[0])):
        mapped = {(z["hf_team_id"], z["official_zh"], z["hf_team_name"])
                  for z in proofs}
        if len(mapped) != 1:
            rejected.append({"official_id": oid, "reason": "conflicting_cross_source_witness"})
            continue
        hf_id, zh, hf_name = next(iter(mapped))
        if hf_id in used:
            rejected.append({"official_id": oid, "reason": "HF_id_alias_collision"})
            continue
        used.add(hf_id)
        additions.append({
            "official_id": oid, "official_zh": zh,
            "hf_team_id": hf_id, "hf_team_name": hf_name,
            "minimum_pre_july_league_games": min(
                p["training_matches_in_league"] for p in proofs
            ),
            "witnesses": sorted(
                (p["witness"] for p in proofs),
                key=lambda w: (w["reviewed_cohort"], w["match_id"]),
            ),
        })
    if not additions:
        raise ValueError("no new clubs passed independent source audits")
    return {
        "task": "TASK0060", "phase": "STRICT_ADDITIVE_CLUB_IDENTITY_ONLY",
        "original_70_unchanged": True,
        "original_clubs": 70, "additional_clubs": len(additions),
        "total_authorized_clubs": 70 + len(additions),
        "original_bridge_sha256": original_sha,
        "frozen_training_manifest_sha256": EXPECTED_HISTORY_MANIFEST,
        "reviewed_0034_report_sha256": sha(path34 / "TASK0034-IDENTITY-AUDIT.json"),
        "reviewed_0036_report_sha256": sha(path36 / "TASK0036-STRICT-INCREMENTAL-BRIDGE.json"),
        "additions": additions, "rejected_source_observations": rejected,
        "limits": [
            "Only previously accepted match identities, verified original HTTP source SHA.",
            "No retroactive pre-kickoff forecasts; no new model training or market input.",
            "14-league policy and original 70 club identity crosswalk unchanged.",
            "Model calibration, CLV, betting profitability and positive EV unproven.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-backups", type=Path, required=True)
    p.add_argument("--original-identity", type=Path, required=True)
    p.add_argument("--history", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = build(base=a.source_backups, identity=a.original_identity, history=a.history)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("x", encoding="utf8") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({
        "status": "STRICT_ADDITIVE_CLUB_IDENTITY_REPLAY",
        "old": 70, "added": result["additional_clubs"],
        "total": result["total_authorized_clubs"],
        "rejection_observations": len(result["rejected_source_observations"]),
        "artifact_sha256": sha(a.out),
    }))


if __name__ == "__main__":
    main()
