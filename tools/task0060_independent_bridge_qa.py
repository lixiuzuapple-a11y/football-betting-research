"""Independent, source-grounded verifier for TASK0060 additive 73-club proof.

Checks all promoted club identities by directly reopening original zipped
Sporttery captures indexed in original SQLite, original SHA-verified ESPN
event pages, and frozen HF parquet, without calling the primary build().
Never upgrades a refused club or manufactures an earlier forecast.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

from tools.task0043_prospective_multimodel_freeze import (
    EXPECTED_BRIDGE_SHA, EXPECTED_HISTORY_MANIFEST,
    ELIGIBLE_LEAGUES, frozen_team_bridge,
)

UTC = dt.timezone.utc
BJT = dt.timezone(dt.timedelta(hours=8))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iso(ts: str):
    value = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if value.utcoffset() is None:
        raise ValueError("non-timezoned accepted original")
    return value.astimezone(UTC)


def independent_qa(*, base: Path, history: Path, original_identity: Path,
                   extension: Path) -> dict:
    import duckdb
    proof = read(extension)
    old, old_sha = frozen_team_bridge(original_identity)
    if old_sha != EXPECTED_BRIDGE_SHA or proof["original_bridge_sha256"] != old_sha:
        raise ValueError("original preapproved 70 original changed")
    if digest(history / "hf_manifest.json") != EXPECTED_HISTORY_MANIFEST:
        raise ValueError("independent HF manifest not pinned")
    for entry in read(history / "hf_manifest.json"):
        if digest(history / entry["file"]) != entry["sha256"]:
            raise ValueError("independent HF original parquet SHA mismatch")
    folder34 = base / "task0034-espn-bridge-20261019"
    folder36 = base / "task0036-data-source-gate-20261022"
    joins34 = read(folder34 / "TASK0034-IDENTITY-AUDIT.json")
    joins36 = read(folder36 / "TASK0036-STRICT-INCREMENTAL-BRIDGE.json")
    if (digest(folder34 / "TASK0034-IDENTITY-AUDIT.json") !=
            proof["reviewed_0034_report_sha256"]
            or digest(folder36 / "TASK0036-STRICT-INCREMENTAL-BRIDGE.json") !=
            proof["reviewed_0036_report_sha256"]):
        raise ValueError("independent reviewed historical join SHA changed")
    matches34 = {str(x["matchId"]): x for x in joins34["joined_fixtures"]}
    matches36 = {str(x["matchId"]): x for x in joins36["accepted"]}
    if len(matches34) != 76 or len(matches36) != 11:
        raise ValueError("accepted 87 match join set changed")

    # Independently reload ESPN originals and their stored SHA receipts.
    espn = {}
    for folder, receipts, old_format in (
        (folder34, read(folder34 / "TASK0034-ESPN-BRIDGE.json")["fetches"], True),
        (folder36 / "ESPN", read(folder36 / "ESPN" / "ESPN_PROBES.json"), False),
    ):
        for item in receipts:
            if item.get("http" if old_format else "status") != 200:
                continue
            source = folder / item["path" if old_format else "file"]
            if digest(source) != item["sha256"]:
                raise ValueError("independent ESPN snapshot SHA mismatch")
            for event in read(source).get("events", []):
                competitors = event["competitions"][0]["competitors"]
                sides = {a["homeAway"]: str(a["team"]["id"]) for a in competitors}
                if len(sides) != 2 or set(sides) != {"home", "away"}:
                    raise ValueError("invalid ESPN sides")
                pair = (sides["home"], sides["away"], iso(event["date"]))
                key = (old_format, str(event["id"]))
                if key in espn and espn[key] != pair:
                    raise ValueError("independent ESPN event source changed")
                espn[key] = pair

    # Do not use any output from primary HF join. Recompute training counts.
    db = duckdb.connect()
    try:
        table = db.execute("SELECT id,name,fd_name FROM read_parquet(?)",
                           [str(history / "teams.parquet")]).fetchall()
        exact = {int(team_id): (name, fd) for team_id, name, fd in table}
        fd_lookup = collections.defaultdict(list)
        for hid, name, fd in table:
            if fd:
                fd_lookup[fd.casefold()].append(int(hid))
        prior_games = db.execute(
            "SELECT league_id, team_id, COUNT(*) n FROM ("
            " SELECT league_id, home_team_id team_id FROM read_parquet(?)"
            " WHERE is_played=true AND date_utc < '2026-07-05'"
            " UNION ALL "
            " SELECT league_id, away_team_id team_id FROM read_parquet(?)"
            " WHERE is_played=true AND date_utc < '2026-07-05'"
            ") GROUP BY league_id,team_id",
            [str(history / "fixtures.parquet"), str(history / "fixtures.parquet")],
        ).fetchall()
        coverage = {(int(l), int(h)): int(n) for l, h, n in prior_games}
        future_hf = {int(row[0]): row for row in db.execute(
            "SELECT id,league_id,home_team_id,away_team_id,date_utc"
            " FROM read_parquet(?) WHERE date_utc >= '2026-10-01'"
            " AND date_utc < '2026-11-01'",
            [str(history / "fixtures.parquet")],
        ).fetchall()}
    finally:
        db.close()

    # Read only the immutable original source SHA that each promoted club
    # names as witness; no scanning every otherwise irrelevant capture.
    original_root = base / "official-20261018"
    snapshot_cursors = {}
    raw_cache = {}
    def original_matches(snapshot: str, body_sha: str):
        key = (snapshot, body_sha)
        if key in raw_cache:
            return raw_cache[key]
        if snapshot not in ("task0024-official-20261010",
                            "task0025-official-20261015"):
            raise ValueError("unapproved official snapshot location")
        root = original_root / snapshot
        if snapshot not in snapshot_cursors:
            conn = sqlite3.connect("file:" + (root / "official.sqlite3").resolve().as_posix()
                                   + "?mode=ro", uri=True)
            conn.execute("PRAGMA query_only=ON")
            snapshot_cursors[snapshot] = conn
        result = snapshot_cursors[snapshot].execute(
            "SELECT raw_path FROM captures WHERE raw_sha256=? AND result='ok' LIMIT 1",
            (body_sha,),
        ).fetchone()
        if result is None:
            raise ValueError("official raw SHA not found in original SQLite")
        loc = (root / result[0]).resolve()
        if not loc.is_relative_to(root.resolve()):
            raise ValueError("official source path outside original evidence")
        raw = gzip.decompress(loc.read_bytes())
        if hashlib.sha256(raw).hexdigest() != body_sha:
            raise ValueError("original Sporttery gzip body SHA differs")
        rows = [x for group in json.loads(raw)["value"]["matchInfoList"]
                for x in group["subMatchList"]]
        if len(rows) != len({str(r["matchId"]) for r in rows}):
            raise ValueError("duplicate official matchId")
        raw_cache[key] = {str(x["matchId"]): x for x in rows}
        return raw_cache[key]

    used_hf = {int(v[0]) for v in old.values()}
    used_official = set(old)
    independent_counts = collections.Counter()
    samples_by_league = collections.Counter()
    checked_ids = []
    try:
        for team in proof["additions"]:
            oid = str(team["official_id"])
            hid = int(team["hf_team_id"])
            name = team["official_zh"]
            if oid in used_official or hid in used_hf:
                raise ValueError("independent duplicate official or HF club")
            if exact.get(hid, (None, None))[0] != team["hf_team_name"]:
                raise ValueError("independent HF team id/name different")
            used_official.add(oid)
            used_hf.add(hid)
            independent_counts["added_clubs"] += 1
            checked_ids.append(oid)
            for witness in team["witnesses"]:
                cohort = witness["reviewed_cohort"]
                mid = witness["match_id"]
                match = (matches34 if cohort == "TASK0034" else
                         matches36 if cohort == "TASK0036" else {}) .get(str(mid))
                if match is None:
                    raise ValueError("independent original witness not accepted")
                side = None
                for s in ("home", "away"):
                    name_key = ("official_" + s + "_team_id" if cohort == "TASK0034"
                                else "official_" + s + "_id")
                    if str(match[name_key]) == oid:
                        side = s
                if side is None:
                    raise ValueError("promoted official ID not in its own witness")
                league = match["league"]
                if league not in ELIGIBLE_LEAGUES:
                    raise ValueError("unapproved league supplied club training")
                league_id = ELIGIBLE_LEAGUES[league][0]
                games = coverage.get((league_id, hid), 0)
                if games < 5:
                    raise ValueError("not enough independently computed prior league games")
                samples_by_league[league] += 1
                if cohort == "TASK0034":
                    if (witness["espn_event_id"] != str(match["espn_event_id"])
                            or witness["fd_name"] != match["fd_" + side]):
                        raise ValueError("TASK0034 witness FD/ESPN join changed")
                    unique = [x for x in fd_lookup[witness["fd_name"].casefold()]
                              if coverage.get((league_id, x), 0) > 0]
                    if unique != [hid]:
                        raise ValueError("TASK0034 HF name/league not unique")
                    event = espn.get((True, str(match["espn_event_id"])))
                    target_time = dt.datetime.fromisoformat(
                        match["day"] + "T" + match["time"]
                    ).replace(tzinfo=BJT).astimezone(UTC)
                    home_espn, away_espn = (
                        str(match["espn_home_team_id"]),
                        str(match["espn_away_team_id"]),
                    )
                else:
                    if (witness["espn_event_id"] != str(match["ESPN_id"])
                            or witness["frozen_hf_fixture_id"] != int(match["HF_fixture_id"])):
                        raise ValueError("TASK0036 reviewed event/fixture mismatch")
                    future = future_hf.get(int(match["HF_fixture_id"]))
                    if future is None or int(future[1]) != league_id:
                        raise ValueError("TASK0036 original HF fixture missing/league conflict")
                    hf_side = int(match["HF_" + side + "_id"])
                    if hf_side != hid or int(future[2 if side == "home" else 3]) != hid:
                        raise ValueError("TASK0036 frozen HF fixture opposite team")
                    event = espn.get((False, str(match["ESPN_id"])))
                    target_time = dt.datetime.fromisoformat(match["utc"]).replace(
                        tzinfo=UTC)
                    home_espn, away_espn = (
                        str(match["ESPN_home_id"]), str(match["ESPN_away_id"]))
                if event is None or event != (home_espn, away_espn, target_time):
                    raise ValueError("independent ESPN team IDs/time not exact")
                snapshot = ("task0024-official-20261010" if cohort == "TASK0034"
                            else None)
                # Original journal source ID may be either of the two archives.
                for candidate_snapshot in ("task0024-official-20261010",
                                           "task0025-official-20261015"):
                    conn = snapshot_cursors.get(candidate_snapshot)
                    if conn is None:
                        root = original_root / candidate_snapshot
                        conn = sqlite3.connect("file:" +
                            (root / "official.sqlite3").resolve().as_posix() +
                            "?mode=ro", uri=True)
                        conn.execute("PRAGMA query_only=ON")
                        snapshot_cursors[candidate_snapshot] = conn
                    exists = conn.execute(
                        "SELECT 1 FROM captures WHERE raw_sha256=? LIMIT 1",
                        (witness["source_sha256"],)).fetchone()
                    if exists:
                        snapshot = candidate_snapshot
                        break
                if not snapshot:
                    raise ValueError("witness official SHA absent from snapshots")
                official = original_matches(snapshot, witness["source_sha256"]).get(str(mid))
                if official is None:
                    raise ValueError("witness original official match not in source SHA")
                if (str(official["homeTeamId" if side == "home" else "awayTeamId"]) != oid
                        or official["homeTeamAllName" if side == "home"
                                     else "awayTeamAllName"] != name):
                    raise ValueError("Sporttery original official name/ID contradicted")
                independent_counts["witnesses_verified"] += 1
        if independent_counts["added_clubs"] != 73 or len(used_hf) != 143:
            raise ValueError("independent addition counts not 73+70")
    finally:
        for conn in snapshot_cursors.values():
            conn.close()
    return {
        "task": "TASK0060", "verdict": "INDEPENDENT_SOURCE_SHA_TEAM_IDENTITY_ACCEPT",
        "reviewed_extension_sha256": digest(extension),
        "original_clubs_unmodified": 70,
        "new_clubs_independently_verified": independent_counts["added_clubs"],
        "total_clubs_unique": len(used_hf),
        "individual_source_witnesses_verified": independent_counts[
            "witnesses_verified"],
        "witness_league_distribution": dict(sorted(samples_by_league.items())),
        "all_new_official_ids": sorted(checked_ids, key=int),
        "limits": "source/provenance check only, no new prospective results, market or EV",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-backups", "history", "original-identity",
                 "extension", "out"):
        parser.add_argument("--"+name, dest=name.replace("-", "_"),
                            type=Path, required=True)
    opts = parser.parse_args()
    result = independent_qa(
        base=opts.source_backups, history=opts.history,
        original_identity=opts.original_identity, extension=opts.extension,
    )
    opts.out.parent.mkdir(parents=True, exist_ok=True)
    with opts.out.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
