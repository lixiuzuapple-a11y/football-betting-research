"""Independent read-only QA: verify TASK0061 14-league registry vs frozen HF.

Separate from generator. SQL recomputes membership and training match counts,
raw UTF-8 CSVs are SHA-pinned, original/additional approved IDs stay unchanged.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

LEAGUES = {23,9,1,5,7,11,13,14,21,38,19,2,10,12}


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check(*, folder: Path, history: Path, identity: Path, extension: Path):
    import duckdb
    from tools.task0043_prospective_multimodel_freeze import (
        frozen_team_bridge, EXPECTED_BRIDGE_SHA, TASK0060_EXTENSION_SHA,
    )
    doc = json.loads((folder/"registry_manifest.json").read_text(encoding="utf8"))
    source = {}
    for name, record in doc["files"].items():
        file = folder/name
        if sha(file) != record["sha256"]:
            raise ValueError("registry output source SHA mismatch")
        source[name] = read_csv(file)
        if len(source[name]) != record["rows"]:
            raise ValueError("registry manifest row count mismatch")
    master = source["team_master.csv"]
    memberships = source["league_team_crosswalk.csv"]
    summary = source["league_summary.csv"]
    aliases = source["alias_candidates.csv"]
    assert len(summary) == 14 and len({int(x["league_hf_id"]) for x in summary}) == 14
    assert {int(x["league_hf_id"]) for x in summary} == LEAGUES
    if len({x["canonical_team_id"] for x in master}) != len(master):
        raise ValueError("duplicate master canonical team key")
    approved = [x for x in master if x["mapping_status"] == "VERIFIED_PUBLISHED"]
    if len(approved) != 143 or len({x["official_team_id"] for x in approved}) != 143:
        raise ValueError("published approved identity count or uniqueness changed")
    if any(x["official_team_id"] for x in master if x not in approved):
        raise ValueError("unapproved historical team received official ID")
    if any(x["alias_approval_status"] !=
           "SOURCE_ONLY_NOT_CROSS_PROVIDER_APPROVED" for x in aliases):
        raise ValueError("an alias was automatically approved")
    if any(x["wikidata_qid_unverified"] for x in master):
        raise ValueError("unverified Wikidata QID falsely included as identity")
    original, origin_sha = frozen_team_bridge(identity)
    if origin_sha != EXPECTED_BRIDGE_SHA or sha(extension) != TASK0060_EXTENSION_SHA:
        raise ValueError("approved club original/extension raw SHA changed")
    added = json.loads(extension.read_text(encoding="utf8"))["additions"]
    expected = {
        str(oid): (int(hf), zh) for oid, (hf, zh) in original.items()
    }
    for row in added:
        oid = str(row["official_id"])
        if oid in expected:
            raise ValueError("official club extension duplicated original ID")
        expected[oid] = (int(row["hf_team_id"]), row["official_zh"])
    for item in approved:
        oid = item["official_team_id"]
        if expected.get(oid) != (int(item["hf_team_id"]), item["official_name_zh"]):
            raise ValueError("source-approved published club altered in registry")
    if len(expected) != len(approved):
        raise ValueError("approved crosswalk not fully represented in master")

    q = duckdb.connect()
    try:
        expected_rows = q.execute(
            "WITH x AS ("
            " SELECT league_id,home_team_id tid,date_utc FROM read_parquet(?)"
            " WHERE is_played=true AND date_utc<'2026-07-05'"
            " UNION ALL"
            " SELECT league_id,away_team_id tid,date_utc FROM read_parquet(?)"
            " WHERE is_played=true AND date_utc<'2026-07-05'"
            ") SELECT league_id,tid,COUNT(*),MAX(date_utc) FROM x"
            " WHERE league_id IN (1,2,5,7,9,10,11,12,13,14,19,21,23,38)"
            " GROUP BY league_id,tid",
            [str(history/"fixtures.parquet"),
             str(history/"fixtures.parquet")],
        ).fetchall()
    finally:
        q.close()
    expected_by_pair = {
        (int(lid),int(tid)): (int(n), last.isoformat()+"Z")
        for lid,tid,n,last in expected_rows
    }
    actual_by_pair = {}
    for x in memberships:
        key = (int(x["league_hf_id"]), int(x["hf_team_id"]))
        if key in actual_by_pair:
            raise ValueError("duplicate league/HF-team membership")
        actual_by_pair[key] = (int(x["historic_completed_league_matches"]),
                               x["last_historical_kickoff_utc"])
        if x["mapping_status"] not in (
            "VERIFIED_PUBLISHED", "HF_HISTORY_ONLY_UNVERIFIED"
        ):
            raise ValueError("unexpected candidate approval state")
        if (x["official_team_id"] and
                expected[x["official_team_id"]] !=
                (int(x["hf_team_id"]), x["official_name_zh"])):
            raise ValueError("membership cross-source club ID/name mismatch")
    if actual_by_pair != expected_by_pair:
        raise ValueError("membership SQL source row, counts or last match mismatch")
    league_counts = collections.Counter(x[0] for x in actual_by_pair)
    for x in summary:
        lid = int(x["league_hf_id"])
        if league_counts[lid] != int(x["historical_unique_hf_clubs"]):
            raise ValueError("league histogram differs from source")
        if (int(x["already_official_verified_clubs"]) +
                int(x["hf_only_unverified_clubs"]) != league_counts[lid]):
            raise ValueError("league approved/unverified split mismatched")
    return {
        "task": "TASK0061",
        "verdict": "INDEPENDENT_HF_SQL_AND_OFFICIAL_SHA_REGISTRY_ACCEPT",
        "master_unique_hf_ids": len(master),
        "league_membership_rows": len(memberships),
        "source_local_alias_proposals": len(aliases),
        "verified_official_identities": len(approved),
        "unapproved_hf_teams": len(master)-len(approved),
        "league_count": len(summary),
        "registry_manifest_sha256": sha(folder/"registry_manifest.json"),
        "source_history_asof": "2026-07-05-exclusive",
        "market_price_and_club_identity_never_inferred": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for k in ("folder","history","identity","extension","out"):
        parser.add_argument("--"+k,type=Path,required=True)
    a = parser.parse_args()
    result=check(folder=a.folder,history=a.history,
                 identity=a.identity,extension=a.extension)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf8") as f:
        json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    main()
